import logging
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
import uuid
import uuid

from .. import db
from ..models.v2_kg import (
    EventInstance,
    StockExposure,
    ReasoningPath,
    EventValidationResult
)

logger = logging.getLogger(__name__)

def get_trading_days() -> List[str]:
    """获取所有历史交易日，并按升序排列。"""
    rows = db.rows("SELECT DISTINCT trade_date FROM daily_prices ORDER BY trade_date ASC")
    return [r["trade_date"] for r in rows]

def determine_t0_date(occurred_at: datetime, trading_days: List[str]) -> Optional[str]:
    """
    进行严格时间判断：
    - 如果事件发生在 15:00 之前（不含15:00），T0 为当日（如果是交易日）或之后的第一个交易日。
    - 如果事件发生在 15:00 之后，市场已收盘，T0 为之后的第一个交易日。
    """
    occurred_date_str = occurred_at.strftime("%Y-%m-%d")
    is_after_market = occurred_at.time() >= time(15, 0)
    
    for td in trading_days:
        if td == occurred_date_str:
            if not is_after_market:
                return td
            continue
        elif td > occurred_date_str:
            return td
            
    return None

def get_window_end_date(t0_date: str, window_days: int, trading_days: List[str]) -> Optional[str]:
    """根据 T0 和窗口大小计算 tn 的交易日"""
    try:
        t0_idx = trading_days.index(t0_date)
        tn_idx = t0_idx + window_days
        if tn_idx < len(trading_days):
            return trading_days[tn_idx]
    except ValueError:
        pass
    return None

def fetch_market_baseline(start_date: str, end_date: str) -> Dict[str, Dict[str, float]]:
    """
    计算 T0 到 Tn 的全市场和行业的平均收益。
    因为验证需要针对每只股票分别计算不同起止时间的超额收益，这里为了准确，
    我们先取出在这段时间内（start_date 和 end_date 对应收盘价）的收益率。
    """
    query = """
    SELECT p1.symbol, s.industry, p1.close as start_close, p2.close as end_close
    FROM daily_prices p1
    JOIN daily_prices p2 ON p1.symbol = p2.symbol
    JOIN stocks s ON p1.symbol = s.symbol
    WHERE p1.trade_date = %s AND p2.trade_date = %s
    """ if db._is_pg() else """
    SELECT p1.symbol, s.industry, p1.close as start_close, p2.close as end_close
    FROM daily_prices p1
    JOIN daily_prices p2 ON p1.symbol = p2.symbol
    JOIN stocks s ON p1.symbol = s.symbol
    WHERE p1.trade_date = ? AND p2.trade_date = ?
    """
    rows = db.rows(query, (start_date, end_date))
    
    industry_returns = {}
    market_returns = []
    
    for r in rows:
        sc = r["start_close"]
        ec = r["end_close"]
        if sc and sc > 0:
            ret = (ec / sc) - 1.0
            ind = r["industry"] or "未分类"
            market_returns.append(ret)
            if ind not in industry_returns:
                industry_returns[ind] = []
            industry_returns[ind].append(ret)
            
    avg_market = sum(market_returns) / len(market_returns) if market_returns else 0.0
    avg_industry = {ind: sum(rets)/len(rets) for ind, rets in industry_returns.items()}
    
    return {
        "market": avg_market,
        "industry": avg_industry
    }

