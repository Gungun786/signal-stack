import logging
import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import Company, Source, ContextChangeLog
from app.engine.sources import source_generator
from app.llm.gateway import llm_gateway

logger = logging.getLogger("signal_stack.context_change")

class ContextChangeEngine:
    """
    Re-assesses source relevance when company strategy, business lines, or target markets pivot.
    Marks outdated sources as inactive/deprecated.
    Discovers and adds new sources tailored to the updated strategic context.
    Logs transparent explanation of all modifications.
    """

    def apply_context_change(self, db: Session, company: Company, new_context: str) -> ContextChangeLog:
        logger.info(f"Applying strategic context change for {company.name}")
        old_context = company.context or "Initial company baseline profile."

        # Update company context
        company.context = new_context
        db.commit()

        # Fetch current active sources
        existing_sources = db.query(Source).filter(
            Source.company_id == company.id,
            Source.is_active == True
        ).all()

        source_names = [f"ID {s.id}: {s.name} ({s.category}) - {s.reason_for_inclusion}" for s in existing_sources]

        prompt = f"""
Company: {company.name} ({company.website})
Previous Strategic Focus:
{old_context}

NEW Updated Strategic Focus:
{new_context}

Currently Active Sources:
{chr(10).join(source_names[:25])}

Analyze the strategic shift:
1. "deprecated_source_ids": List of Source IDs that are no longer relevant to the new strategic focus.
2. "deprecation_rationale": Clear 2-3 sentence explanation of why the strategic pivot warrants deprecating these sources.
3. "new_search_queries": 3 specific queries to find newly relevant competitors or regulatory feeds for the new context.

Respond in JSON:
{{
  "deprecated_source_ids": [1, 2],
  "deprecation_rationale": "...",
  "new_search_queries": ["query 1", "query 2", "query 3"]
}}
"""
        evaluation = llm_gateway.generate_json(prompt)
        deprecated_ids = []
        explanation = f"Strategic pivot to: '{new_context[:100]}...'"
        new_queries = []

        if isinstance(evaluation, dict):
            deprecated_ids = evaluation.get("deprecated_source_ids", [])
            explanation = evaluation.get("deprecation_rationale", explanation)
            new_queries = evaluation.get("new_search_queries", [])

        # Mark deprecated sources
        deprecated_records = []
        for s in existing_sources:
            if s.id in deprecated_ids:
                s.is_active = False
                s.health_status = "deprecated"
                deprecated_records.append({"id": s.id, "name": s.name, "category": s.category})
        db.commit()

        # Generate newly relevant sources based on new queries
        added_records = []
        for q in new_queries[:3]:
            encoded_q = q.replace(" ", "+")
            new_s = Source(
                company_id=company.id,
                name=f"Pivot Intel: {q.title()}",
                category="market",
                url=f"https://news.google.com/search?q={encoded_q}&hl=en-US&gl=US&ceid=US:en",
                feed_url=f"https://news.google.com/rss/search?q={encoded_q}&hl=en-US&gl=US&ceid=US:en",
                reason_for_inclusion=f"Added dynamically in response to strategic context change: {q}",
                specificity_score=94.0,
                recency_score=92.0,
                credibility_score=88.0,
                is_approved=True,
                is_active=True
            )
            db.add(new_s)
            db.commit()
            db.refresh(new_s)
            added_records.append({"id": new_s.id, "name": new_s.name, "category": new_s.category})

        log_entry = ContextChangeLog(
            company_id=company.id,
            old_context=old_context,
            new_context=new_context,
            sources_added=added_records,
            sources_deprecated=deprecated_records,
            explanation=explanation
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

context_change_engine = ContextChangeEngine()
