# Project Tasks - AI Item Listing Generator

> See `features.md` for a consolidated features inventory, acceptance criteria, and immediate unblock checklist.

## Quick next steps (run before work)
- [ ] Create GitHub/GitLab repo and add SSH key for this machine (owner: cbwinslow)
- [ ] Fix package manifests: remove JS-scoped packages from Python requirements; replace or remove `@bitwarden/web-sdk`
- [ ] Populate `.env` from `.env.example` with dev keys (Stripe, Supabase, Clerk, OpenRouter) or enable dev-mock mode
- [ ] Install OS libs required by Playwright if running E2E locally (or rely on CI runners)

## Actionable Task Breakdown (priority-first)

The sections below break high-priority tasks into small microgoals with clear acceptance criteria and a place for an AI-agent sign-off and proof of completion. Use these when closing tasks or filing PRs.

1) Fix Dependency & Manifest Issues (Priority: Critical, ETA: 1-2 hours)
- Microgoals:
    - Scan `backend/requirements.txt`, `package.json` (root, frontend, mobile) and `setup-full.sh` for JS-scoped packages or invalid entries.
    - Remove JS-scoped / npm-only entries from Python requirements (e.g., @langchain/openai) and add a note in `backend/requirements.txt` for the corresponding JS package if needed.
    - Replace or remove non-existent npm packages (e.g., `@bitwarden/web-sdk`) and pick an alternative (e.g., `@bitwarden/sdk-napi` or use Bitwarden CLI wrapper).
    - Run `pnpm install` (frontend) and `pip install -r backend/requirements.txt` inside a fresh venv; fix any remaining version/type errors.
- Acceptance criteria:
    - `pnpm install` completes without 404 errors.
    - `pip install -r backend/requirements.txt` completes without JS-scoped package errors.
    - `node_modules` and Python venv exist and `next dev` and `uvicorn main:app --reload` start locally (dev ports available).
- AI agent sign-off:
    - Agent: ____________________
    - Date: ____________________
    - Short proof summary (commands run / last lines of success output):
        ```
        ...proof here...
        ```

2) Repo creation & SSH push (Priority: Critical, ETA: 15-30 mins)
- Microgoals:
    - Create repository on GitHub (owner: cbwinslow) or provide a remote URL.
    - Add this machine's SSH public key to your GitHub account.
    - Set remote `origin` to the new repo and push `dev` branch.
- Acceptance criteria:
    - `git push origin dev` succeeds and GitHub shows the branch and commits.
    - GitHub Actions triggers (if workflows present) or repo web UI shows files.
- AI agent sign-off:
    - Agent: ____________________
    - Date: ____________________
    - Remote URL: ____________________
    - Proof (push output / run):
        ```
        ...proof here...
        ```

3) Frontend dev flow: local verification (Priority: High, ETA: 30-60 mins)
- Microgoals:
    - Ensure `frontend` and root `package.json` dependencies are consistent; prefer single workspace package if using root `pnpm`.
    - Run `pnpm install` and `pnpm dev` (or `cd frontend && pnpm dev`) and fix any runtime errors.
    - Verify main page (`/`) loads, sign-in/sign-up buttons route, and the submission form renders when signed in.
- Acceptance criteria:
    - Browser loads `http://localhost:3000` without JS console errors preventing UI.
    - Submission form visible (signed-in or mock user) and `Generate Listings` hits `/api/submit` (network call visible in devtools).
- AI agent sign-off:
    - Agent: ____________________
    - Date: ____________________
    - Proof (screenshot URL or terminal output):
        ```
        ...proof here...
        ```

4) Backend dev flow: local verification (Priority: High, ETA: 30-60 mins)
- Microgoals:
    - Create & activate Python venv: `python -m venv backend/venv && source backend/venv/bin/activate`.
    - Clean `backend/requirements.txt` and install.
    - Start `uvicorn backend.main:app --reload` and exercise `/submit` endpoint with a sample POST (curl or Postman).
- Acceptance criteria:
    - `uvicorn` runs and `/submit` returns 200+ JSON for sample request (mock images/summary allowed).
    - Logs show Sentry initialization line when SENTRY_DSN is set to a test DSN.
