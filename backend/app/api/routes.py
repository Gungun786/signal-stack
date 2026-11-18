import logging
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header, Query, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models import (
    Company, IntelligenceProfile, InterviewQuestion, Source,
    CrawledItem, SignalAnalysis, Brief, ContextChangeLog,
    SchedulerLog, MonthlyAuditReport
)
from app.schemas import (
    CompanyCreate, CompanyResponse, IntelligenceProfileResponse,
    IntelligenceProfileUpdate, InterviewAnswerRequest, InterviewQuestionResponse,
    SourceCreate, SourceResponse, SourceApprovalRequest,
    SignalAnalysisResponse, BriefResponse, ContextChangeRequest,
    ContextChangeResponse, ActionItemUpdateRequest, SchedulerTriggerResponse
)
from app.engine.research import research_engine
from app.engine.interview import interview_engine, INTERVIEW_DOMAINS
from app.engine.sources import source_generator
from app.engine.monitor import monitoring_engine
from app.engine.analysis import analysis_engine
from app.engine.ranking import ranking_engine
from app.engine.brief import brief_engine
from app.engine.context_change import context_change_engine
from app.engine.audit import audit_engine
from app.crawler.internal import internal_parser
from app.crawler.crawler import crawler_client
from app.scheduler.jobs import run_weekly_brief_job, run_monthly_audit_job

logger = logging.getLogger("signal_stack.api")
router = APIRouter(prefix="/api")

# --- 1. COMPANIES & SETUP ---

@router.post("/seed")
def seed_demo_data(db: Session = Depends(get_db)):
    """Populates demo entities with full research, sources, and real signals."""
    from run_demos import run_company_workflow
    try:
        # MeetUniversity
        m_id = run_company_workflow(
            name="MeetUniversity",
            website="https://www.meetuniversity.com",
            initial_context="Leading international student admissions counseling platform."
        )
        # Supabase
        s_id = run_company_workflow(
            name="Supabase",
            website="https://supabase.com",
            initial_context="Open source Firebase alternative providing PostgreSQL, Auth, and Edge Functions.",
            custom_competitors=["Firebase", "Hasura", "Appwrite", "Neon Postgres", "PlanetScale"],
            custom_market=["PostgreSQL 17 release", "Serverless database pricing", "Vector database benchmarks AI"]
        )
        # Razorpay
        r_id = run_company_workflow(
            name="Razorpay",
            website="https://razorpay.com",
            initial_context="Leading Indian full-stack payments and financial solutions provider for businesses.",
            custom_competitors=["Stripe", "Cashfree Payments", "Pine Labs", "PayU India", "PhonePe Payment Gateway"],
            custom_market=["RBI Payment Aggregator license guidelines", "UPI credit line regulations", "Cross border remittance India"]
        )
        return {"status": "success", "companies": [m_id, s_id, r_id]}
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/companies", response_model=CompanyResponse)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    existing = db.query(Company).filter(Company.name == payload.name).first()
    if existing:
        return existing

    company = Company(
        name=payload.name,
        website=payload.website,
        context=payload.context or f"Initial company setup for {payload.name}."
    )
    db.add(company)
    db.commit()
    db.refresh(company)

    # Automatically perform initial research crawl
    try:
        profile_data = research_engine.conduct_initial_research(company.name, company.website)
        profile = IntelligenceProfile(
            company_id=company.id,
            products=profile_data.get("products", []),
            customers=profile_data.get("customers", []),
            positioning=profile_data.get("positioning", []),
            business_lines=profile_data.get("business_lines", [])
        )
        db.add(profile)
        db.commit()
    except Exception as e:
        logger.error(f"Error during initial research for {company.name}: {e}")

    return company


@router.get("/companies", response_model=List[CompanyResponse])
def list_companies(db: Session = Depends(get_db)):
    return db.query(Company).order_by(Company.id.desc()).all()


@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


# --- 2. INTELLIGENCE PROFILE ---

