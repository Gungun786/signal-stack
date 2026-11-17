# Signal Stack — Cost & Free-Tier Specifications

Signal Stack is built strictly with **100% free-tier services, open-source libraries, and zero paid API subscriptions**.

| Component | Provider / Tool | Plan / Tier | Free-Tier Limits & Quotas | Strategies to Stay Free |
| :--- | :--- | :--- | :--- | :--- |
| **Primary LLM** | Google AI Studio (Gemini API) | Free Tier (`gemini-2.5-flash` / `gemini-1.5-flash`) | 15 Requests Per Minute (RPM), 1 Million Tokens Per Minute (TPM), 1,500 Requests Per Day (RPD). | Exponential backoff retry loop, batch summarization, compact JSON prompt structuring. |
| **Fallback LLM** | Groq Cloud API | Free Tier (`llama-3.3-70b-versatile`, `mixtral-8x7b-32768`) | 30 RPM, 6,000 TPM, 14,400 RPD on Llama 3.3 70B. | Seamless failover when Gemini hits 429 rate limit or quota thresholds. |
| **Web Search & Discovery** | DuckDuckGo Search (`duckduckgo-search`), Google News RSS, Hacker News Algolia, Reddit RSS/JSON | Open Source / Public APIs | Unlimited public search queries with rate politeness headers. | No API key required; user-agent pacing and 1.5s delay between search rounds. |
| **Web Crawling & Parsing** | `trafilatura`, `feedparser`, `beautifulsoup4`, `httpx` | Open Source (Self-hosted) | Bound only by local CPU and host network bandwidth. | In-memory robots.txt caching, content-hash deduplication prevents redundant page crawls. |
| **Backend Hosting** | Render / Hugging Face Spaces | Free Tier Web Service | 750 free instance hours per month. Spins down after 15 mins of inactivity. | Woken up via GitHub Actions cron before scheduled weekly briefing runs. |
| **Database** | SQLite (local) / Supabase or Neon (cloud) | Free Tier PostgreSQL | Supabase: 500MB database storage, 2 active projects. Neon: 0.5 GB storage, serverless autosuspend. | Lean relational schema with pruned crawl raw buffers; indexed foreign keys. |
| **Frontend Hosting** | Vercel | Hobby (Free) | 100 GB bandwidth, unlimited deployments, automatic SSL certificate. | Static Vite React build assets hosted on edge CDN. |
| **Scheduled Automation** | GitHub Actions | Free Tier (Public/Private Repos) | 2,000 minutes/month for free private repositories; unlimited for public repositories. | Two lightweight cron jobs (Weekly Brief on Monday 06:00 UTC, Monthly Audit on 1st of month at 00:00 UTC). Runs take < 2 minutes. |

---

## Zero-Cost Guarantee Summary
- Total monthly cloud cost: **\$0.00**
- Total initial setup cost: **\$0.00**
- Paid scraping platform cost: **\$0.00**
- Paid vector database cost: **\$0.00**
