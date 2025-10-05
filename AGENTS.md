# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Coding Rules (Non-Obvious Only)

### AI & Agent Integration
- **CrewAI Calls**: Proxy all CrewAI calls via [`lib/crew.ts`](lib/crew.ts:1) to backend `/crew` endpoint (vercel.json rewrite required; direct localhost:8000 fails in Vercel serverless).
- **Stateful Memory**: Use LettaClient in [`backend/core/agents/submit_agent.py`](backend/core/agents/submit_agent.py:1) for stateful agent memory (transient; stateless LLMs ignore prior submissions).
- **Vision Analysis**: Vision analysis requires image URLs (not base64) sent to OpenRouter LLaVA via [`lib/openrouter.ts`](lib/openrouter.ts:1) (mobile Expo uploads to Supabase storage first).

### Web Scraping
- **Scraping Delays**: Scraping in [`lib/scraper.ts`](lib/scraper.ts:1) mandates 1s delays and 'ItemAnalyzerBot/1.0' User-Agent (bypasses rate limits; backend Playwright for async sites like eBay).
- **Backend Scraping**: Use backend Playwright for async sites like eBay; frontend scraping is limited to simple requests.

### Payment & Credits
- **Credit Deduction**: Deduct credits from Supabase 'users' table before LLM calls in [`app/api/submit/route.ts`](app/api/submit/route.ts:1) (unlimited subs via Stripe metadata; no rollback on failure).
- **CSV Generation**: Generate CSV in [`app/api/submit/route.ts`](app/api/submit/route.ts:1) using PapaParse only after scraping (hardcoded platforms: eBay/Amazon/FB; arbitrage flags <70% avg price).

### Security & Secrets
- **Secrets Rotation**: Backend secrets rotate via Bitwarden in [`main.py`](backend/main.py:1) `/rotate-secrets` (cron via Supabase Edge; update env without restart).
- **Image URLs**: Image URLs are transient—delete after 1h processing (vercel.json proxy).

## Build/Lint/Test Commands

### Frontend Development
- **Development Server**: `pnpm dev` (uses Turbopack)
- **Single File Lint**: `pnpm lint -- --file src/app/page.tsx`
- **Build**: `pnpm build`
- **Start**: `pnpm start`

### Backend Development
- **Environment Setup**: `cd backend && source venv/bin/activate && pip install -r requirements.txt`
- **Development Server**: `cd backend && source venv/bin/activate && uvicorn main:app --reload` (venv required; no tests)
- **Production**: `cd backend && source venv/bin/activate && uvicorn main:app`

### Mobile Development
- **Development Server**: `cd mobile && npx expo start` (scan QR; no single-test command)
- **Build iOS**: `npx expo build:ios`
- **Build Android**: `npx expo build:android`

### Testing
- **E2E Testing**: `npx playwright test` (add tests/ dir first)
- **No Unit Tests**: Currently no unit tests; E2E via Playwright only

## Code Style Guidelines

### TypeScript (Frontend)
- **Strict Mode**: Enable strict TypeScript mode
- **Modules**: Use esnext modules
- **Paths**: `@/*` paths resolve to root (tsconfig.json)
- **Imports**: Use OpenRouter client from [`lib/openrouter.ts`](lib/openrouter.ts:1) for all LLMs (not direct OpenAI)

### Python (Backend)
- **Models**: Use Pydantic for backend models
- **Naming**: snake_case in Python (FastAPI)
- **FastAPI**: Follow FastAPI best practices

### General
- **Formatting**: ESLint next/core-web-vitals; Tailwind via Shadcn (no custom plugins)
- **Validation**: Zod for frontend validation (zod dep)
- **Naming**: camelCase in TS/JS
- **Error Handling**: Wrap API calls in try/catch; use Sentry spans for tracing ([`backend/main.py`](backend/main.py:1))

## Architecture Overview

### Multi-Agent System
The project uses a sophisticated multi-agent architecture:

1. **Submit Agent** ([`backend/core/agents/submit_agent.py`](backend/core/agents/submit_agent.py:1))
   - Handles item analysis and listing generation
   - Uses Letta for stateful memory
   - Integrates with CrewAI for complex workflows

2. **Arbitrage Crew** ([`backend/core/agents/arbitrage_crew.py`](backend/core/agents/arbitrage_crew.py:1))
   - Specialized for market analysis and arbitrage detection
   - Uses CrewAI for multi-agent collaboration
   - Identifies underpriced items across platforms

### Frontend Integration
- **CrewAI Proxy**: Frontend CrewAI calls go through [`lib/crew.ts`](lib/crew.ts:1) which proxies to backend
- **Server Actions**: Form submissions use Next.js server actions for security
- **Real-time Updates**: Live status updates during processing

### Data Flow
1. User uploads images and description
2. Frontend validates and sends to `/api/submit`
3. Backend checks credits and processes through agents
4. Agents analyze images and scrape market data
5. Generate listings and CSV export
6. Return results to frontend

