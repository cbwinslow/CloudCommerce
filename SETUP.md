# CloudCommerce - AI Item Listing Generator

A full-stack AI-powered application that analyzes item images and generates optimized listings for multiple e-commerce platforms.

## 🚀 Features

- **AI Analysis**: Computer vision analysis of item images using OpenRouter LLaVA
- **Multi-Platform Listings**: Generate optimized listings for eBay, Amazon, and Facebook Marketplace
- **Price Recommendations**: AI-powered pricing suggestions based on market analysis
- **Arbitrage Detection**: Identify potential profit opportunities
- **Mobile App**: React Native Expo app for on-the-go submissions
- **User Management**: Authentication with Clerk and credit-based system
- **Database**: Supabase for data storage and real-time updates
- **Payment Processing**: Stripe integration for credit purchases
- **Scraping**: Ethical web scraping for market research

## 📁 Project Structure

```
CloudCommerce/
├── app/                    # Next.js frontend
│   ├── api/               # API routes
│   ├── components/        # React components
│   └── page.tsx           # Main page
├── backend/               # FastAPI backend
│   ├── main.py           # FastAPI application
│   ├── requirements.txt  # Python dependencies
│   └── core/             # Core business logic
├── mobile/               # React Native Expo app
├── lib/                  # Shared utilities
├── supabase/             # Database schema
└── docs/                 # Documentation
```

## 🛠️ Setup Instructions

### Prerequisites

- Node.js 18+
- pnpm (or npm/yarn)
- Python 3.10+
- Expo CLI
- Supabase account
- OpenRouter API key
- Stripe account
- Clerk account

### 1. Clone and Setup

```bash
git clone <repository-url>
cd CloudCommerce
cp .env.example .env.local
```

### 2. Environment Configuration

Edit `.env.local` with your API keys:

```env
# Frontend
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=your_stripe_key
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_key

# Backend
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
STRIPE_SECRET_KEY=your_stripe_secret_key
CLERK_SECRET_KEY=your_clerk_secret_key
OPENROUTER_API_KEY=your_openrouter_key
```

### 3. Database Setup

1. Create a Supabase project
2. Run the schema from `supabase/schema.sql`
3. Set up storage buckets for images and exports

### 4. Frontend Setup

```bash
cd app
pnpm install
pnpm dev
```

### 5. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 6. Mobile App Setup

```bash
cd mobile
npm install
npx expo start
```

## 📱 Mobile App

The mobile app allows users to:
- Take photos of items
- Submit for AI analysis
- View results and download CSV files
- Manage credits

### Mobile Development

```bash
cd mobile
npx expo start          # Start development server
npx expo start --ios    # Start for iOS
npx expo start --android # Start for Android
```

## 🔧 API Endpoints

### Frontend API Routes

- `POST /api/submit` - Submit item for analysis
- `POST /api/create-checkout-session` - Create Stripe checkout session

### Backend API Routes

- `POST /submit` - Process item submission
- `POST /crew` - CrewAI integration
- `POST /rotate-secrets` - Rotate API keys

## 🧪 Testing

### Frontend Testing

```bash
cd app
pnpm lint               # Run ESLint
npx playwright test     # E2E testing
```

### Backend Testing

```bash
cd backend
pytest -v              # Run Python tests
```

## 🚀 Deployment

### Frontend (Vercel)

1. Connect repository to Vercel
2. Set environment variables
3. Deploy

### Backend (Render)

1. Create Dockerfile
2. Connect repository to Render
3. Set environment variables
4. Deploy

### Mobile App (Expo)

1. Build for production
2. Submit to app stores

## 📊 Database Schema

### Users Table
- `id` - UUID (Primary Key)
- `email` - User email
- `credits` - Available credits
- `sub_status` - Subscription status
- `created_at` - Creation timestamp

### Submissions Table
- `id` - UUID (Primary Key)
- `user_id` - Foreign key to users
- `summary` - Item description
- `analysis` - AI analysis results (JSONB)
- `listings` - Generated listings (JSONB)
- `csv_data` - CSV export data
- `image_urls` - Uploaded image URLs

## 🔐 Authentication

- **Clerk** handles user authentication
- **Supabase** manages user data and credits
- **Stripe** handles payments and subscriptions

## 💳 Monetization

- Credit-based system for API usage
- Stripe integration for payments
- Subscription plans available

## 🎨 UI/UX

- **Frontend**: Next.js with Tailwind CSS and Shadcn UI
- **Mobile**: React Native with Expo
- **Dark Mode**: Supported across all platforms

## 📈 Analytics

- **Google Analytics** for user tracking
- **Sentry** for error tracking
- **Supabase** for database analytics

## 🔧 Configuration

### Vercel Configuration

```json
{
  "rewrites": [
    { "source": "/crew", "destination": "http://localhost:8000/crew" }
  ]
}
```

### Supabase Configuration

- Enable RLS (Row Level Security)
- Set up storage buckets
- Create database functions

## 🚨 Security

- API keys stored securely
- Row Level Security on database
- Input validation and sanitization
- Rate limiting on API endpoints

## 🔄 Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key |
| `STRIPE_SECRET_KEY` | Stripe secret key |
| `CLERK_SECRET_KEY` | Clerk secret key |
| `OPENROUTER_API_KEY` | OpenRouter API key |

## 📚 API Documentation

### Submit Item

```typescript
const response = await fetch('/api/submit', {
  method: 'POST',
  body: formData,
});
```

### Generate Listings

```python
# Backend
@app.post("/submit")
async def submit_item(data: dict):
    # Process images and generate listings
    return {"analysis": "...", "listings": {...}}
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection**: Verify Supabase credentials
2. **API Keys**: Check all environment variables
3. **Image Upload**: Verify storage bucket permissions
4. **Mobile Build**: Ensure Expo dependencies are installed

### Debug Mode

Set `NODE_ENV=development` for detailed logging.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- OpenRouter for AI models
- Supabase for database and storage
- Stripe for payment processing
- Clerk for authentication
- Expo for mobile development

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting guide