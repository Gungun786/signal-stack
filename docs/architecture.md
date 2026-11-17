# Signal Stack Architecture Specification

## 1. System Overview & Core Principles

**Signal Stack** is an autonomous company intelligence and Monday Morning Brief engine engineered for competitive, customer, and market intelligence synthesis without hallucinated evidence or generic platitudes.

### Architectural Philosophy
1. **Absolute Evidence Traceability**: No signal or intelligence item is ever reported without a verified source URL, publication timestamp, discovery timestamp, and direct quotation/evidence snippet.
2. **Strict Separation of Truth vs. Interpretation**: Facts (direct observations from crawled sources) and AI Interpretations (strategic implications, urgency, opportunities) are bifurcated at the database model level and visual representation layer.
3. **Dynamic Zero-Hardcoding**: Every company onboarded undergoes automated web discovery and an adaptive 10-step AI interview. Sources, competitors, customer discussion hubs, and search vectors are dynamically generated from company positioning and market presence.
4. **Resilient Multi-Provider LLM Gateway**: A unified, provider-agnostic LLM client with automatic fallback from Gemini API (primary) to Groq (fallback), incorporating rate-limit backoff, schema-validated JSON outputs, and structured parsing.
5. **Zero-Cost & Free-Tier Optimization**: Designed exclusively on free, open-source or free-tier infrastructure (Google AI Studio / Groq, SQLite / Supabase PostgreSQL, Render / HF Spaces, Vercel).

```
                      +---------------------------------------+
                      |       Vite + React Dashboard UI       |
                      | (Intelligence Feed, Briefs, Sources)  |
                      +-------------------+-------------------+
                                          | REST API
                      +-------------------v-------------------+
                      |         FastAPI Backend Engine        |
                      +--+------------------+---------------+--+
                         |                  |               |
                         v                  v               v
            +------------+----+     +-------+-------+  +----+--------------+
            |  Crawl/Discovery|     |  LLM Gateway  |  |  APScheduler /    |
            |     Engine      |     | (Gemini/Groq) |  |  GH Actions Cron  |
            +------------+----+     +-------+-------+  +----+--------------+
                         |                  |               |
                         v                  v               v
            +------------+------------------+---------------+--+
            |       SQLAlchemy Database Layer (SQLite/PG)     |
            +-------------------------------------------------+
```

---

## 2. Dynamic Source Discovery Pipeline

The discovery engine dynamically locates relevant intelligence sources across 4 distinct categories:

| Category | Primary Discovery Vectors | Data Harvest Technique |
| :--- | :--- | :--- |
| **Customers** | Reddit (`r/`, user comments), G2/Capterra/Trustpilot snippets, industry forums, Hacker News threads | RSS/JSON feed parsing, HN Algolia API queries (`https://hn.algolia.com/api/v1/search`), targeted DDG queries |
| **Competitors** | Dynamic discovery of 5-10 direct/substitute competitors via positioning similarity, Google News RSS, company blogs | Google News RSS topic feeds (`news.google.com/rss/search?q={competitor}`), sitemaps, Atom/RSS feeds |
| **Market** | Regulatory bodies, industry publications, trade press, macroeconomic signals | Google News RSS sector queries, industry RSS aggregation, DDG News |
| **Internal** | Uploaded sales objection notes, lost-deal logs, customer tickets, meeting transcripts | Multipart file upload (CSV, Excel `.xlsx`, PDF, Plaintext), regex & NLP tabular chunking |

### Discovery Workflow
1. When a company is created (`name` + `website`), the crawler extracts homepage metadata, positioning, target audience, and product lines.
2. Discovery queries are synthesized:
   - `{company_name} alternatives review complaints`
   - `"{competitor}" launch OR pricing OR partnership`
   - `site:reddit.com "{problem_space}" recommendation`
   - Google News RSS: `https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en`
3. Sources are ranked by:
   - **Specificity** (0-100): How specifically the source focuses on the target market vs. general news.
   - **Recency** (0-100): Publication activity and update frequency.
   - **Credibility** (0-100): Domain authority, editorial integrity, and verifiable authorship.
4. User reviews and approves candidate sources (minimum 20 approved for production tracking).

---

## 3. Crawling & Parsing Engine

### Compliance & Ethics
- **Robots.txt Parser**: `urllib.robotparser.RobotFileParser` checks all target domains before HTTP requests. Disallowed paths are strictly bypassed.
- **Identifiable User-Agent**: All crawler requests declare `SignalStackBot/1.0 (+https://github.com/signal-stack/signal-stack; intelligence-engine)`.
- **Politeness & Rate Limits**: Requests to any given host are paced with minimum delays and exponential backoff on HTTP 429.

### Fetch Pipeline
```
[Candidate Source URL]
        |
        v
[Robots.txt Verification] ---> Disallowed: Log & Skip
        | Allowed
        v
[Feed Detection (RSS/Atom)]
     /      \
(Feed Found) (No Feed)
   /          \
  v            v
[feedparser]  [httpx GET with HTML clean]
  |            |
  |            v
  |           [trafilatura extraction / BeautifulSoup fallback]
  \            /
   v          v
[Extracted Items: Title, Link, PubDate, FullText, ContentHash]
```

