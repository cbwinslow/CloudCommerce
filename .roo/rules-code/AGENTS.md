# Project Coding Rules (Non-Obvious Only)
- Proxy all CrewAI calls via lib/crew.ts to backend /crew endpoint (vercel.json rewrite required; direct localhost:8000 fails in Vercel serverless).
- Use LettaClient in backend/core/agents/submit_agent.py for stateful agent memory (transient; stateless LLMs ignore prior submissions).
- Scraping in lib/scraper.ts mandates 1s delays and 'ItemAnalyzerBot/1.0' User-Agent (bypasses rate limits; backend Playwright for async sites like eBay).
- Vision analysis requires image URLs (not base64) sent to OpenRouter LLaVA via lib/openrouter.ts (mobile Expo uploads to Supabase storage first).
- Deduct credits from Supabase 'users' table before LLM calls in app/api/submit/route.ts (unlimited subs via Stripe metadata; no rollback on failure).
- Generate CSV in app/api/submit/route.ts using PapaParse only after scraping (hardcoded platforms: eBay/Amazon/FB; arbitrage flags <70% avg price).
- Backend secrets rotate via Bitwarden in main.py /rotate-secrets (cron via Supabase Edge; update env without restart).