- AI agent sign-off:
    - Agent: ____________________
    - Date: ____________________
    - Proof (curl output / server logs):
        ```
        ...proof here...
        ```

5) CI / Tests / Playwright (Priority: High, ETA: 1-3 hours)
- Microgoals:
    - Ensure `package.json` scripts for lint/test exist and run locally.
    - Install Playwright dependencies and OS libs (or plan to run tests in CI runner). For Debian/Ubuntu, this is `apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxss1 libasound2 libgbm1 libxshmfence1 libgconf-2-4 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxrandr2 libpangocairo-1.0-0 libxkbcommon0 libxkbcommon-x11-0 libgtk-3-0`.
    - Run a minimal Playwright test that just opens `/` and checks for the page title.
- Acceptance criteria:
    - `npx playwright test` runs at least the smoke test and exits success on CI runner or local host with OS libs installed.
    - CI workflow runs unit tests and lints on push.
- AI agent sign-off:
    - Agent: ____________________
    - Date: ____________________
    - Proof (playwright output / CI run link):
        ```
        ...proof here...
        ```

Notes:
- If any microgoal is blocked by credentials (Stripe, Supabase, OpenRouter), enable `DEV_MOCK=true` in `.env.local` and update `features.md` to indicate which features are running in mock mode.
- Add brief PR template and an automated checklist (I can add this) so contributors attach AI sign-off with terminal output when merging.


## Setup & Development Tasks

### 1. Fix Dependency Issues
- [x] Fix pnpm dependency: `pnpm add @supabase/supabase-js` (correct package name)
- [ ] Set up Python virtual environment and install requirements
- [x] Verify all dependencies are correctly installed

### 2. Frontend Setup & Development
- [x] Install frontend dependencies: `cd frontend && pnpm install`
- [x] Start frontend development server: `pnpm dev` (localhost:3000)
- [ ] Test /submit form with Shadcn UI components
- [ ] Verify PWA functionality and responsive design

### 3. Backend Setup & Development
- [x] Set up Python virtual environment: `cd backend && python -m venv venv`
- [x] Activate virtual environment and install requirements
- [x] Start backend server: `uvicorn main:app --reload` (localhost:8000)
- [x] Verify API endpoints are working

### 4. Mobile App Setup
- [x] Install mobile dependencies: `cd mobile && npx expo install`
- [x] Add camera dependencies for image functionality
- [x] Start Expo development server: `npx expo start`
- [ ] Test mobile app submission to API

### 5. Integration Testing
- [x] Test complete form submission workflow
- [x] Verify analysis and CSV download functionality
- [x] Test mobile app integration with frontend API
- [x] Run linting: `pnpm lint --fix`
- [x] Run E2E tests: `npx playwright test`

## Deployment Tasks

### 6. Staging Deployment
- [ ] Deploy frontend to Vercel staging environment
- [ ] Deploy backend to Render staging environment
- [ ] Set up Supabase project with required tables
- [ ] Configure environment variables for staging
- [ ] Set up Supabase Edge Functions for cron jobs
- [ ] Test end-to-end functionality in staging

### 7. Production Deployment
- [ ] Upgrade to Vercel Pro ($20/mo)
- [ ] Upgrade to Render Pro ($7/mo)
- [ ] Deploy frontend to Vercel production
- [ ] Deploy backend to Render production
- [ ] Update environment variables for production URLs
- [ ] Test complete production workflow

### 8. Mobile App Production
- [ ] Add camera integration to mobile app
- [ ] Publish Expo app to app stores
- [ ] Test production mobile app functionality

## Maintenance & Monitoring Tasks

### 9. Monitoring Setup
- [ ] Set up error monitoring with Sentry
- [ ] Configure logging for production
- [ ] Set up performance monitoring
- [ ] Create dashboard for key metrics

### 10. Documentation Updates
- [ ] Update API documentation
- [ ] Create user guides for all platforms
- [ ] Document deployment procedures
- [ ] Create troubleshooting guides

