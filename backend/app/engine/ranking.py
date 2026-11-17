import logging
from typing import List
from sqlalchemy.orm import Session
from app.models import SignalAnalysis

logger = logging.getLogger("signal_stack.ranking")

class SignalRankingEngine:
    """
    Ranks signals on:
    - Relevance (30%)
    - Business Impact (25%)
    - Urgency (20%)
    - Source Credibility (15%)
    - Recency (10%)
    Ensures rank explanations are transparent and un-conflated.
    """

    def recompute_company_ranks(self, db: Session, company_id: int) -> List[SignalAnalysis]:
        signals = db.query(SignalAnalysis).filter(
            SignalAnalysis.company_id == company_id
        ).all()

        for s in signals:
            score = (
                (s.strategic_relevance * 0.30) +
                (s.business_impact * 0.25) +
                (s.urgency_score * 0.20) +
                (s.source_credibility * 0.15) +
                (s.recency_score * 0.10)
            )
            s.rank_score = round(score, 1)
            s.rank_explanation = (
                f"Ranked #{s.id} (Score: {s.rank_score:.1f}/100) — Relevance: {s.strategic_relevance:.0f}%, "
                f"Impact: {s.business_impact:.0f}%, Urgency: {s.urgency_score:.0f}%, "
                f"Source Credibility: {s.source_credibility:.0f}%. Area: {s.affected_business_area}."
            )
        
        db.commit()
        # Return sorted by rank_score descending
        return sorted(signals, key=lambda x: x.rank_score, reverse=True)

ranking_engine = SignalRankingEngine()
