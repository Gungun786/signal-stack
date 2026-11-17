from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class CompanyCreate(BaseModel):
    name: str = Field(..., description="Company name")
    website: str = Field(..., description="Company website URL")
    context: Optional[str] = Field(None, description="Initial context or notes")

class CompanyResponse(BaseModel):
    id: int
    name: str
    website: str
    context: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ProfileItem(BaseModel):
    item: str
    status: str = "verified" # "verified" or "assumption"
    source_url: Optional[str] = None

class IntelligenceProfileResponse(BaseModel):
    id: int
    company_id: int
    products: List[Dict[str, Any]]
    customers: List[Dict[str, Any]]
    positioning: List[Dict[str, Any]]
    business_lines: List[Dict[str, Any]]
    updated_at: datetime

    class Config:
        from_attributes = True

class IntelligenceProfileUpdate(BaseModel):
    products: Optional[List[Dict[str, Any]]] = None
    customers: Optional[List[Dict[str, Any]]] = None
    positioning: Optional[List[Dict[str, Any]]] = None
    business_lines: Optional[List[Dict[str, Any]]] = None

class InterviewAnswerRequest(BaseModel):
    step_number: int
    answer_text: Optional[str] = None
    skipped: bool = False

class InterviewQuestionResponse(BaseModel):
    id: int
    company_id: int
    step_number: int
    domain: str
    question_text: str
    suggested_context: Optional[str] = None
    answer_text: Optional[str] = None
    skipped: bool
    created_at: datetime

    class Config:
        from_attributes = True

class SourceCreate(BaseModel):
    url: str
    name: str
    category: str # 'customers', 'competitors', 'market', 'internal'
    reason_for_inclusion: str
    feed_url: Optional[str] = None
    specificity_score: float = 75.0
    recency_score: float = 75.0
    credibility_score: float = 80.0
    is_approved: bool = True

class SourceResponse(BaseModel):
    id: int
    company_id: int
    url: str
    name: str
    category: str
    feed_url: Optional[str] = None
    reason_for_inclusion: str
    specificity_score: float
    recency_score: float
    credibility_score: float
    is_approved: bool
    is_active: bool
    health_status: str
    last_crawled_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    failure_count: int
    last_error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SourceApprovalRequest(BaseModel):
    approved_ids: List[int]
    rejected_ids: Optional[List[int]] = None

class SignalAnalysisResponse(BaseModel):
    id: int
    crawled_item_id: int
    company_id: int
    category: str
    what_happened: str
    source_url: str
    publication_date: Optional[datetime] = None
    discovery_date: datetime
    evidence_snippet: str
    verified: bool
    verification_reasoning: str
    why_it_matters: str
    affected_business_area: str
    signal_type: str
    urgency: str
    suggested_action: str
    strategic_relevance: float
    business_impact: float
    urgency_score: float
    source_credibility: float
    recency_score: float
    novelty_score: float
    rank_score: float
    rank_explanation: str
    created_at: datetime

    class Config:
        from_attributes = True

class BriefResponse(BaseModel):
    id: int
    company_id: int
    title: str
    period_start: datetime
    period_end: datetime
    executive_summary: List[Any]
    customer_signals: List[Any]
    competitor_intelligence: List[Any]
    market_intelligence: List[Any]
    internal_intelligence: List[Any]
    opportunities: List[Any]
    risks_and_threats: List[Any]
    recommended_actions: List[Any]
    what_to_watch: List[Any]
    source_appendix: List[Any]
    markdown_content: Optional[str] = None
    html_content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ContextChangeRequest(BaseModel):
    new_context: str = Field(..., description="Updated strategic focus, new business line or geo expansion")

class ContextChangeResponse(BaseModel):
    id: int
    company_id: int
    old_context: str
    new_context: str
    sources_added: List[Any]
    sources_deprecated: List[Any]
    explanation: str
    created_at: datetime

    class Config:
        from_attributes = True

class ActionItemUpdateRequest(BaseModel):
    action_index: int
    status: str # "pending", "in_progress", "completed"

class SchedulerTriggerResponse(BaseModel):
    status: str
    job: str
    message: str
    timestamp: datetime
