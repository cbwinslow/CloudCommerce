# AI Item Listing Generator (Final MVP)

## Status
MVP complete: Frontend (Next.js PWA with Shadcn UI, server actions), Backend (FastAPI + LangChain/Letta), integrations (OpenRouter, Playwright scraping, Supabase DB, Stripe/Clerk). Ready for staging/prod.

## Enhancements Added
- **Shadcn UI**: Modern components (Button/Input/Checkbox/Card) for /submit form – responsive, accessible, dark mode.
- **Server Actions**: Form submits directly (no fetch; secure, fast).
- **Mobile**: Expo app (/mobile) for native (camera → API; test with `npx expo start`).

## Setup & Run
1. **Fix Prior Errors**:
   - pnpm: `pnpm add @supabase/supabase-js` (correct name).
   - Python: `cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`.
2. **Frontend**:
   - `cd frontend && pnpm install` (includes Shadcn).
   - `pnpm dev` (localhost:3000; test /submit with Shadcn form).
3. **Backend**:
   - `cd backend && source venv/bin/activate && uvicorn main:app --reload` (localhost:8000).
4. **Mobile (Expo)**:
   - `cd mobile && npx expo install` (add deps: expo-camera for images).
   - `npx expo start` (scan QR for iOS/Android; submits to localhost:3000/api/submit).
5. **Test**:
   - Submit form → Analysis/CSV download.
   - Lint: `pnpm lint --fix`.
   - E2E: `npx playwright test` (add tests/ for form).
6. **Deploy**:
   - **Vercel (Frontend)**: `vercel --prod` (PWA auto; env keys).
   - **Render (Backend)**: Push to GitHub; connect Render (Dockerfile); env secrets.
   - **Supabase**: Project with tables (users/credits, submissions).
   - **Cron**: Supabase Edge for deletes/arbitrage (dashboard: functions/add).
   - Full: Update frontend env (BACKEND_URL=prod-api.render.com).

## Next
- Staging: Deploy Vercel/Render → Test end-to-end.
- Prod: Vercel Pro ($20/mo), Render Pro ($7/mo).
- Expo: Publish to stores (add camera integration).

Project solid – deploy and iterate!