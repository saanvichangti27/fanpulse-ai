from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Match(Base):
    __tablename__ = 'matches'
    id = Column(String, primary_key=True)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    kickoff_time = Column(String, nullable=False)
    stage = Column(Integer, nullable=False, default=0)
    venue_capacity = Column(Integer, nullable=False, default=60000)
    city = Column(String)
    city_population_m = Column(Float)
    home_rank = Column(Integer)
    away_rank = Column(Integer)
    rivalry_flag = Column(Integer, default=0)
    host_involved = Column(Integer, default=0)
    status = Column(String, nullable=False, default='upcoming')

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String, nullable=False)
    match_id = Column(String, ForeignKey('matches.id'))
    source = Column(String, nullable=False)
    author = Column(String)
    text = Column(String, nullable=False)
    country = Column(String)
    sentiment = Column(String, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    emotion = Column(String, nullable=False)
    emotion_score = Column(Float, nullable=False)
    topics_json = Column(String, nullable=False, default='[]')
    created_at = Column(String, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('source', 'external_id', name='uq_source_external_id'),
        Index('idx_messages_match_created', 'match_id', 'created_at'),
    )

class Moment(Base):
    __tablename__ = 'moments'
    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey('matches.id'))
    event_tag = Column(String, nullable=False)
    detected_at = Column(String, nullable=False)
    momentum_json = Column(String, nullable=False)
    description = Column(String)

class Campaign(Base):
    __tablename__ = 'campaigns'
    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey('matches.id'))
    industry = Column(String, nullable=False)
    archetype = Column(String, nullable=False)
    target_segment = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    trigger = Column(String, nullable=False)
    moment_id = Column(String, ForeignKey('moments.id'))
    window_minutes = Column(Integer)
    copy_json = Column(String, nullable=False)
    roi_json = Column(String, nullable=False)
    evidence_json = Column(String, nullable=False)
    confidence = Column(Float)
    llm_fallback = Column(Integer, default=0)
    created_at = Column(String, nullable=False)

class ContentIdea(Base):
    __tablename__ = 'content_ideas'
    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey('matches.id'))
    platform = Column(String, nullable=False)
    idea_json = Column(String, nullable=False)
    evidence_json = Column(String, nullable=False)
    confidence = Column(Float)
    llm_fallback = Column(Integer, default=0)
    created_at = Column(String, nullable=False)

class Forecast(Base):
    __tablename__ = 'forecasts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String, ForeignKey('matches.id'))
    is_reforecast = Column(Integer, nullable=False, default=0)
    forecast_json = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