## Next Phase: Production Readiness & Market Launch

### Phase 1: Core Feature Completion (Week 1-2)
1. **User Management & Authentication**
   - [x] Set up Clerk authentication (already configured)
   - [x] Create sign-in/sign-up pages
   - [x] Add password reset functionality
   - [x] Create user profile management page
   - [ ] Add social login options (Google, GitHub)
   - [ ] Implement role-based access control

2. **Image Upload & Storage System**
   - [x] Set up Supabase storage (already configured)
   - [x] Implement proper drag-and-drop image upload
   - [ ] Add image compression and optimization
   - [x] Create image gallery management
   - [x] Add support for multiple image formats
   - [x] Add image preview and deletion

3. **Advanced Analysis Features**
   - [ ] Implement batch processing for multiple items
   - [ ] Add real-time progress indicators
   - [ ] Create analysis history and favorites
   - [ ] Add export options (PDF, Excel, JSON)
   - [ ] Implement analysis templates

4. **Enhanced UI/UX**
   - [x] Complete Shadcn UI component integration
   - [ ] Add dark/light mode toggle
   - [x] Implement responsive design improvements
   - [x] Add loading states and skeletons
   - [x] Create intuitive navigation and breadcrumbs
   - [x] Add proper styling and animations

5. **Error Handling & Validation**
   - [x] Add comprehensive form validation
   - [x] Implement user-friendly error messages
   - [x] Add retry mechanisms for failed requests
   - [x] Create fallback UI states
   - [x] Add input sanitization and validation

### Phase 2: Performance & Scalability (Week 3-4)
6. **Performance Optimization**
   - [ ] Implement code splitting and lazy loading
   - [ ] Optimize bundle size and reduce unused code
   - [ ] Add service worker for offline functionality
   - [ ] Implement virtual scrolling for large lists
   - [ ] Add performance monitoring

7. **Caching & Rate Limiting**
   - [ ] Implement Redis caching for API responses
   - [ ] Add client-side caching strategies
   - [ ] Create rate limiting for API endpoints
   - [ ] Implement request deduplication
   - [ ] Add cache invalidation strategies

8. **Database Optimization**
   - [ ] Optimize database queries and indexes
   - [ ] Implement database connection pooling
   - [ ] Add database migration system
   - [ ] Set up read replicas for scaling
   - [ ] Implement data archiving

9. **CDN & Asset Optimization**
   - [ ] Set up CDN for static assets
   - [ ] Implement image optimization pipeline
   - [ ] Add asset preloading strategies
   - [ ] Optimize font loading
   - [ ] Implement critical CSS inlining

10. **Load Testing**
    - [ ] Set up load testing environment
    - [ ] Create performance benchmarks
    - [ ] Identify and fix performance bottlenecks
    - [ ] Implement auto-scaling strategies
    - [ ] Add performance regression testing

### Phase 3: Business & Monetization (Week 5-6)
11. **Subscription Management**
    - [ ] Implement subscription tier system
    - [ ] Add usage-based billing
    - [ ] Create subscription management UI
    - [ ] Add prorated billing for plan changes
    - [ ] Implement dunning management

12. **Usage Analytics & Billing**
    - [ ] Track and display usage metrics
    - [ ] Create billing history and invoices
    - [ ] Add cost estimation tools
    - [ ] Implement usage alerts and notifications
    - [ ] Create financial reporting dashboard

13. **Admin Dashboard**
    - [ ] Build admin user management interface
    - [ ] Create system monitoring dashboard
    - [ ] Add analytics and reporting tools
    - [ ] Implement feature flag management
    - [ ] Create content management system

14. **Customer Support System**
    - [ ] Implement ticketing system
    - [ ] Add live chat support
    - [ ] Create knowledge base and FAQ
    - [ ] Add user feedback collection
    - [ ] Implement support analytics

15. **API Rate Limiting & Quotas**
    - [ ] Implement per-user rate limiting
    - [ ] Add quota management system
    - [ ] Create usage dashboard for users
    - [ ] Add overage billing for exceeded quotas
    - [ ] Implement fair usage policies

