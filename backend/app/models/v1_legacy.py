from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.schema import PrimaryKeyConstraint
from .base import Base

class Stock(Base):
    __tablename__ = 'stocks'
    symbol = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=False, default='未分类')
    updated_at = Column(String, nullable=False)

class DailyPrice(Base):
    __tablename__ = 'daily_prices'
    symbol = Column(String, nullable=False, primary_key=True)
    trade_date = Column(String, nullable=False, primary_key=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    amount = Column(Float, nullable=False, default=0)

class NewsItem(Base):
    __tablename__ = 'news_items'
    id = Column(String, primary_key=True)
    source = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    language = Column(String, nullable=False, default='zh')
    region = Column(String, nullable=False, default='CN')
    published_at = Column(String, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(String, nullable=False, default='')
    url = Column(String)
    sentiment = Column(Float, nullable=False, default=0)
    model_version = Column(String, nullable=False, default='rule-keywords-v1')
    score_source = Column(String, nullable=False, default='rule')
    model_raw_output = Column(String, nullable=False, default='{}')
    event_type = Column(String, nullable=False, default='general')
    keywords = Column(String, nullable=False, default='[]')
    raw_payload = Column(String, nullable=False, default='{}')
    created_at = Column(String, nullable=False)

class NewsStockLink(Base):
    __tablename__ = 'news_stock_links'
    news_id = Column(String, nullable=False, primary_key=True)
    symbol = Column(String, nullable=False, primary_key=True)
    confidence = Column(Float, nullable=False, default=1.0)
    match_type = Column(String, nullable=False, default='symbol')

class StockAlias(Base):
    __tablename__ = 'stock_aliases'
    alias = Column(String, nullable=False, primary_key=True)
    symbol = Column(String, nullable=False, primary_key=True)
    language = Column(String, nullable=False, default='zh')
    confidence = Column(Float, nullable=False, default=0.9)

class Signal(Base):
    __tablename__ = 'signals'
    symbol = Column(String, nullable=False, primary_key=True)
    signal_date = Column(String, nullable=False, primary_key=True)
    trend_score = Column(Float, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    volume_score = Column(Float, nullable=False)
    total_score = Column(Float, nullable=False)
    burst = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    metrics = Column(String, nullable=False)

class Job(Base):
    __tablename__ = 'jobs'
    name = Column(String, primary_key=True)
    status = Column(String, nullable=False)
    started_at = Column(String)
    finished_at = Column(String)
    progress_current = Column(Integer, nullable=False, default=0)
    progress_total = Column(Integer, nullable=False, default=0)
    message = Column(String, nullable=False, default='')
    details = Column(String, nullable=False, default='{}')

class Event(Base):
    __tablename__ = 'events'
    id = Column(String, primary_key=True)
    news_id = Column(String)
    title = Column(String, nullable=False)
    summary = Column(String, nullable=False, default='')
    event_type = Column(String, nullable=False)
    subtype = Column(String, nullable=False, default='')
    intensity = Column(Float, nullable=False, default=0.0)
    direction = Column(String, nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    published_at = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    extraction_source = Column(String, nullable=False, default='rule')
    extraction_raw_output = Column(String, nullable=False, default='{}')

class CommodityImpact(Base):
    __tablename__ = 'commodity_impacts'
    id = Column(Integer, primary_key=True)
    event_id = Column(String, nullable=False)
    commodity = Column(String, nullable=False)
    impact_type = Column(String, nullable=False)
    direction = Column(String, nullable=False)

class CommoditySectorMapping(Base):
    __tablename__ = 'commodity_sector_mappings'
    commodity = Column(String, nullable=False, primary_key=True)
    sector = Column(String, nullable=False, primary_key=True)
    relationship = Column(String, nullable=False)
    coefficient = Column(Float, nullable=False, default=1.0)

class SectorStockExposure(Base):
    __tablename__ = 'sector_stock_exposures'
    sector = Column(String, nullable=False, primary_key=True)
    symbol = Column(String, nullable=False, primary_key=True)
    exposure = Column(Float, nullable=False, default=100.0)

class EventStockScore(Base):
    __tablename__ = 'event_stock_scores'
    event_id = Column(String, nullable=False, primary_key=True)
    symbol = Column(String, nullable=False, primary_key=True)
    event_score = Column(Float, nullable=False)
    event_impact = Column(Float, nullable=False)
    sector_exposure = Column(Float, nullable=False)
    trend_strength = Column(Float, nullable=False)
    direction = Column(String, nullable=False)
    causal_chain = Column(String, nullable=False)
    evidence = Column(String, nullable=False)

class CompanyCommodityProfile(Base):
    __tablename__ = 'company_commodity_profiles'
    symbol = Column(String, nullable=False, primary_key=True)
    commodity = Column(String, nullable=False, primary_key=True)
    role = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    benefit_when_price_up = Column(Integer, nullable=False, default=0)
    benefit_when_price_down = Column(Integer, nullable=False, default=0)
    exposure_strength = Column(Float, nullable=False, default=50.0)
    pricing_power = Column(Float, nullable=False, default=50.0)
    inventory_sensitivity = Column(Float, nullable=False, default=50.0)
    pass_through_ability = Column(Float, nullable=False, default=50.0)
    earnings_elasticity = Column(Float, nullable=False, default=50.0)
    lag_days = Column(Integer, nullable=False, default=0)
    evidence = Column(String, nullable=False, default='')
    updated_at = Column(String, nullable=False)

class EventEarningsImpact(Base):
    __tablename__ = 'event_earnings_impacts'
    event_id = Column(String, nullable=False, primary_key=True)
    symbol = Column(String, nullable=False, primary_key=True)
    commodity = Column(String, nullable=False, primary_key=True)
    revenue_impact_score = Column(Float, nullable=False)
    margin_impact_score = Column(Float, nullable=False)
    profit_impact_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False, default=0.7)
    horizon = Column(String, nullable=False, default='medium')
    reason = Column(String, nullable=False)

class EventStockReactionScoreV2(Base):
    __tablename__ = 'event_stock_reaction_scores_v2'
    event_id = Column(String, nullable=False, primary_key=True)
    symbol = Column(String, nullable=False, primary_key=True)
    commodity = Column(String, nullable=False, primary_key=True)
    shock_score = Column(Float, nullable=False)
    exposure_score = Column(Float, nullable=False)
    earnings_score = Column(Float, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    trend_score = Column(Float, nullable=False)
    reaction_score = Column(Float, nullable=False)
    direction = Column(String, nullable=False)
    horizon = Column(String, nullable=False, default='medium')
    confidence = Column(Float, nullable=False, default=0.7)
    transmission_chain = Column(String, nullable=False)
    evidence = Column(String, nullable=False)
