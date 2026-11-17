import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    website = Column(String(512), nullable=False)
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    profile = relationship("IntelligenceProfile", back_populates="company", uselist=False, cascade="all, delete-orphan")
    interviews = relationship("InterviewQuestion", back_populates="company", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="company", cascade="all, delete-orphan")
    crawled_items = relationship("CrawledItem", back_populates="company", cascade="all, delete-orphan")
    signals = relationship("SignalAnalysis", back_populates="company", cascade="all, delete-orphan")
    briefs = relationship("Brief", back_populates="company", cascade="all, delete-orphan")
    context_logs = relationship("ContextChangeLog", back_populates="company", cascade="all, delete-orphan")
    audits = relationship("MonthlyAuditReport", back_populates="company", cascade="all, delete-orphan")


class IntelligenceProfile(Base):
    __tablename__ = "intelligence_profiles"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), unique=True)
    products = Column(JSON, default=list)        # [{item, status: 'verified'|'assumption', source_url}]
    customers = Column(JSON, default=list)       # [{segment, status, source_url}]
    positioning = Column(JSON, default=list)     # [{claim, status, source_url}]
    business_lines = Column(JSON, default=list)  # [{line, details, status, source_url}]
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="profile")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    step_number = Column(Integer, nullable=False)
    domain = Column(String(100), nullable=False)
    question_text = Column(Text, nullable=False)
    suggested_context = Column(Text, nullable=True)
    answer_text = Column(Text, nullable=True)
    skipped = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="interviews")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    url = Column(String(1024), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False) # 'customers', 'competitors', 'market', 'internal'
    feed_url = Column(String(1024), nullable=True)
    reason_for_inclusion = Column(Text, nullable=False)
    specificity_score = Column(Float, default=70.0)
    recency_score = Column(Float, default=70.0)
    credibility_score = Column(Float, default=70.0)
    is_approved = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    health_status = Column(String(50), default="healthy") # 'healthy', 'warning', 'dead'
    last_crawled_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="sources")
    crawled_items = relationship("CrawledItem", back_populates="source", cascade="all, delete-orphan")


class CrawledItem(Base):
    __tablename__ = "crawled_items"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    url = Column(String(1024), nullable=False)
    title = Column(String(512), nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    snippet = Column(Text, nullable=False)
    raw_content = Column(Text, nullable=True)
    publication_date = Column(DateTime, nullable=True)
    discovery_date = Column(DateTime, default=datetime.datetime.utcnow)

    source = relationship("Source", back_populates="crawled_items")
    company = relationship("Company", back_populates="crawled_items")
    analysis = relationship("SignalAnalysis", back_populates="crawled_item", uselist=False, cascade="all, delete-orphan")


class SignalAnalysis(Base):
    __tablename__ = "signal_analyses"

    id = Column(Integer, primary_key=True, index=True)
    crawled_item_id = Column(Integer, ForeignKey("crawled_items.id", ondelete="CASCADE"), unique=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    category = Column(String(50), nullable=False)
    what_happened = Column(Text, nullable=False)
    source_url = Column(String(1024), nullable=False)
    publication_date = Column(DateTime, nullable=True)
    discovery_date = Column(DateTime, default=datetime.datetime.utcnow)
    evidence_snippet = Column(Text, nullable=False)
    verified = Column(Boolean, default=True)
    verification_reasoning = Column(Text, nullable=False)
    why_it_matters = Column(Text, nullable=False)
    affected_business_area = Column(String(100), nullable=False)
    signal_type = Column(String(50), default="neutral") # 'opportunity', 'threat', 'neutral'
    urgency = Column(String(50), default="monitor")      # 'immediate', 'this_week', 'monitor'
    suggested_action = Column(Text, nullable=False)

    # Multi-dimensional ranking scores
    strategic_relevance = Column(Float, default=50.0)
    business_impact = Column(Float, default=50.0)
    urgency_score = Column(Float, default=50.0)
    source_credibility = Column(Float, default=50.0)
    recency_score = Column(Float, default=50.0)
    novelty_score = Column(Float, default=50.0)
    rank_score = Column(Float, default=50.0, index=True)
    rank_explanation = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="signals")
    crawled_item = relationship("CrawledItem", back_populates="analysis")


class Brief(Base):
    __tablename__ = "briefs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    period_start = Column(DateTime, default=datetime.datetime.utcnow)
    period_end = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Sections
    executive_summary = Column(JSON, default=list)       # Top 5 developments
    customer_signals = Column(JSON, default=list)
    competitor_intelligence = Column(JSON, default=list)
    market_intelligence = Column(JSON, default=list)
    internal_intelligence = Column(JSON, default=list)
    opportunities = Column(JSON, default=list)           # Min 3 with evidence, impact, next step, priority
    risks_and_threats = Column(JSON, default=list)
    recommended_actions = Column(JSON, default=list)     # prioritized actions with reason & owner
    what_to_watch = Column(JSON, default=list)
    source_appendix = Column(JSON, default=list)

    markdown_content = Column(Text, nullable=True)
    html_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="briefs")


class ContextChangeLog(Base):
    __tablename__ = "context_change_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    old_context = Column(Text, nullable=False)
    new_context = Column(Text, nullable=False)
    sources_added = Column(JSON, default=list)
    sources_deprecated = Column(JSON, default=list)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="context_logs")


class SchedulerLog(Base):
    __tablename__ = "scheduler_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=datetime.datetime.utcnow)


class MonthlyAuditReport(Base):
    __tablename__ = "monthly_audit_reports"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    dead_urls = Column(JSON, default=list)
    inactive_sources = Column(JSON, default=list)
    relevance_drift = Column(JSON, default=list)
    recommended_additions = Column(JSON, default=list)
    recommended_removals = Column(JSON, default=list)
    health_summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    company = relationship("Company", back_populates="audits")
