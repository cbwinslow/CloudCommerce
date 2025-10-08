-- Supabase Database Schema for CloudCommerce

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    credits INTEGER DEFAULT 5,
    sub_status TEXT DEFAULT 'free' CHECK (sub_status IN ('free', 'active', 'cancelled', 'past_due')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create RLS policy for users
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Submissions table
CREATE TABLE submissions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    summary TEXT NOT NULL,
    category TEXT,
    condition TEXT,
    analysis JSONB,
    listings JSONB,
    csv_data TEXT,
    image_urls TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create RLS policy for submissions
ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own submissions" ON submissions
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own submissions" ON submissions
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own submissions" ON submissions
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own submissions" ON submissions
    FOR DELETE USING (auth.uid() = user_id);

-- Storage buckets for images and exports
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('images', 'images', true, 5242880, ARRAY['image/jpeg', 'image/png', 'image/gif']),
       ('exports', 'exports', true, 10485760, ARRAY['text/csv', 'application/json']);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for updated_at
CREATE TRIGGER handle_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at();

CREATE TRIGGER handle_submissions_updated_at
    BEFORE UPDATE ON submissions
    FOR EACH ROW
    EXECUTE FUNCTION handle_updated_at();

-- Function to handle new user registration
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user registration
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- Function to add credits after payment
CREATE OR REPLACE FUNCTION add_credits(user_id UUID, amount INTEGER)
RETURNS INTEGER AS $$
DECLARE
    current_credits INTEGER;
BEGIN
    SELECT credits INTO current_credits FROM users WHERE id = user_id;
    UPDATE users SET credits = current_credits + amount WHERE id = user_id;
    RETURN current_credits + amount;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check user credits
CREATE OR REPLACE FUNCTION check_credits(user_id UUID)
RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT credits FROM users WHERE id = user_id);
END;
$$ LANGUAGE plpgsql;

-- Create indexes for better performance
CREATE INDEX idx_submissions_user_id ON submissions(user_id);
CREATE INDEX idx_submissions_created_at ON submissions(created_at);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_sub_status ON users(sub_status);

-- Create views for common queries
CREATE VIEW user_stats AS
SELECT 
    u.id,
    u.email,
    u.credits,
    u.sub_status,
    COUNT(s.id) as total_submissions,
    MAX(s.created_at) as last_submission
FROM users u
LEFT JOIN submissions s ON u.id = s.user_id
GROUP BY u.id, u.email, u.credits, u.sub_status;

-- Create function for arbitrage detection
CREATE OR REPLACE FUNCTION detect_arbitrage(item_price NUMERIC, category TEXT)
RETURNS TABLE(
    platform TEXT,
    title TEXT,
    price NUMERIC,
    arbitrage_percentage NUMERIC
) AS $$
BEGIN
    -- This is a simplified version - in production you'd want to scrape actual data
    RETURN QUERY 
    SELECT 
        'ebay' as platform,
        'Similar Item' as title,
        item_price * 0.8 as price,
        20 as arbitrage_percentage
    UNION ALL
    SELECT 
        'amazon' as platform,
        'Similar Item' as title,
        item_price * 0.9 as price,
        10 as arbitrage_percentage
    WHERE category = 'electronics';
END;
$$ LANGUAGE plpgsql;