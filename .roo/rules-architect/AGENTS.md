# Project Architecture Rules (Non-Obvious Only)
- Frontend/Backend split: Next.js serverless proxies FastAPI via vercel.json rewrites (/crew -> backend); direct localhost:8000 fails in Vercel.
- Stateful agents via Letta in backend/core/agents/submit_agent.py (transient memory; resets on restart, no persistent state).
- Image flow: Mobile Expo -> Supabase storage (transient URLs) -> OpenRouter LLaVA via lib/openrouter.ts (auto-delete 1h; no base64).
- Monetization coupling: Supabase users table + Stripe metadata (unlimited subs bypass credits; deduct before LLM, no rollback).
- Scraping architecture: Frontend lib/scraper.ts (axios + delays) for sync; backend Playwright for async sites (eBay/Amazon integration).