@router.get("/companies/{company_id}/profile", response_model=IntelligenceProfileResponse)
def get_profile(company_id: int, db: Session = Depends(get_db)):
    profile = db.query(IntelligenceProfile).filter(IntelligenceProfile.company_id == company_id).first()
    if not profile:
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        # Generate initial profile if missing
        profile_data = research_engine.conduct_initial_research(company.name, company.website)
        profile = IntelligenceProfile(
            company_id=company.id,
            products=profile_data.get("products", []),
            customers=profile_data.get("customers", []),
            positioning=profile_data.get("positioning", []),
            business_lines=profile_data.get("business_lines", [])
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("/companies/{company_id}/profile", response_model=IntelligenceProfileResponse)
def update_profile(company_id: int, payload: IntelligenceProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(IntelligenceProfile).filter(IntelligenceProfile.company_id == company_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if payload.products is not None:
        profile.products = payload.products
    if payload.customers is not None:
        profile.customers = payload.customers
    if payload.positioning is not None:
        profile.positioning = payload.positioning
    if payload.business_lines is not None:
        profile.business_lines = payload.business_lines

    db.commit()
    db.refresh(profile)
    return profile


# --- 3. ADAPTIVE AI INTERVIEW (10 STEPS) ---

@router.get("/companies/{company_id}/interview/current", response_model=InterviewQuestionResponse)
def get_current_interview_question(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    answered_steps = db.query(InterviewQuestion).filter(
        InterviewQuestion.company_id == company_id
    ).order_by(InterviewQuestion.step_number.asc()).all()

    current_step = len(answered_steps) + 1
    if current_step > 10:
        return answered_steps[-1]

    # Fetch profile and prior answers for context
    profile_data = {}
    if company.profile:
        profile_data = {
            "products": company.profile.products,
            "customers": company.profile.customers,
            "positioning": company.profile.positioning
        }
    prior_answers = [
        {"step_number": a.step_number, "domain": a.domain, "answer_text": a.answer_text}
        for a in answered_steps
    ]

    q_data = interview_engine.generate_question(
        company.name, company.website, current_step, profile_data, prior_answers
    )

    question = InterviewQuestion(
        company_id=company.id,
        step_number=current_step,
        domain=q_data["domain"],
        question_text=q_data["question_text"],
        suggested_context=q_data["suggested_context"]
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.post("/companies/{company_id}/interview/answer", response_model=InterviewQuestionResponse)
def answer_interview_question(company_id: int, payload: InterviewAnswerRequest, db: Session = Depends(get_db)):
    question = db.query(InterviewQuestion).filter(
        InterviewQuestion.company_id == company_id,
        InterviewQuestion.step_number == payload.step_number
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question step not found")

    question.answer_text = payload.answer_text if not payload.skipped else None
    question.skipped = payload.skipped
    db.commit()
    db.refresh(question)

    # Append to company context
    company = db.query(Company).filter(Company.id == company_id).first()
    if company and payload.answer_text:
        company.context = (company.context or "") + f"\n[{question.domain}]: {payload.answer_text}"
        db.commit()

    return question


@router.get("/companies/{company_id}/interview/all", response_model=List[InterviewQuestionResponse])
def get_all_interview_questions(company_id: int, db: Session = Depends(get_db)):
    return db.query(InterviewQuestion).filter(
        InterviewQuestion.company_id == company_id
    ).order_by(InterviewQuestion.step_number.asc()).all()


# --- 4. SIGNAL STACK & SOURCES MANAGER ---

@router.post("/companies/{company_id}/sources/generate", response_model=List[SourceResponse])
def generate_company_sources(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    profile_dict = {}
    if company.profile:
        profile_dict = {
            "products": company.profile.products,
            "positioning": company.profile.positioning,
            "customers": company.profile.customers
        }

    interview_answers = [
        {"domain": q.domain, "answer_text": q.answer_text}
        for q in company.interviews if q.answer_text
    ]

    candidate_sources = source_generator.generate_sources(
        company.name, company.website, profile_dict, interview_answers
    )

    created_sources = []
    for s_data in candidate_sources:
        existing = db.query(Source).filter(
            Source.company_id == company_id,
            Source.url == s_data["url"]
        ).first()
        if not existing:
            source = Source(
                company_id=company_id,
                url=s_data["url"],
                name=s_data["name"],
                category=s_data["category"],
                feed_url=s_data.get("feed_url"),
                reason_for_inclusion=s_data["reason_for_inclusion"],
                specificity_score=s_data.get("specificity_score", 80.0),
                recency_score=s_data.get("recency_score", 80.0),
                credibility_score=s_data.get("credibility_score", 80.0),
                is_approved=s_data.get("is_approved", True),
                is_active=True
            )
            db.add(source)
            created_sources.append(source)
    db.commit()
    return db.query(Source).filter(Source.company_id == company_id).all()


@router.get("/companies/{company_id}/sources", response_model=List[SourceResponse])
def get_company_sources(
    company_id: int,
    category: Optional[str] = None,
    approved_only: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(Source).filter(Source.company_id == company_id)
    if category:
        query = query.filter(Source.category == category)
    if approved_only:
        query = query.filter(Source.is_approved == True)
    return query.order_by(Source.id.asc()).all()


@router.post("/companies/{company_id}/sources", response_model=SourceResponse)
def add_custom_source(company_id: int, payload: SourceCreate, db: Session = Depends(get_db)):
    source = Source(
        company_id=company_id,
        url=payload.url,
        name=payload.name,
        category=payload.category,
        feed_url=payload.feed_url,
        reason_for_inclusion=payload.reason_for_inclusion,
        specificity_score=payload.specificity_score,
        recency_score=payload.recency_score,
        credibility_score=payload.credibility_score,
        is_approved=payload.is_approved,
        is_active=True
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.post("/companies/{company_id}/sources/approve")
def approve_sources(company_id: int, payload: SourceApprovalRequest, db: Session = Depends(get_db)):
    if payload.approved_ids:
        db.query(Source).filter(
            Source.company_id == company_id,
            Source.id.in_(payload.approved_ids)
        ).update({Source.is_approved: True}, synchronize_session=False)

    if payload.rejected_ids:
        db.query(Source).filter(
            Source.company_id == company_id,
            Source.id.in_(payload.rejected_ids)
        ).update({Source.is_approved: False}, synchronize_session=False)

    db.commit()
    return {"status": "success", "approved": len(payload.approved_ids)}


@router.delete("/companies/{company_id}/sources/{source_id}")
def delete_source(company_id: int, source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.company_id == company_id, Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return {"status": "deleted"}


# --- 5. INTERNAL FILE INGESTION ---

@router.post("/companies/{company_id}/internal/upload")
async def upload_internal_file(company_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    content = await file.read()
    parsed_items = internal_parser.parse_file(file.filename, content)

    # Ingest parsed records into internal signals
    created_count = 0
    for item in parsed_items:
        content_hash = crawler_client.calculate_hash(item["title"] + item["content"])
        crawled = CrawledItem(
            source_id=None,
            company_id=company.id,
            url=f"local://internal/{file.filename}",
            title=item["title"],
            content_hash=content_hash,
            snippet=item["content"][:600],
            raw_content=item["content"],
            publication_date=datetime.datetime.utcnow(),
            discovery_date=datetime.datetime.utcnow()
        )
        db.add(crawled)
        db.commit()
        db.refresh(crawled)

        # Analyze internal signal
        analysis_engine.analyze_item(db, crawled, company)
        created_count += 1

    return {"status": "success", "filename": file.filename, "extracted_signals": created_count}


# --- 6. MONITORING & INTELLIGENCE FEED ---

@router.post("/companies/{company_id}/monitor")
def run_monitoring_cycle(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    new_items = monitoring_engine.monitor_all_company_sources(db, company_id)
    analyzed_signals = []
    for item in new_items:
        sig = analysis_engine.analyze_item(db, item, company)
        analyzed_signals.append(sig)

    ranking_engine.recompute_company_ranks(db, company_id)

    return {
        "status": "success",
        "new_items_crawled": len(new_items),
        "signals_generated": len(analyzed_signals)
    }


@router.get("/companies/{company_id}/signals", response_model=List[SignalAnalysisResponse])
def get_intelligence_feed(
    company_id: int,
    category: Optional[str] = None,
    signal_type: Optional[str] = None,
    urgency: Optional[str] = None,
    verified_only: bool = False,
    min_rank: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SignalAnalysis).filter(SignalAnalysis.company_id == company_id)
    if category:
        query = query.filter(SignalAnalysis.category == category)
    if signal_type:
        query = query.filter(SignalAnalysis.signal_type == signal_type)
    if urgency:
        query = query.filter(SignalAnalysis.urgency == urgency)
    if verified_only:
        query = query.filter(SignalAnalysis.verified == True)
    if min_rank is not None:
        query = query.filter(SignalAnalysis.rank_score >= min_rank)

    return query.order_by(SignalAnalysis.rank_score.desc()).all()


# --- 7. MONDAY MORNING BRIEF ---

@router.post("/companies/{company_id}/briefs/generate", response_model=BriefResponse)
def generate_monday_brief(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    brief = brief_engine.generate_brief(db, company)
    return brief


@router.get("/companies/{company_id}/briefs", response_model=List[BriefResponse])
def list_company_briefs(company_id: int, db: Session = Depends(get_db)):
    return db.query(Brief).filter(Brief.company_id == company_id).order_by(Brief.id.desc()).all()


@router.get("/briefs/{brief_id}", response_model=BriefResponse)
def get_brief(brief_id: int, db: Session = Depends(get_db)):
    brief = db.query(Brief).filter(Brief.id == brief_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    return brief


@router.get("/briefs/{brief_id}/export/markdown")
def export_brief_markdown(brief_id: int, db: Session = Depends(get_db)):
    brief = db.query(Brief).filter(Brief.id == brief_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    return Response(content=brief.markdown_content or "", media_type="text/markdown")


@router.get("/briefs/{brief_id}/export/html")
def export_brief_html(brief_id: int, db: Session = Depends(get_db)):
    brief = db.query(Brief).filter(Brief.id == brief_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    return Response(content=brief.html_content or "", media_type="text/html")


@router.patch("/briefs/{brief_id}/actions")
def update_action_item_status(brief_id: int, payload: ActionItemUpdateRequest, db: Session = Depends(get_db)):
    brief = db.query(Brief).filter(Brief.id == brief_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")

    actions = list(brief.recommended_actions)
    if 0 <= payload.action_index < len(actions):
        actions[payload.action_index]["status"] = payload.status
        brief.recommended_actions = actions
        db.commit()
        return {"status": "success", "action": actions[payload.action_index]}
    raise HTTPException(status_code=400, detail="Invalid action index")


# --- 8. CONTEXT CHANGE FEATURE ---

@router.post("/companies/{company_id}/context-change", response_model=ContextChangeResponse)
def apply_context_change(company_id: int, payload: ContextChangeRequest, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    log = context_change_engine.apply_context_change(db, company, payload.new_context)
    return log


@router.get("/companies/{company_id}/context-changes", response_model=List[ContextChangeResponse])
def get_context_change_logs(company_id: int, db: Session = Depends(get_db)):
    return db.query(ContextChangeLog).filter(
        ContextChangeLog.company_id == company_id
    ).order_by(ContextChangeLog.id.desc()).all()


# --- 9. MONTHLY AUDIT ---

@router.post("/companies/{company_id}/audit")
def run_monthly_audit(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    report = audit_engine.perform_monthly_audit(db, company)
    return report


@router.get("/companies/{company_id}/audits")
def list_monthly_audits(company_id: int, db: Session = Depends(get_db)):
    return db.query(MonthlyAuditReport).filter(
        MonthlyAuditReport.company_id == company_id
    ).order_by(MonthlyAuditReport.id.desc()).all()


# --- 10. SCHEDULER & CRON TRIGGERS (GITHUB ACTIONS READY) ---

@router.get("/scheduler/logs")
def get_scheduler_logs(db: Session = Depends(get_db)):
    return db.query(SchedulerLog).order_by(SchedulerLog.id.desc()).limit(50).all()


@router.post("/scheduler/trigger-weekly", response_model=SchedulerTriggerResponse)
def trigger_weekly_cron(
    secret: Optional[str] = Query(None),
    x_cron_secret: Optional[str] = Header(None),
    company_id: Optional[int] = Query(None)
):
    token = secret or x_cron_secret
    if token != settings.CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron authorization token")

    res = run_weekly_brief_job(target_company_id=company_id)
    return {
        "status": res.get("status", "unknown"),
        "job": "weekly_brief",
        "message": f"Processed {res.get('signals', 0)} signals.",
        "timestamp": datetime.datetime.utcnow()
    }


@router.post("/scheduler/trigger-monthly", response_model=SchedulerTriggerResponse)
def trigger_monthly_cron(
    secret: Optional[str] = Query(None),
    x_cron_secret: Optional[str] = Header(None),
    company_id: Optional[int] = Query(None)
):
    token = secret or x_cron_secret
    if token != settings.CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron authorization token")

    res = run_monthly_audit_job(target_company_id=company_id)
    return {
        "status": res.get("status", "unknown"),
        "job": "monthly_audit",
        "message": f"Audited companies: {res.get('audited_companies', 0)}",
        "timestamp": datetime.datetime.utcnow()
    }