## Environment Configuration

### Required Environment Variables
```bash
# Authentication
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_clerk_secret_key

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# AI Services
OPENROUTER_API_KEY=your_openrouter_api_key
LETTA_API_KEY=your_letta_api_key

# Payment
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

# Monitoring
SENTRY_DSN=your_sentry_dsn

# Secrets Management
BITWARDEN_EMAIL=your_bitwarden_email
BITWARDEN_PASSWORD=your_bitwarden_password
```

### Vercel Configuration
```json
{
  "functions": {
    "app/api/**/*.ts": {
      "runtime": "nodejs18.x"
    }
  },
  "rewrites": [
    { "source": "/crew", "destination": "http://localhost:8000/crew" }
  ]
}
```

## Development Best Practices

### Agent Development
- **State Management**: Use Letta for persistent agent memory
- **Error Handling**: Implement robust error handling for agent failures
- **Rate Limiting**: Respect API rate limits and implement backoff strategies
- **Testing**: Test agent workflows with mock data before production

### Frontend Development
- **Type Safety**: Use TypeScript strict mode and proper typing
- **Performance**: Implement lazy loading and code splitting
- **Accessibility**: Ensure all components are accessible
- **Responsive Design**: Test on all device sizes

### Backend Development
- **Async Operations**: Use async/await for all I/O operations
- **Security**: Validate all inputs and sanitize outputs
- **Monitoring**: Implement comprehensive logging and monitoring
- **Scalability**: Design for horizontal scaling

## Deployment Guidelines

### Frontend Deployment
- **Vercel**: Deploy to Vercel for PWA functionality
- **Environment**: Set up environment variables for production
- **Build**: Optimize build size and performance
- **Monitoring**: Enable Sentry error tracking

### Backend Deployment
- **Render**: Deploy to Render with Docker support
- **Environment**: Configure production environment variables
- **Scaling**: Set up auto-scaling for load handling
- **Monitoring**: Enable Sentry and performance monitoring

### Database Deployment
- **Supabase**: Set up production database with proper scaling
- **Backups**: Configure automated backups
- **Security**: Set up proper authentication and authorization
- **Monitoring**: Monitor database performance

## Troubleshooting

### Common Issues
- **CrewAI Proxy**: Ensure vercel.json rewrites are configured correctly
- **Image Upload**: Verify image URLs are properly formatted and accessible
- **Credit System**: Check Supabase user table structure and credit tracking
- **Scraping**: Verify 1s delays and proper User-Agent headers

### Debugging
- **Sentry**: Use Sentry for error tracking and debugging
- **Logging**: Implement comprehensive logging for debugging
- **Network**: Monitor API calls and network latency
- **Performance**: Profile application performance and identify bottlenecks

## Security Considerations

### Data Protection
- **Encryption**: Encrypt sensitive data at rest and in transit
- **Authentication**: Use Clerk for secure user authentication
- **Authorization**: Implement proper role-based access control
- **Input Validation**: Validate all user inputs to prevent injection attacks

### Compliance
- **GDPR**: Ensure compliance with data protection regulations
- **Privacy**: Implement proper data privacy measures
- **Audit Logging**: Maintain comprehensive audit logs
- **Rate Limiting**: Implement rate limiting to prevent abuse

## Performance Optimization

### Frontend Optimization
- **Code Splitting**: Implement lazy loading for components
- **Image Optimization**: Optimize images for web delivery
- **Caching**: Implement proper caching strategies
- **Bundle Size**: Monitor and optimize bundle size

### Backend Optimization
- **Database Optimization**: Optimize queries and indexing
- **Caching**: Implement caching for frequently accessed data
- **Connection Pooling**: Use proper connection pooling
- **Load Balancing**: Implement load balancing for scalability

## Monitoring & Analytics

### Application Monitoring
- **Sentry**: Error tracking and performance monitoring
- **Uptime Monitoring**: Monitor application uptime
- **Performance Metrics**: Track key performance indicators
- **User Behavior**: Monitor user interaction patterns

### Business Metrics
- **User Acquisition**: Track user acquisition and retention
- **Usage Analytics**: Monitor feature usage and engagement
- **Revenue Tracking**: Track revenue and conversion metrics
- **Performance Metrics**: Monitor system performance and reliability

## Future Enhancements

### Planned Features
- **Advanced Analytics**: Implement advanced analytics dashboard
- **Batch Processing**: Add batch processing capabilities
- **Marketplace Integration**: Integrate with additional marketplaces
- **Advanced AI**: Implement more sophisticated AI models

### Technical Improvements
- **Microservices**: Consider microservices architecture
- **Containerization**: Full containerization deployment
- **Database Optimization**: Advanced database optimization
- **Caching Strategies**: Implement advanced caching strategies

---

This document should be updated as the project evolves and new technologies or practices are adopted.