def calculate_stock_stats(symbol: str, t0_date: str, tn_date: str) -> Optional[Dict[str, float]]:
    """
    计算个股在 t0_date 到 tn_date 之间的绝对收益、最大涨幅、最大回撤。
    """
    query = """
    SELECT trade_date, close, high, low
    FROM daily_prices
    WHERE symbol = %s AND trade_date >= %s AND trade_date <= %s
    ORDER BY trade_date ASC
    """ if db._is_pg() else """
    SELECT trade_date, close, high, low
    FROM daily_prices
    WHERE symbol = ? AND trade_date >= ? AND trade_date <= ?
    ORDER BY trade_date ASC
    """
    rows = db.rows(query, (symbol, t0_date, tn_date))
    if not rows or len(rows) < 2:
        return None
        
    start_close = rows[0]["close"]
    end_close = rows[-1]["close"]
    if start_close <= 0:
        return None
        
    absolute_return = (end_close / start_close) - 1.0
    
    max_price = max(r["high"] for r in rows)
    min_price = min(r["low"] for r in rows)
    
    max_gain = (max_price / start_close) - 1.0
    max_drawdown = (min_price / start_close) - 1.0
    
    return {
        "absolute_return": absolute_return,
        "max_gain": max_gain,
        "max_drawdown": max_drawdown
    }

def run_event_validation(event_id: str):
    """
    验证引擎入口。
    计算该事件所暴露的股票的 T+1, 3, 5, 10 收益并入库。
    """
    trading_days = get_trading_days()
    if not trading_days:
        logger.error("No trading days found in database.")
        return

    engine = db.get_engine()
    with Session(engine) as session:
        event = session.query(EventInstance).filter_by(event_id=event_id).first()
        if not event:
            logger.error(f"Event {event_id} not found.")
            return
            
        if not event.occurred_at:
            logger.warning(f"Event {event_id} has no occurred_at.")
            return

        t0_date = determine_t0_date(event.occurred_at, trading_days)
        if not t0_date:
            logger.error(f"Cannot determine T0 for event {event_id} occurred at {event.occurred_at}")
            return
            
        logger.info(f"Event {event_id} occurred at {event.occurred_at}, determined T0: {t0_date}")

        # 获取暴露的股票
        exposures = session.query(StockExposure).filter_by(event_id=event_id).all()
        if not exposures:
            logger.warning(f"No stock exposures for event {event_id}")
            return
            
        logger.info(f"Found {len(exposures)} stock exposures for event {event_id}")
        
        # Windows to evaluate
        windows = {"T+1": 1, "T+3": 3, "T+5": 5, "T+10": 10}
        
        # 预先清理当前事件的旧验证结果，支持反复执行重算
        session.query(EventValidationResult).filter_by(event_id=event_id).delete()
        
        for w_name, w_days in windows.items():
            tn_date = get_window_end_date(t0_date, w_days, trading_days)
            if not tn_date:
                logger.info(f"Window {w_name} end date not available for T0 {t0_date}")
                continue
                
            baseline = fetch_market_baseline(t0_date, tn_date)
            
            for exp in exposures:
                stock = db.row("SELECT industry FROM stocks WHERE symbol = ?", (exp.stock_code,))
                industry = stock["industry"] if stock else "未分类"
                
                stats = calculate_stock_stats(exp.stock_code, t0_date, tn_date)
                
                result = EventValidationResult(
                    validation_id=str(uuid.uuid4()),
                    event_id=event_id,
                    stock_code=exp.stock_code,
                    path_id=exp.reason_path_id,
                    window=w_name,
                    t0_date=datetime.strptime(t0_date, "%Y-%m-%d"),
                    end_date=datetime.strptime(tn_date, "%Y-%m-%d"),
                    calculated_at=datetime.now()
                )
                
                if stats:
                    result.absolute_return = stats["absolute_return"]
                    result.max_gain = stats["max_gain"]
                    result.max_drawdown = stats["max_drawdown"]
                    
                    result.benchmark_return = baseline["market"]
                    result.industry_return = baseline["industry"].get(industry, baseline["market"])
                    
                    result.excess_return_index = result.absolute_return - result.benchmark_return
                    result.excess_return_industry = result.absolute_return - result.industry_return
                    
                    # 定义命中条件：相对行业取得正超额，且绝对收益也为正？这里我们用：相对行业超额 > 0 记为命中
                    result.hit = result.excess_return_industry > 0.0
                    result.status = "calculated"
                else:
                    result.status = "missing_data"
                    
                session.add(result)
        
        session.commit()
        logger.info(f"Validation for event {event_id} completed.")
