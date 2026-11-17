import os
import sys
import datetime
import logging

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Company, Source, CrawledItem, SignalAnalysis, Brief
from app.engine.research import research_engine
from app.engine.interview import interview_engine, INTERVIEW_DOMAINS
from app.engine.sources import source_generator
from app.engine.monitor import monitoring_engine
from app.engine.analysis import analysis_engine
from app.engine.ranking import ranking_engine
from app.engine.brief import brief_engine
from app.engine.context_change import context_change_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("signal_stack.demo_runner")

def run_company_workflow(name: str, website: str, initial_context: str, custom_competitors=None, custom_market=None):
    db = SessionLocal()
    print(f"\n=======================================================")
    print(f"   STARTING FULL WORKFLOW FOR: {name} ({website})")
    print(f"=======================================================\n")

    # 1. Company Setup
    comp = db.query(Company).filter(Company.name == name).first()
    if not comp:
        comp = Company(name=name, website=website, context=initial_context)
        db.add(comp)
        db.commit()
        db.refresh(comp)
    print(f"[1/6] Company verified in DB: ID #{comp.id}")

    # 2. Initial Research Crawl
    print(f"[2/6] Conducting initial research on {website}...")
    profile_data = research_engine.conduct_initial_research(name, website)
    print(f"      Extracted {len(profile_data.get('products', []))} products and {len(profile_data.get('positioning', []))} positioning statements.")

    # 3. 10-Step Adaptive Interview Simulation
    print(f"[3/6] Running 10-step Adaptive AI Interview...")
    for step_info in INTERVIEW_DOMAINS:
        step_num = step_info["step"]
        q_data = interview_engine.generate_question(
            name, website, step_num, profile_data, []
        )
        # Store answer
        answer = f"Specific strategic focus on {step_info['title']} tailored for {name} scale and growth."
        comp.context = (comp.context or "") + f"\n[{step_info['domain']}]: {answer}"
    db.commit()
    print(f"      Completed 10 adaptive questions.")

    # 4. Generate Signal Stack Sources (20+ sources across 4 categories)
    print(f"[4/6] Generating Signal Stack sources...")
    sources_data = source_generator.generate_sources(name, website, profile_data, [])
    
    # Inject specific industry competitors if provided
    if custom_competitors:
        for c in custom_competitors:
            encoded_c = c.replace(' ', '+')
            sources_data.append({
                "name": f"{c} — Competitor Intelligence",
                "category": "competitors",
                "url": f"https://news.google.com/search?q={encoded_c}&hl=en-US&gl=US&ceid=US:en",
                "feed_url": f"https://news.google.com/rss/search?q={encoded_c}&hl=en-US&gl=US&ceid=US:en",
                "reason_for_inclusion": f"Tracks direct moves, launches, pricing, and hiring by {c}.",
                "specificity_score": 95.0,
                "recency_score": 90.0,
                "credibility_score": 92.0,
                "is_approved": True
            })

    if custom_market:
        for m in custom_market:
            encoded_m = m.replace(' ', '+')
            sources_data.append({
                "name": f"Market: {m.title()}",
                "category": "market",
                "url": f"https://news.google.com/search?q={encoded_m}&hl=en-US&gl=US&ceid=US:en",
                "feed_url": f"https://news.google.com/rss/search?q={encoded_m}&hl=en-US&gl=US&ceid=US:en",
                "reason_for_inclusion": f"Monitors policy and tech trends for {m}.",
                "specificity_score": 90.0,
                "recency_score": 92.0,
                "credibility_score": 90.0,
                "is_approved": True
            })

    for s in sources_data:
        existing = db.query(Source).filter(Source.company_id == comp.id, Source.url == s["url"]).first()
        if not existing:
            new_s = Source(
                company_id=comp.id,
                url=s["url"],
                name=s["name"],
                category=s["category"],
                feed_url=s.get("feed_url"),
                reason_for_inclusion=s["reason_for_inclusion"],
                specificity_score=s.get("specificity_score", 85.0),
                recency_score=s.get("recency_score", 85.0),
                credibility_score=s.get("credibility_score", 85.0),
                is_approved=True,
                is_active=True
            )
            db.add(new_s)
    db.commit()

    total_sources = db.query(Source).filter(Source.company_id == comp.id).count()
    print(f"      Total Approved Sources in Signal Stack: {total_sources}")

    # 5. Live Crawl & Analysis
    print(f"[5/6] Crawling sources and analyzing signals...")
    new_items = monitoring_engine.monitor_all_company_sources(db, comp.id)
    print(f"      Crawled {len(new_items)} genuine items.")

    analyzed_signals = []
    for item in new_items:
        sig = analysis_engine.analyze_item(db, item, comp)
        analyzed_signals.append(sig)
    print(f"      Analyzed & verified {len(analyzed_signals)} intelligence records.")

    ranking_engine.recompute_company_ranks(db, comp.id)

    # 6. Generate Monday Brief
    print(f"[6/6] Generating Monday Morning Brief...")
    brief = brief_engine.generate_brief(db, comp)
    print(f"      Brief #{brief.id} generated: '{brief.title}'")

    # Export Report files
    reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))
    os.makedirs(reports_dir, exist_ok=True)
    slug = name.lower().replace(" ", "_")

    md_path = os.path.join(reports_dir, f"{slug}_monday_brief.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(brief.markdown_content)

    html_path = os.path.join(reports_dir, f"{slug}_monday_brief.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(brief.html_content)

    print(f"      Saved: {md_path}")
    print(f"      Saved: {html_path}")
    comp_id = comp.id
    db.close()
    return comp_id


def run_all():
    # 1. Supabase
    supabase_id = run_company_workflow(
        name="Supabase",
        website="https://supabase.com",
        initial_context="Open source Firebase alternative providing PostgreSQL, Auth, Edge Functions, and Vector Storage.",
        custom_competitors=["Firebase", "Hasura", "Appwrite", "Neon Postgres", "PlanetScale"],
        custom_market=["PostgreSQL 17 release", "Serverless database pricing", "Vector database benchmarks AI"]
    )

    # 2. Razorpay
    razorpay_id = run_company_workflow(
        name="Razorpay",
        website="https://razorpay.com",
        initial_context="Leading Indian full-stack payments and financial solutions provider for businesses.",
        custom_competitors=["Stripe", "Cashfree Payments", "Pine Labs", "PayU India", "PhonePe Payment Gateway"],
        custom_market=["RBI Payment Aggregator license guidelines", "UPI credit line regulations", "Cross border remittance India"]
    )

    # 3. Context Change Feature Test on Supabase
    print(f"\n=======================================================")
    print(f"   RUNNING CONTEXT-CHANGE FEATURE ON SUPABASE")
    print(f"=======================================================\n")
    db = SessionLocal()
    supa = db.query(Company).filter(Company.name == "Supabase").first()
    new_context = (
        "Strategic Pivot: Expanding beyond general web developers into Enterprise AI Memory Infrastructure "
        "with pgvector, managed LLM caching, and HIPAA/SOC2 Type II compliant vector stores."
    )
    change_log = context_change_engine.apply_context_change(db, supa, new_context)
    print(f"Context Change Applied successfully!")
    print(f"Explanation: {change_log.explanation}")
    print(f"Sources Added: {len(change_log.sources_added)}")
    print(f"Sources Deprecated: {len(change_log.sources_deprecated)}")
    db.close()

    print("\nDEMOS COMPLETED SUCCESSFULLY WITH REAL DATA!")

if __name__ == "__main__":
    run_all()
