# AI Item Listing Generator - CloudCommerce

A comprehensive AI-powered platform that transforms item images into marketplace-ready listings across multiple e-commerce platforms. Built with Next.js, FastAPI, and cutting-edge AI technologies.

## 🚀 Project Overview

CloudCommerce is an MVP-ready application that enables users to:
- Upload item images and descriptions
- AI-analyze items using computer vision and NLP
- Generate optimized listings for eBay, Amazon, and Facebook Marketplace
- Export listings as CSV for bulk upload
- Discover arbitrage opportunities through market analysis
- Access features via web, mobile (Expo), and API endpoints

## 🏗️ Architecture

### Frontend (Next.js PWA)
- **Framework**: Next.js 14 with App Router
- **UI**: Shadcn components with Tailwind CSS
- **Authentication**: Clerk for user management
- **State Management**: React hooks with server actions
- **Mobile**: Expo app for iOS/Android

### Backend (FastAPI + Python)
- **Framework**: FastAPI with async support
- **AI Integration**: OpenRouter API for LLM models
- **Agents**: CrewAI for multi-agent workflows
- **Memory**: Letta for stateful agent memory
- **Scraping**: Playwright for ethical web scraping
- **Monitoring**: Sentry for error tracking

### Database & Storage
- **Primary**: Supabase (PostgreSQL) for data storage
- **Storage**: Supabase storage for image uploads
- **Cache**: Built-in caching strategies
- **Backup**: Automated backup procedures

### Infrastructure
- **Frontend Hosting**: Vercel (PWA enabled)
- **Backend Hosting**: Render (Docker support)
- **Secrets**: Bitwarden for secure secret management
- **Monitoring**: Sentry for application monitoring

## 📁 Project Structure

```
CloudCommerce/
├── app/                          # Next.js App Router
│   ├── api/                     # API routes
│   │   ├── submit/             # Main submission endpoint
│   │   └── create-checkout-session/ # Stripe integration
│   ├── sign-in/                 # Clerk authentication pages
│   ├── sign-up/                 # Clerk authentication pages
│   ├── layout.tsx              # Root layout
│   └── page.tsx                # Home page
├── components/                  # React components
│   └── SubmissionForm.tsx      # Main submission form
├── lib/                        # Shared libraries
│   ├── crew.ts                 # CrewAI integration
│   ├── openrouter.ts           # OpenRouter API client
│   └── scraper.ts              # Web scraping utilities
├── backend/                    # Python FastAPI backend
│   ├── main.py                 # Main FastAPI application
│   ├── requirements.txt        # Python dependencies
│   └── core/                   # Core business logic
│       ├── agents/             # AI agent implementations
│       │   ├── submit_agent.py # Item analysis agent
│       │   └── arbitrage_crew.py # Arbitrage detection crew
│       └── auth/               # Authentication logic
├── mobile/                     # Expo mobile app
│   ├── App.tsx                 # Main mobile component
│   └── package.json            # Mobile dependencies
├── frontend/                   # Alternative frontend (legacy)
├── docs/                       # Documentation
├── templates/                  # Listing templates
└── public/                     # Static assets
```

## 🛠️ Key Features

### Core Functionality
- **Image Upload**: Drag-and-drop interface with preview
- **AI Analysis**: Computer vision + NLP for item understanding
- **Multi-Platform Listings**: eBay, Amazon, Facebook Marketplace
- **CSV Export**: Bulk upload ready format
- **Arbitrage Detection**: Market analysis for profit opportunities
- **User Management**: Authentication with Clerk

### Technical Features
- **Progressive Web App**: Offline support and mobile experience
- **Real-time Processing**: Live status updates during analysis
- **Responsive Design**: Works on all device sizes
- **Error Handling**: Comprehensive error management
- **Performance Optimized**: Code splitting and lazy loading
- **Security First**: Input validation, CSRF protection, secure headers

### AI Capabilities
- **Vision Analysis**: LLaVA-13b for image understanding
- **Text Generation**: Llama 3.1 for listing creation
- **Market Research**: Automated price and competitor analysis
- **Arbitrage Detection**: Identify underpriced items
- **Stateful Memory**: Letta for context-aware conversations

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- Python 3.8+
- pnpm package manager
- Expo CLI (for mobile development)

### Environment Setup

1. **Clone and Install Dependencies**
```bash
# Install frontend dependencies
pnpm install

# Setup Python environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup mobile dependencies
cd mobile
npm install
```

2. **Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys:
# - STRIPE_SECRET_KEY
# - STRIPE_WEBHOOK_SECRET
# - SUPABASE_URL
# - SUPABASE_ANON_KEY
# - CLERK_PUBLISHABLE_KEY
# - CLERK_SECRET_KEY
# - OPENROUTER_API_KEY
# - LETTA_API_KEY
# - SENTRY_DSN
# - BITWARDEN_EMAIL
# - BITWARDEN_PASSWORD
```

3. **Database Setup**
```bash
# Create Supabase project and set up tables:
# - users (credits, sub_status)
# - submissions (analysis, listings, metadata)
# - Set up storage buckets for images
```

### Development Commands

#### Frontend Development
```bash
# Start development server
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start

# Lint code
pnpm lint -- --file src/app/page.tsx
```

#### Backend Development
```bash
# Start backend server
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

#### Mobile Development
```bash
# Start Expo development server
cd mobile
npx expo start

# Build for production
npx expo build:ios
npx expo build:android
```

#### Testing
```bash
# E2E testing with Playwright
npx playwright test

# Add tests/ directory first if needed
```

## 🎯 API Endpoints