### Phase 4: Security & Compliance (Week 7-8)
16. **Security Hardening**
    - [ ] Implement input validation and sanitization
    - [ ] Add CSRF protection
    - [ ] Implement secure headers (HSTS, CSP, etc.)
    - [ ] Add API security best practices
    - [ ] Implement secure session management

17. **Data Privacy Compliance**
    - [ ] Add GDPR compliance features
    - [ ] Implement data retention policies
    - [ ] Add privacy policy and terms of service
    - [ ] Create data export/deletion tools
    - [ ] Add cookie consent management

18. **Backup & Recovery**
    - [ ] Set up automated database backups
    - [ ] Implement file storage backup
    - [ ] Create disaster recovery procedures
    - [ ] Add backup monitoring and alerts
    - [ ] Test backup restoration procedures

19. **Audit Logging**
    - [ ] Implement comprehensive audit trails
    - [ ] Add user activity logging
    - [ ] Create security event monitoring
    - [ ] Add compliance reporting
    - [ ] Implement log retention policies

20. **SSL & HTTPS**
    - [ ] Set up SSL certificates for all domains
    - [ ] Implement HTTPS redirect
    - [ ] Add security monitoring
    - [ ] Implement certificate auto-renewal
    - [ ] Add SSL security headers

### Phase 5: Marketing & Launch (Week 9-10)
21. **Landing Pages & SEO**
    - [ ] Create compelling landing pages
    - [ ] Implement SEO optimization
    - [ ] Add meta tags and structured data
    - [ ] Create sitemap and robots.txt
    - [ ] Add social media meta tags

22. **Analytics & Tracking**
    - [ ] Set up Google Analytics 4
    - [ ] Implement conversion tracking
    - [ ] Add user behavior analytics
    - [ ] Create custom event tracking
    - [ ] Add A/B testing framework

23. **Marketing Automation**
    - [ ] Set up email marketing automation
    - [ ] Create lead capture forms
    - [ ] Implement referral program
    - [ ] Add social media integrations
    - [ ] Create marketing campaign tools

24. **Beta Testing Program**
    - [ ] Set up beta testing environment
    - [ ] Create beta user management
    - [ ] Implement feedback collection
    - [ ] Add feature request system
    - [ ] Create beta-to-production workflow

25. **Launch Preparation**
    - [ ] Create launch checklist
    - [ ] Prepare press kit and materials
    - [ ] Set up social media accounts
    - [ ] Create demo accounts and content
    - [ ] Plan launch events and announcements

### Phase 6: Operations & Maintenance (Week 11-12)
26. **Monitoring & Alerting**
    - [ ] Set up application performance monitoring
    - [ ] Implement error tracking and alerting
    - [ ] Add uptime monitoring
    - [ ] Create custom dashboards
    - [ ] Implement incident response procedures

27. **Documentation**
    - [ ] Create comprehensive API documentation
    - [ ] Write user guides and tutorials
    - [ ] Create developer documentation
    - [ ] Add video tutorials and demos
    - [ ] Create troubleshooting guides

28. **CI/CD Pipeline**
    - [ ] Set up automated testing pipeline
    - [ ] Implement continuous integration
    - [ ] Add automated deployment
    - [ ] Create staging environment workflow
    - [ ] Add rollback procedures

29. **Disaster Recovery**
    - [ ] Create disaster recovery plan
    - [ ] Set up redundant systems
    - [ ] Implement failover mechanisms
    - [ ] Add data center redundancy
    - [ ] Create business continuity procedures

30. **Customer Success Tools**
    - [ ] Create onboarding workflows
    - [ ] Add in-app guidance and tooltips
    - [ ] Implement user feedback surveys
    - [ ] Create customer success metrics
    - [ ] Add churn prevention tools

## Priority Order:
1. **Core Feature Completion** (Foundation)
2. **Performance & Scalability** (Reliability)
3. **Business & Monetization** (Revenue)
4. **Security & Compliance** (Trust)
5. **Marketing & Launch** (Growth)
6. **Operations & Maintenance** (Sustainability)
