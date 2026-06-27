import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from .. import db
from ..models.v2_kg import (
    EventValidationResult,
    ValidationSummary,
    KGRelation,
    KGChangeLog,
    ReasoningPath
)

logger = logging.getLogger(__name__)

def generate_validation_summary(window: str = "T+5"):
    """
    批处理聚合同类事件和路径的验证结果。
    为了简化，我们聚合的维度是 reason_path (其实可以聚合关系类型，但关系可能交织，所以最直观的是根据 reasoning_paths 内涉及的 relation 更新)
    这里我们将直接按照 relation 进行聚合：
    一条 reason_path 由多条边 (relation) 组成，对于 path 产生超额收益，其组成的所有的 relation 我们视作一次成功验证。
    """
    engine = db.get_engine()
    with Session(engine) as session:
        # 查询 window 下的有效验证结果
        results = session.query(EventValidationResult).filter(
            EventValidationResult.window == window,
            EventValidationResult.status == 'calculated'
        ).all()
        
        if not results:
            logger.warning(f"No validation results found for window {window}")
            return
            
        # 统计每个关系涉及到的验证次数与命中次数
        relation_stats = {} # relation_id -> {"total": 0, "hits": 0, "excess_sum": 0.0}
        
        for r in results:
            if not r.path_id:
                continue
            path = session.query(ReasoningPath).filter_by(path_id=r.path_id).first()
            if not path or not path.edges_json:
                continue
                
            for edge in path.edges_json:
                rel_id = edge.get("relation_id")
                if not rel_id:
                    continue
                if rel_id not in relation_stats:
                    relation_stats[rel_id] = {"total": 0, "hits": 0, "excess_sum": 0.0}
                
                relation_stats[rel_id]["total"] += 1
                if r.hit:
                    relation_stats[rel_id]["hits"] += 1
                relation_stats[rel_id]["excess_sum"] += r.excess_return_industry
        
        # 对每一个 relation 生成 summary，并回写 weight
        for rel_id, stats in relation_stats.items():
            total = stats["total"]
            hits = stats["hits"]
            excess_sum = stats["excess_sum"]
            
            hit_rate = hits / total if total > 0 else 0.0
            avg_excess = excess_sum / total if total > 0 else 0.0
            
            # 计算权重调整
            # 基础策略：如果胜率 > 60%，提升权重；如果胜率 < 40%，降低权重
            weight_adjustment = 0.0
            if hit_rate > 0.6:
                weight_adjustment = 0.1
            elif hit_rate < 0.4:
                weight_adjustment = -0.1
                
            # 存入 / 更新 ValidationSummary
            summary = session.query(ValidationSummary).filter_by(
                summary_type="relation",
                summary_key=rel_id,
                window=window
            ).first()
            
            if not summary:
                summary = ValidationSummary(
                    summary_id=str(uuid.uuid4()),
                    summary_type="relation",
                    summary_key=rel_id,
                    window=window,
                    sample_count=total,
                    hit_rate=hit_rate,
                    avg_excess_return=avg_excess,
                    weight_adjustment=weight_adjustment,
                    updated_at=datetime.now()
                )
                session.add(summary)
            else:
                summary.sample_count = total
                summary.hit_rate = hit_rate
                summary.avg_excess_return = avg_excess
                summary.weight_adjustment = weight_adjustment
                summary.updated_at = datetime.now()
                
            # 直接应用权重变更
            if weight_adjustment != 0.0:
                relation = session.query(KGRelation).filter_by(relation_id=rel_id).first()
                if relation:
                    old_weight = relation.weight
                    new_weight = max(0.0, min(1.0, old_weight + weight_adjustment)) # 限制在 0-1
                    
                    if old_weight != new_weight:
                        relation.weight = new_weight
                        relation.updated_at = datetime.now()
                        
                        log = KGChangeLog(
                            operation_type="weight_update",
                            relation_id=rel_id,
                            old_value=str(old_weight),
                            new_value=str(new_weight),
                            reason=f"Validation loop {window} hit rate: {hit_rate:.2f}",
                            operator="validation_engine",
                            created_at=datetime.now()
                        )
                        session.add(log)
                        logger.info(f"Updated relation {rel_id} weight from {old_weight} to {new_weight}")
        
        session.commit()
        logger.info("Validation summary generated and relations updated.")

def override_relation_weight(relation_id: str, new_weight: float, reason: str = "Manual override"):
    """
    提供手动修改关系权重的入口。
    """
    new_weight = max(0.0, min(1.0, new_weight))
    engine = db.get_engine()
    with Session(engine) as session:
        relation = session.query(KGRelation).filter_by(relation_id=relation_id).first()
        if not relation:
            logger.error(f"Relation {relation_id} not found.")
            return False
            
        old_weight = relation.weight
        relation.weight = new_weight
        relation.updated_at = datetime.now()
        
        log = KGChangeLog(
            operation_type="weight_update",
            relation_id=relation_id,
            old_value=str(old_weight),
            new_value=str(new_weight),
            reason=reason,
            operator="manual_admin",
            created_at=datetime.now()
        )
        session.add(log)
        session.commit()
        logger.info(f"Manually updated relation {relation_id} weight from {old_weight} to {new_weight}")
        return True
