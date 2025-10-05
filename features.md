# CloudCommerce — Features Inventory

This file lists the product features implemented or planned in the workspace and provides concise acceptance criteria and a short contract for each major area. Use this as the single source-of-truth when closing tasks or creating release notes.

## High-level features

- Monitoring & Tracing
  - Sentry (frontend + backend) for errors, performance and session replay
  - LangFuse traces for LLM observability
  - Acceptance: Errors show up in Sentry in staging when triggered by a dev route; LLM requests include a trace id that appears in LangFuse or logs.

- Payments & Paywall
  - Stripe Checkout + webhook, dev bypass mode and gating for paid features
  - Acceptance: Creating a checkout session returns a valid session id; webhook verifies signature and records payment in Supabase test environment.

- Authentication & Teams
  - Clerk for user auth + JWT/cookie support; org/team membership in Supabase
  - Acceptance: Sign-up and sign-in work; team members can share listings where authorized.

- AI / RAG / Semantic Search
  - LiteLLM proxy / OpenRouter client, LlamaIndex for retrieval, pgvector embeddings in Supabase
  - Acceptance: Index a document and return relevant hits for a semantic query; embeddings stored in pgvector.

- Marketplace Integrations (MCP)
  - Upload stubs and research agents for eBay, Amazon, Facebook Marketplace, Mercari, Goodwill, GSA, Craigslist
  - Acceptance: Agents run in dev returning simulated success; integration enabled after provider API keys are supplied.

- Bulk Upload & CSV Workflows
  - CSV import, batch LLM validation, review queue and CSV export
  - Acceptance: Upload a CSV, it parses to items, items show up in review UI with confidence and rationale.

- Image Validation & Malware Scanning
  - Image format checks, optional ClamAV scanning for uploads
  - Acceptance: Non-image files rejected; ClamAV scan returns pass/fail in metadata when enabled.

- White-label & Multi-tenant
  - Org settings, custom branding assets, feature flags per org
  - Acceptance: Settings UI persists to Supabase and applies to the example org in staging.

- NFT Mock Minting & Mobile Push
  - Metadata upload + mock mint endpoint; Expo push registration skeleton
  - Acceptance: Mint endpoint returns EVM-like tx object in dev; mobile registers a device token in Supabase.

- Security & Secrets
  - Bitwarden integration planned for secret rotation; secure env usage; RLS policies in Supabase
  - Acceptance: Secrets not present in repo; sample vault integration script works in dry-run mode (no credentials).

- CI / Tests / Deployment
  - GitHub Actions workflows, Dockerfiles, Playwright E2E, pytest unit tests
  - Acceptance: CI runs unit tests and lints; deploy workflow triggers a preview build.

## Minimal contracts (per subsystem)

- Payments API
  - Input: item id and plan id
  - Output: Stripe checkout session id or dev-bypass token
  - Errors: invalid item, missing env key, signature mismatch on webhook

- Submit Flow (AI analysis)
  - Input: images + listing metadata
  - Output: generated title, description, price suggestion, list of recommended marketplaces, confidence score (0-100)
  - Errors: invalid images, LLM timeout, missing embeddings

- Marketplace Upload Agent
  - Input: validated listing object + marketplace credential
  - Output: success/failure per platform and platform-specific ids/URLs
  - Errors: auth error, validation error, rate-limit

## Edge cases to cover in tests

- Empty or corrupt CSV rows
- Images with unsupported formats or very large size
- Rate-limited marketplace APIs and transient network failures
- Partial failures in multi-platform uploads (some succeed, some fail)
- Missing environment keys in CI vs local dev

## Immediate next steps (unblocks)

1. Create GitHub/GitLab repo under the project's owner (or give push access) and configure SSH keys so CI and pushes work. (Blocking for release)
2. Remove or replace incorrect package names in manifests (example: JS-scoped packages inside Python requirements; @bitwarden/web-sdk not in registry). (Blocking for reproducible setup)
3. Provide dev API keys for Stripe, Supabase and one marketplace (e.g., eBay sandbox) as CI secrets so workflow E2E can run. (Optional: use dry-run / mock mode)

## Current Development Status

**Mock Mode Enabled**: The application is currently configured to run in mock mode (`DEV_MOCK=true`) for development and testing. This allows the system to function without requiring real API keys for:
- Stripe payment processing
- Supabase database operations
- Clerk authentication
- OpenRouter AI services

**Features Running in Mock Mode**:
- ✅ Payments & Paywall (Stripe mock responses)
- ✅ Authentication & Teams (Clerk mock authentication)
- ✅ AI / RAG / Semantic Search (OpenRouter mock responses)
- ✅ Marketplace Integrations (Simulated agent responses)
- ✅ Image Validation & Malware Scanning (Mock validation)
- ✅ NFT Mock Minting & Mobile Push (Mock endpoints)

**To Enable Production Features**: Set `DEV_MOCK=false` in `.env` and `backend/.env` files and provide real API keys for all services.

## Where to find things in the repo

- Frontend: /app and /frontend/src
- Backend: /backend
- Mobile: /mobile
- Supabase migrations: /supabase/migrations
- Tests: /test-results and playwright configs

If you want, I can generate a release checklist and a short PR template that maps each feature here to a test case and documentation requirement.
