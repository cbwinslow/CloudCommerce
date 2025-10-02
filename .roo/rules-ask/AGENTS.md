# Project Documentation Rules (Non-Obvious Only)
- /docs/ subdirs (e.g., openrouter, supabase) outdated; canonical refs in lib/openrouter.ts and app/api/submit/route.ts code.
- Backend Letta stateful memory transient (resets per session); see backend/core/agents/submit_agent.py inline comments.
- Mobile Expo camera uploads to Supabase storage first (transient URLs); adapt to prod BACKEND_URL (missing from .env.example).
- vercel.json rewrites /crew to backend; direct localhost:8000 fails in Vercel (serverless isolation).
- Shadcn UI components in components/ (e.g., SubmissionForm.tsx); Tailwind config no plugins (extend only gradients).