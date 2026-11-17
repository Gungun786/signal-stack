import logging
from typing import Dict, Any, List, Optional
from app.llm.gateway import llm_gateway

logger = logging.getLogger("signal_stack.interview")

INTERVIEW_DOMAINS = [
    {
        "step": 1,
        "domain": "business_lines",
        "title": "Business Lines & Revenue Streams",
        "description": "What are your primary revenue streams, and which business lines drive the majority of your gross margin today?"
    },
    {
        "step": 2,
        "domain": "customer_segments",
        "title": "Core Customer Segments",
        "description": "Who are your top 2-3 target customer segments or buyer personas, and how has their behavior changed over the past 6 months?"
    },
    {
        "step": 3,
        "domain": "customer_problems",
        "title": "Critical Customer Pain Points",
        "description": "What is the single most urgent problem or operational headache your customers hire your platform to solve?"
    },
    {
        "step": 4,
        "domain": "differentiators",
        "title": "Why Customers Choose You (Moat)",
        "description": "When a prospect chooses you over alternative solutions, what is the primary decisive reason or feature they cite?"
    },
    {
        "step": 5,
        "domain": "competitors",
        "title": "Competitors & Substitutes",
        "description": "Who are the direct rivals and indirect substitutes you encounter most frequently in competitive deal evaluations?"
    },
    {
        "step": 6,
        "domain": "market_changes",
        "title": "Macro & Regulatory Shifts",
        "description": "What industry, regulatory, economic, or technological tailwinds/headwinds are creating friction or opening opportunities for you?"
    },
    {
        "step": 7,
        "domain": "material_threats",
        "title": "Material Business Threats",
        "description": "What is the biggest operational, competitive, or macroeconomic threat that could derail your targets over the next 12 months?"
    },
    {
        "step": 8,
        "domain": "priorities",
        "title": "6-12 Month Strategic Priorities",
        "description": "What are your top 2-3 executive strategic priorities or key milestones for the next 6-12 months?"
    },
    {
        "step": 9,
        "domain": "internal_data",
        "title": "Internal Signals & Lost-Deal Data",
        "description": "What internal metrics or signals (e.g. lost-deal objections, churn exit surveys, feature requests) should directly influence your decisions?"
    },
    {
        "step": 10,
        "domain": "decision_support",
        "title": "Decisions This System Must Support",
        "description": "What specific high-stakes weekly or monthly decisions (e.g. pricing adjustments, feature prioritization, defensive marketing) should the Monday Brief inform?"
    }
]

class AdaptiveInterviewEngine:
    """
    Manages the 10-step adaptive AI interview.
    Generates tailored questions conditioned on:
    - Initial crawled company research
    - Prior answers given by the user
    - The specific domain for that step
    """

    def generate_question(
        self,
        company_name: str,
        website: str,
        step_number: int,
        research_profile: Dict[str, Any],
        prior_answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        domain_info = next((d for d in INTERVIEW_DOMAINS if d["step"] == step_number), INTERVIEW_DOMAINS[0])
        domain_name = domain_info["domain"]

        # Build context from prior answers
        prior_context_str = ""
        for pa in prior_answers:
            if pa.get("answer_text"):
                prior_context_str += f"- Step {pa.get('step_number')} ({pa.get('domain')}): {pa.get('answer_text')}\n"

        prompt = f"""
You are conducting an adaptive executive intelligence interview for '{company_name}' ({website}).
Current Step: {step_number} of 10.
Domain: {domain_info['title']} ({domain_name})
Base Goal: {domain_info['description']}

Initial Research Findings:
- Products: {[p.get('item') for p in research_profile.get('products', [])][:3]}
- Positioning: {[p.get('item') for p in research_profile.get('positioning', [])][:2]}
- Customers: {[c.get('item') for c in research_profile.get('customers', [])][:2]}

Prior Answers Provided:
{prior_context_str or "None yet."}

Generate:
1. "question_text": A sharp, personalized, executive-level interview question specifically tailored to '{company_name}' that digs deep into {domain_info['title']}. Do NOT ask a generic question; incorporate what was already learned from research and prior answers.
2. "suggested_context": A brief 1-2 sentence tip explaining why answering this helps calibrate their competitive intelligence radar, and note that confidential questions can be skipped.

Respond in JSON:
{{
  "question_text": "...",
  "suggested_context": "..."
}}
"""
        generated = llm_gateway.generate_json(prompt)
        if isinstance(generated, dict) and "question_text" in generated:
            return {
                "step_number": step_number,
                "domain": domain_name,
                "question_text": generated["question_text"],
                "suggested_context": generated.get("suggested_context", "Skipping is allowed if confidential.")
            }

        # Fallback to domain default
        return {
            "step_number": step_number,
            "domain": domain_name,
            "question_text": f"Regarding {company_name}'s {domain_info['title'].lower()}: {domain_info['description']}",
            "suggested_context": "Your response directly steers the autonomous source monitoring engine."
        }

interview_engine = AdaptiveInterviewEngine()
