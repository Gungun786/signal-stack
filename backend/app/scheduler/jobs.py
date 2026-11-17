import logging
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import SessionLocal
from app.models import Company, SchedulerLog
from app.engine.monitor import monitoring_engine
from app.engine.analysis import analysis_engine
from app.engine.ranking import ranking_engine
from app.engine.brief import brief_engine
from app.engine.audit import audit_engine

logger = logging.getLogger("signal_stack.scheduler")

scheduler = BackgroundScheduler(daemon=True)

def run_weekly_brief_job(target_company_id: int = None):
    """Weekly Brief pipeline: source checks -> collect -> detect changes -> analyze -> rank -> brief."""
    logger.info("Executing Weekly Brief automated job...")
    db = SessionLocal()
    start_time = datetime.datetime.utcnow()
    try:
        query = db.query(Company)
        if target_company_id:
            query = query.filter(Company.id == target_company_id)
        companies = query.all()

        total_crawled = 0
        total_signals = 0

        for company in companies:
            # 1. Harvest new items from approved sources
            new_items = monitoring_engine.monitor_all_company_sources(db, company.id)
            total_crawled += len(new_items)

            # 2. Analyze newly discovered items
            for item in new_items:
                analysis_engine.analyze_item(db, item, company)
                total_signals += 1

            # 3. Recompute multi-factor ranks
            ranking_engine.recompute_company_ranks(db, company.id)

            # 4. Generate and save Monday Brief
            brief_engine.generate_brief(db, company)

        log = SchedulerLog(
            job_type="weekly_brief",
            status="success",
            details=f"Successfully processed {len(companies)} companies, {total_crawled} new items, {total_signals} analyzed signals.",
            executed_at=start_time
        )
        db.add(log)
        db.commit()
        logger.info(f"Weekly Brief job completed in {(datetime.datetime.utcnow() - start_time).total_seconds()}s")
        return {"status": "success", "crawled": total_crawled, "signals": total_signals}
    except Exception as e:
        logger.error(f"Weekly Brief job failed: {e}")
        log = SchedulerLog(
            job_type="weekly_brief",
            status="failed",
            details=f"Error encountered: {str(e)}",
            executed_at=start_time
        )
        db.add(log)
        db.commit()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


def run_monthly_audit_job(target_company_id: int = None):
    """Monthly Signal Stack Audit: dead URLs, duplicate/inactive sources, health report."""
    logger.info("Executing Monthly Signal Stack Audit automated job...")
    db = SessionLocal()
    start_time = datetime.datetime.utcnow()
    try:
        query = db.query(Company)
        if target_company_id:
            query = query.filter(Company.id == target_company_id)
        companies = query.all()

        for company in companies:
            audit_engine.perform_monthly_audit(db, company)

        log = SchedulerLog(
            job_type="monthly_audit",
            status="success",
            details=f"Successfully audited {len(companies)} companies for dead URLs and source health.",
            executed_at=start_time
        )
        db.add(log)
        db.commit()
        return {"status": "success", "audited_companies": len(companies)}
    except Exception as e:
        logger.error(f"Monthly Audit job failed: {e}")
        log = SchedulerLog(
            job_type="monthly_audit",
            status="failed",
            details=f"Error encountered: {str(e)}",
            executed_at=start_time
        )
        db.add(log)
        db.commit()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


def start_scheduler():
    """Initializes local cron triggers (Monday 06:00 and 1st of month 00:00)."""
    if not scheduler.running:
        # Every Monday at 06:00 UTC
        scheduler.add_job(
            run_weekly_brief_job,
            trigger=CronTrigger(day_of_week="mon", hour=6, minute=0),
            id="weekly_brief_job",
            replace_existing=True
        )
        # 1st of every month at 00:00 UTC
        scheduler.add_job(
            run_monthly_audit_job,
            trigger=CronTrigger(day=1, hour=0, minute=0),
            id="monthly_audit_job",
            replace_existing=True
        )
        scheduler.start()
        logger.info("APScheduler background engine started successfully.")