### Core Submission API
- **POST** `/api/submit` - Main item analysis endpoint
- **POST** `/api/create-checkout-session` - Stripe payment processing
- **GET** `/api/submissions/[id]` - Retrieve submission history

### Backend Python APIs
- **POST** `/submit` - FastAPI submission endpoint
- **POST** `/crew` - CrewAI workflow execution
- **POST** `/rotate-secrets` - Secret rotation endpoint

## 🔧 Configuration

### Environment Variables
```bash
# Authentication
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_SECRET_KEY=your_clerk_secret_key

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Payment
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

# AI Services
OPENROUTER_API_KEY=your_openrouter_api_key
LETTA_API_KEY=your_letta_api_key

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

## 🚀 Deployment

### Staging Deployment
1. **Frontend**: Deploy to Vercel staging
2. **Backend**: Deploy to Render staging
3. **Database**: Set up Supabase staging environment
4. **Environment**: Configure staging environment variables
5. **Testing**: Run end-to-end tests in staging

### Production Deployment
1. **Upgrade Plans**: Vercel Pro ($20/mo), Render Pro ($7/mo)
2. **Frontend**: Deploy to Vercel production
3. **Backend**: Deploy to Render production
4. **Environment**: Update production URLs
5. **Monitoring**: Enable production monitoring
6. **Mobile**: Publish to app stores

## 📊 Monetization

### Credit System
- **Free Tier**: Limited submissions per month
- **Paid Plans**: Credit-based pricing
- **Subscriptions**: Unlimited plans for power users
- **Enterprise**: Custom pricing for businesses

### Payment Integration
- **Stripe**: Payment processing and subscriptions
- **Webhooks**: Real-time payment notifications
- **Prorated Billing**: Fair pricing for plan changes
- **Usage Tracking**: Monitor API usage and billing

## 🔒 Security Features

### Authentication & Authorization
- **Clerk**: Secure user authentication
- **JWT Tokens**: Stateless session management
- **Role-based Access**: Different user permissions
- **Social Login**: Google, GitHub integration

### Data Protection
- **Input Validation**: Zod schema validation
- **CSRF Protection**: Cross-site request forgery prevention
- **Secure Headers**: HSTS, CSP, security headers
- **Data Encryption**: Sensitive data encryption

### Compliance
- **GDPR**: Data privacy compliance
- **Backup**: Automated data backup procedures
- **Audit Logging**: Comprehensive audit trails
- **Rate Limiting**: API rate limiting and quotas

## 📈 Monitoring & Analytics

### Application Monitoring
- **Sentry**: Error tracking and performance monitoring
- **Performance**: Application performance metrics
- **Uptime**: Service availability monitoring
- **Custom Dashboards**: Real-time metrics dashboard

### Business Analytics
- **User Metrics**: User acquisition and retention
- **Usage Analytics**: Feature usage and engagement
- **Revenue Tracking**: Monetization metrics
- **Conversion Tracking**: Funnel analysis

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request
6. **Review** and merge

### Code Standards
- **TypeScript**: Strict mode enabled
- **Python**: PEP 8 compliance
- **Linting**: ESLint and Pylint
- **Testing**: E2E testing with Playwright
- **Documentation**: Comprehensive documentation

## 📚 Documentation

### API Documentation
- **OpenAPI/Swagger**: Auto-generated API docs
- **Endpoints**: Detailed endpoint documentation
- **Authentication**: Auth flow documentation
- **Examples**: Request/response examples

### User Guides
- **Getting Started**: Quick start guide
- **Feature Documentation**: Detailed feature guides
- **Troubleshooting**: Common issues and solutions
- **Best Practices**: Usage recommendations

## 🔄 Maintenance

### Regular Tasks
- **Dependency Updates**: Keep packages updated
- **Security Patches**: Apply security updates
- **Performance Monitoring**: Monitor application performance
- **User Feedback**: Collect and implement user feedback

### Backup & Recovery
- **Database Backups**: Automated database backups
- **File Storage**: Storage backup procedures
- **Disaster Recovery**: Recovery procedures
- **Testing**: Regular backup testing

## 🎯 Roadmap

### Phase 1: Core Features ✅
- [x] User authentication and management
- [x] Image upload and processing
- [x] AI analysis and listing generation
- [x] Multi-platform export
- [x] Mobile app support

### Phase 2: Enhanced Features 🚧
- [ ] Advanced analytics dashboard
- [ ] Batch processing capabilities
- [ ] Integration with more marketplaces
- [ ] Advanced arbitrage detection
- [ ] Custom listing templates

### Phase 3: Enterprise Features 📋
- [ ] API rate limiting and quotas
- [ ] Advanced admin dashboard
- [ ] White-label solutions
- [ ] Multi-tenant architecture
- [ ] Advanced reporting

### Phase 4: Future Innovations 🔮
- [ ] Real-time market data integration
- [ ] Predictive pricing algorithms
- [ ] AI-powered image enhancement
- [ ] Voice-to-listing capabilities
- [ ] Blockchain-based verification

## 📞 Support

### Technical Support
- **Documentation**: Comprehensive guides and tutorials
- **Issues**: GitHub issue tracking
- **Community**: Community forums and discussions
- **Email**: Direct support for enterprise customers

### Business Support
- **Sales**: Sales team for enterprise inquiries
- **Partnership**: Partnership program information
- **Feedback**: User feedback collection and analysis
- **Updates**: Product updates and announcements

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Clerk**: Authentication and user management
- **Supabase**: Database and storage infrastructure
- **OpenRouter**: AI model access
- **Stripe**: Payment processing
- **Vercel**: Frontend hosting
- **Render**: Backend hosting
- **Sentry**: Error monitoring and tracking

---

**Built with ❤️ by the CloudCommerce team**