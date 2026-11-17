# Signal Stack

Signal Stack is an automated market and competitive intelligence engine that monitors industry movements, customer sentiment, regulatory changes, and internal sales friction to generate structured Monday Morning Briefs.

Every reported item includes verifiable sources, publication dates, discovery timestamps, and source snippets, keeping raw observations strictly separated from strategic analysis.

---

## Overview & Architecture

```
                    ┌─────────────────────────────────────────┐
                    │        React + Vite Dashboard UI        │
                    │  (Feed, Briefs, Source Radar, Audit)    │
                    └────────────────────┬────────────────────┘
                                         │ REST API
                    ┌────────────────────▼────────────────────┐
                    │          FastAPI Backend Engine         │
                    └───┬───────────────────┬───────────────┬─┘
                        │                   │               │
                        ▼                   ▼               ▼
           ┌────────────┴────────┐ ┌────────┴────────┐ ┌────┴───────────────┐
           │   Crawler Engine    │ │   LLM Gateway   │ │  APScheduler &     │
           │  (ddgs, RSS, feeds) │ │ (Gemini & Groq) │ │  GitHub Actions    │
           └────────────┬────────┘ └────────┬────────┘ └────┬───────────────┘
                        │                   │               │
                        ▼                   ▼               ▼
           ┌────────────────────────────────────────────────┴─┐
           │      Database Layer (SQLite / PostgreSQL)        │
           └──────────────────────────────────────────────────┘
```

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, APScheduler, ReportLab.
- **Crawlers**: `trafilatura`, `feedparser`, `ddgs`, `beautifulsoup4`, `httpx` (robots.txt compliant).
- **Frontend**: React 19, Vite, Lucide Icons.
- **LLM Gateway**: Provider-agnostic gateway prioritizing Gemini Flash free tier, with automatic failover to Groq (Llama 3.3 70B) and JSON-schema validated outputs.

---

## Core Capabilities

1. **Dynamic Setup & Discovery**: Enter a company name and website to run an automated crawl and a 10-step adaptive interview covering business lines, revenue drivers, churn factors, and priorities.
2. **Four-Category Signal Stack**:
   - **Customers**: Reddit discussions, forums, and review hubs capturing recurring pain points in user language.
   - **Competitors**: Tracks 5-10 direct competitors for product releases, pricing changes, partnerships, and key hires.
   - **Market**: Regulatory updates, policy shifts, and industry news filtered from general news.
   - **Internal**: File parser for CSV, Excel (.xlsx), PDF, and text logs extracting sales objections, feature requests, and churn reasons.
3. **Multi-Factor Ranking**: Ranks items using separate, explicit metrics: Strategic Relevance (30%), Business Impact (25%), Urgency (20%), Source Credibility (15%), Recency (10%), and Novelty. Every score includes a transparent explanation.
4. **Monday Morning Brief**: Generates an executive summary (top 5), customer signals, competitor movements, regulatory updates, internal signals, 3+ opportunities tied to evidence, material risks, and an action plan with designated owners. Exports to Markdown, HTML, and PDF.
5. **Context Pivot**: If business priorities or product lines shift, the engine reassesses existing sources, deprecates outdated feeds, discovers new sources, and records an audit log.

---

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### 1. Clone & Setup Environment
```bash
git clone https://github.com/Gungun786/signal-stack.git
cd signal-stack
cp .env.example .env
```
Add your free `GEMINI_API_KEY` (Google AI Studio) or `GROQ_API_KEY` (Groq Console) to `.env` if available. The system also includes rule-based parsing fallbacks.

### 2. Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```
API Documentation: `http://localhost:8000/docs`

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Dashboard: `http://localhost:5173`

---

## Docker Setup

To run everything in a container:
```bash
docker-compose up --build
```
Open `http://localhost:8000` to access the full application.

---

## Sample Data & Demo Reports

The repository comes populated with empirical data collected from live web sources across three different sectors:

| Company | Sector | Approved Sources | Collected Signals | Briefs |
| :--- | :--- | :--- | :--- | :--- |
| **MeetUniversity** | EdTech / Admissions | 20 sources | 295 records | [PDF](reports/meetuniversity_monday_brief.pdf) &bull; [MD](reports/meetuniversity_monday_brief.md) &bull; [HTML](reports/meetuniversity_monday_brief.html) |
| **Supabase** | Cloud Infrastructure | 23 sources | 350 records | [PDF](reports/supabase_monday_brief.pdf) &bull; [MD](reports/supabase_monday_brief.md) &bull; [HTML](reports/supabase_monday_brief.html) |
| **Razorpay** | FinTech / Payments | 23 sources | 394 records | [PDF](reports/razorpay_monday_brief.pdf) &bull; [MD](reports/razorpay_monday_brief.md) &bull; [HTML](reports/razorpay_monday_brief.html) |

To re-run the crawl and analysis pipeline locally:
```bash
python backend/run_demos.py
```

---

## Deployment

### 1. Database (Supabase / Neon)
1. Create a free project at [supabase.com](https://supabase.com) or [neon.tech](https://neon.tech).
2. Copy your PostgreSQL connection URI from database settings:
   ```
   postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```

### 2. Backend (Render)
1. Go to [render.com](https://render.com) and create a new **Blueprint** service pointing to your repository.
2. Render uses `render.yaml` to configure the web service automatically.
3. Supply the environment variables:
   - `DATABASE_URL`: Your PostgreSQL connection URI.
   - `GEMINI_API_KEY`: Your Gemini key.
   - `CRON_SECRET`: Secret token used to authorize cron runs.
4. Deploy the service.

### 3. Frontend (Vercel)
1. Import the repository at [vercel.com](https://vercel.com).
2. Set the root directory to `frontend`.
3. Deploy. The included `frontend/vercel.json` proxies `/api` calls directly to the Render backend.

### 4. Scheduled Jobs (GitHub Actions)
Add these repository secrets under **Settings &rarr; Secrets &rarr; Actions**:
- `BACKEND_URL`: `https://signal-stack-backend.onrender.com`
- `CRON_SECRET`: Same token set on Render.

Workflows configured:
- Weekly Brief: Mondays at 06:00 UTC (`.github/workflows/weekly-brief.yml`)
- Monthly Audit: 1st of month at 00:00 UTC (`.github/workflows/monthly-audit.yml`)

---

## Screen Recording Checklist (5-10 min)

1. **Architecture & Scope (1-2 min)**:
   - High-level overview of the pipeline: Crawl &rarr; Hash Deduplication &rarr; Truth Verification &rarr; Multi-factor Ranking &rarr; Monday Brief.
   - Reference `COST.md` for free-tier constraints.
2. **Company Setup & Profile (2 min)**:
   - Show entity switcher (MeetUniversity, Supabase, Razorpay).
   - Review Company Profile: products, customers, positioning tagged with `verified` vs `assumption`.
3. **Adaptive Interview & Source Radar (2 min)**:
   - Demonstrate the 10-step adaptive interview questionnaire.
   - Show the Signal Stack view: 20+ sources filtered by category with health statuses and credibility scores.
4. **Intelligence Feed & Verification (2 min)**:
   - Filter signals by category and impact.
   - Open a signal modal showing source URL, pub date, verbatim snippet, and explanation of rank score.
5. **Monday Brief & Exports (2 min)**:
   - Review the generated Monday Brief: Top 5 developments, interactive action items, opportunities, risks.
   - Demonstrate export to Markdown, HTML, and PDF.
   - Show Context Pivot feature with audit diff.

---

## License
MIT License.
