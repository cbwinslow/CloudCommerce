import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

def run_migrations():
    """Run database migrations"""
    print("🔄 Running database migrations...")
    
    # Create subscription_plans table if it doesn't exist
    supabase.rpc('pg_catalog.pg_extension', 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"').execute()
    
    # Create subscription_plans table
    supabase.rpc('pg_catalog.pg_extension', '''
        CREATE TABLE IF NOT EXISTS public.subscription_plans (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            monthly_listings INTEGER NOT NULL,
            price_monthly DECIMAL(10, 2) NOT NULL,
            price_yearly DECIMAL(10, 2),
            stripe_price_id TEXT,
            features JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''').execute()
    
    # Add subscription columns to users table if they don't exist
    try:
        supabase.rpc('pg_catalog.pg_extension', '''
            ALTER TABLE public.users 
            ADD COLUMN IF NOT EXISTS subscription_plan_id TEXT REFERENCES public.subscription_plans(id) DEFAULT 'free',
            ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'active',
            ADD COLUMN IF NOT EXISTS subscription_start_date TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
            ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT,
            ADD COLUMN IF NOT EXISTS monthly_listings_used INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS last_billing_date TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS next_billing_date TIMESTAMPTZ
        ''').execute()
    except Exception as e:
        # Columns might already exist
        pass
    
    # Create subscription_usage table
    supabase.rpc('pg_catalog.pg_extension', '''
        CREATE TABLE IF NOT EXISTS public.subscription_usage (
            id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            user_id UUID REFERENCES auth.users(id) NOT NULL,
            month DATE NOT NULL,
            listings_used INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(user_id, month)
        )
    ''').execute()
    
    # Create subscription_history table
    supabase.rpc('pg_catalog.pg_extension', '''
        CREATE TABLE IF NOT EXISTS public.subscription_history (
            id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            user_id UUID REFERENCES auth.users(id) NOT NULL,
            plan_id TEXT REFERENCES public.subscription_plans(id) NOT NULL,
            action TEXT NOT NULL,
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''').execute()
    
    # Create billing_history table
    supabase.rpc('pg_catalog.pg_extension', '''
        CREATE TABLE IF NOT EXISTS public.billing_history (
            id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
            user_id UUID REFERENCES auth.users(id) NOT NULL,
            stripe_invoice_id TEXT,
            amount DECIMAL(10, 2) NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL,
            billing_period_start TIMESTAMPTZ,
            billing_period_end TIMESTAMPTZ,
            failure_reason TEXT,
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''').execute()
    
    # Create indexes
    supabase.rpc('pg_catalog.pg_extension', '''
        CREATE INDEX IF NOT EXISTS idx_subscription_usage_user_month 
        ON public.subscription_usage(user_id, month)
    ''').execute()
    
    supabase.rpc('pg_catalog.pg_extension', '''
        CREATE INDEX IF NOT EXISTS idx_users_subscription_status 
        ON public.users(subscription_status)
    ''').execute()
    
    print("✅ Database migrations completed successfully!")

def seed_plans():
    """Seed subscription plans"""
    print("\n🌱 Seeding subscription plans...")
    
    plans = [
        {
            "id": "free",
            "name": "Free",
            "description": "Basic listing features",
            "monthly_listings": 5,
            "price_monthly": 0,
            "features": ["Basic AI analysis", "Single marketplace export"]
        },
        {
            "id": "pro",
            "name": "Pro",
            "description": "For power sellers",
            "monthly_listings": 100,
            "price_monthly": 19.99,
            "features": ["Advanced AI features", "Multiple marketplace exports", "Basic analytics"]
        },
        {
            "id": "unlimited",
            "name": "Unlimited",
            "description": "For high-volume sellers",
            "monthly_listings": 0,  # 0 means unlimited
            "price_monthly": 99.99,
            "features": ["Unlimited listings", "Priority support", "Advanced analytics"]
        }
    ]
    
    for plan in plans:
        # Upsert plan
        supabase.table('subscription_plans').upsert({
            'id': plan['id'],
            'name': plan['name'],
            'description': plan['description'],
            'monthly_listings': plan['monthly_listings'],
            'price_monthly': plan['price_monthly'],
            'features': plan['features']
        }, on_conflict='id').execute()
    
    print("✅ Subscription plans seeded successfully!")

if __name__ == "__main__":
    print("🚀 Setting up database...")
    try:
        run_migrations()
        seed_plans()
        print("\n✨ Database setup completed successfully!")
    except Exception as e:
        print(f"\n❌ Error setting up database: {str(e)}")
