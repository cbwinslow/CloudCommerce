-- Create subscription plans table
CREATE TABLE IF NOT EXISTS subscription_plans (
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
);

-- Add subscription fields to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS subscription_plan_id TEXT REFERENCES subscription_plans(id) DEFAULT 'free',
ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'active',
ADD COLUMN IF NOT EXISTS subscription_start_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
ADD COLUMN IF NOT EXISTS monthly_listings_used INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_billing_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS next_billing_date TIMESTAMPTZ;

-- Create usage history table
CREATE TABLE IF NOT EXISTS subscription_usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    month DATE NOT NULL,
    listings_used INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, month)
);

-- Create subscription history table
CREATE TABLE IF NOT EXISTS subscription_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) NOT NULL,
    plan_id TEXT REFERENCES subscription_plans(id) NOT NULL,
    action TEXT NOT NULL, -- 'created', 'updated', 'cancelled', 'renewed'
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_subscription_usage_user_month ON subscription_usage(user_id, month);
CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users(subscription_status);

-- Insert default subscription plans
INSERT INTO subscription_plans (id, name, description, monthly_listings, price_monthly, features)
VALUES 
    ('free', 'Free', 'Basic listing features', 5, 0.00, '["Basic AI analysis", "Single marketplace export"]'::jsonb),
    ('pro', 'Pro', 'For power sellers', 100, 19.99, '["Advanced AI features", "Multiple marketplace exports", "Basic analytics"]'::jsonb),
    ('unlimited', 'Unlimited', 'For high-volume sellers', 0, 99.99, '["Unlimited listings", "Priority support", "Advanced analytics"]'::jsonb)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    monthly_listings = EXCLUDED.monthly_listings,
    price_monthly = EXCLUDED.price_monthly,
    features = EXCLUDED.features,
    updated_at = NOW();

-- Create function to track monthly usage
CREATE OR REPLACE FUNCTION track_monthly_usage()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO subscription_usage (user_id, month, listings_used, created_at, updated_at)
    VALUES (
        NEW.user_id,
        DATE_TRUNC('month', NOW()),
        1,
        NOW(),
        NOW()
    )
    ON CONFLICT (user_id, month) 
    DO UPDATE SET 
        listings_used = subscription_usage.listings_used + 1,
        updated_at = NOW()
    WHERE subscription_usage.user_id = NEW.user_id 
    AND subscription_usage.month = DATE_TRUNC('month', NOW());
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new listings
CREATE OR REPLACE TRIGGER track_listing_created
AFTER INSERT ON listings
FOR EACH ROW
EXECUTE FUNCTION track_monthly_usage();

-- Create function to check subscription limits
CREATE OR REPLACE FUNCTION check_subscription_limit()
RETURNS TRIGGER AS $$
DECLARE
    current_usage INTEGER;
    max_listings INTEGER;
BEGIN
    -- Get current month's usage
    SELECT COALESCE(SUM(listings_used), 0) INTO current_usage
    FROM subscription_usage
    WHERE user_id = NEW.user_id
    AND month = DATE_TRUNC('month', NOW());
    
    -- Get user's subscription limit
    SELECT monthly_listings INTO max_listings
    FROM subscription_plans sp
    JOIN users u ON sp.id = u.subscription_plan_id
    WHERE u.id = NEW.user_id;
    
    -- Check if user has reached their limit
    IF current_usage >= max_listings AND max_listings > 0 THEN
        RAISE EXCEPTION 'Monthly listing limit reached for this subscription plan';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger to enforce subscription limits
CREATE OR REPLACE TRIGGER enforce_subscription_limit
BEFORE INSERT ON listings
FOR EACH ROW
EXECUTE FUNCTION check_subscription_limit();
