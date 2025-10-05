# Project Debug Rules (Non-Obvious Only)
- Backend traces via Sentry spans in main.py (enable_profiling=True; view in Sentry dashboard, not console).
- Scraping failures silent in lib/scraper.ts if timeout (check axios errors; Playwright logs in backend/core/agents/submit_agent.py).
- Image URLs in Supabase storage auto-delete after 1h (no manual cleanup; transient for vision models).
- Letta agent memory transient—debug stateful flows by checking LETTA_AGENT_ID env (resets on restart).
- No unit tests; E2E Playwright requires manual tests/ dir creation (npx playwright test fails without).