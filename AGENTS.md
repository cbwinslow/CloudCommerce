# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Build/Lint/Test Commands
- Frontend: `pnpm dev` (uses Turbopack); single lint: `pnpm lint -- --file src/app/page.tsx`.
- Backend: `cd backend && source venv/bin/activate && uvicorn main:app --reload` (venv required; no tests).
- Mobile: `cd mobile && npx expo start` (scan QR; no single-test command).
- No unit tests; E2E via Playwright: `npx playwright test` (add tests/ dir first).

## Code Style Guidelines
- TS: Strict mode, esnext modules, @/* paths resolve to root (tsconfig.json).
- Imports: Use OpenRouter client from lib/openrouter.ts for all LLMs (not direct OpenAI).
- Formatting: ESLint next/core-web-vitals; Tailwind via Shadcn (no custom plugins).
- Types: Pydantic for backend models; Zod for frontend validation (zod dep).
- Naming: snake_case in Python (FastAPI); camelCase in TS/JS.
- Error Handling: Wrap API calls in try/catch; use Sentry spans for tracing (backend/main.py).
- Non-obvious: Image URLs transient—delete after 1h processing (vercel.json proxy).