### Content Hashing & Deduplication
- Content deduplication utilizes SHA-256 hashing of normalized body text (`re.sub(r'\s+', '', text).lower()`).
- Near-duplicate detection compares normalized title Jaccard similarity and Levenshtein distance: if title similarity > 0.85 within a 7-day sliding window, the item is recognized as a duplicate and merged to avoid clutter.

---

## 4. Multi-Dimensional Ranking & Scoring System

Every discovered signal is evaluated along six distinct, non-conflated dimensions:

$$\text{Rank Score} = w_r S_r + w_i S_i + w_u S_u + w_c S_c + w_t S_t + w_n S_n$$

Where:
- $S_r$ = **Strategic Relevance** (0-100): Alignment with company's 6-12 month priorities and business lines.
- $S_i$ = **Business Impact** (0-100): Potential magnitude on revenue, customer churn, or competitive moat.
- $S_u$ = **Urgency** (0-100): Velocity requirement for management response (e.g. today vs this quarter).
- $S_c$ = **Source Credibility & Reliability** (0-100): Objective track record of the publisher or user account.
- $S_t$ = **Recency** (0-100): Decay function based on days since publication ($e^{-\lambda \cdot \Delta t}$).
- $S_n$ = **Novelty** (0-100): Degree of new information vs. previously captured intelligence.

### Explainability Mandate
Every ranked signal includes an explicit `rank_explanation` string (e.g., *"Ranked #1 because competitor announced a direct pricing cut targeting MeetUniversity's core tier with high credibility and immediate 48h urgency"*).
LLM confidence is **never** used as a proxy for empirical factuality.

---

## 5. AI Analysis Engine & Truth Separation

### Model Gateway Architecture
```
[Analysis Request (Pydantic Schema)]
                 |
                 v
     [LLMGateway.generate_structured()]
           /                   \
(GEMINI_API_KEY set)    (Fallback / GROQ_API_KEY)
         /                       \
        v                         v
[Google GenAI Client]       [Groq API Client]
(gemini-2.5-flash / pro)    (llama-3.3-70b-versatile)
        \                         /
         \                       /
          v                     v
    [Pydantic Validation & JSON-Schema Enforcement]
                 |
                 v
[SignalAnalysis Object: facts, interpretation, actions]
```

### Signal Extraction Schema
```json
{
  "what_happened": "Clear factual summary of the event",
  "publication_date": "YYYY-MM-DD",
  "source_url": "https://...",
  "verified": true,
  "verification_reasoning": "Confirmed via official press release and SEC filing",
  "why_it_matters": "Direct threat to Enterprise subscription tier",
  "affected_business_area": "Product / Sales / Pricing / Marketing",
  "signal_type": "opportunity | threat | neutral",
  "urgency": "immediate | this_week | monitor",
  "suggested_action": "Evaluate bundle pricing defense for international admissions",
  "facts": ["Fact 1 with citation", "Fact 2 with citation"],
  "ai_interpretation": "Strategic inference deduced from facts"
}
```

---

## 6. Monday Morning Brief Engine

The weekly brief synthesizes actionable intelligence into a crisp, executive-grade brief:
1. **Executive Summary**: Top 5 critical developments of the week.
2. **Customer Signals**: Voice-of-customer excerpts, recurring complaints, unaddressed desires.
3. **Competitor Intelligence**: Product launches, pricing tweaks, partnerships, executive hires.
4. **Market Intelligence**: Regulatory shifts, macro factors, tech developments.
5. **Internal Business Intelligence**: Correlated sales friction points, lost-deal patterns from internal uploads.
6. **Opportunities (At least 3)**: Each tied to specific evidence, quantified impact, concrete next step, and priority.
7. **Risks & Threats**: Strategic vulnerabilities exposed by the week's signals.
8. **Recommended Actions This Week**: Prioritized table containing Action, Rationale, and Designated Owner (e.g., VP Product, Head of Growth).
9. **What to Watch**: Emerging early-stage indicators to track over subsequent cycles.
10. **Source Appendix**: Complete audit trail with Source Name, Link, Publication Date, Discovery Date, Verbatim Snippet, Verification Status.

*If any category experiences zero signals during a cycle, the system explicitly reports "No significant developments detected this cycle" rather than hallucinating filler.*

---

## 7. Scheduling, Reliability & Context-Change

### Dual-Cadence Automation
1. **Weekly Brief Engine**: Triggers source crawls, dedupes content, performs AI analysis, scores items, compiles Monday Brief, and records action items.
2. **Monthly Signal Stack Audit**: Evaluates source health (HTTP status, error rates, frequency of relevant signals). Identifies dead URLs, stagnant sources, or sources with declining relevance; proposes additions/removals.

### Resilient Execution
- Local execution leverages **APScheduler** background threads.
- Cloud hosts (Render, Supabase) leverage secure token-authenticated endpoints (`/api/scheduler/trigger-weekly`, `/api/scheduler/trigger-monthly`) called by **GitHub Actions cron** workflows to avoid cold-boot sleep limitations.

### Context-Change Engine
When a company pivots (e.g. expanding from Indian student admissions to UK/European direct enrollment):
- The system takes the new context, reassesses existing sources against the updated scope.
- Flags outdated competitors/sources as `deprecated`.
- Discovers 5-10 new category-aligned sources and logs an explicit audit trail explaining why each source was kept, replaced, or added.
