-- Create enum types
CREATE TYPE marketplace_type AS ENUM ('amazon', 'ebay', 'shopify', 'etsy', 'woocommerce', 'walmart', 'other');
CREATE TYPE product_condition AS ENUM ('new', 'used_like_new', 'used_good', 'used_fair', 'refurbished');
CREATE TYPE listing_status AS ENUM ('draft', 'active', 'paused', 'ended', 'error');

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    brand VARCHAR(100),
    category VARCHAR(100) NOT NULL,
    condition product_condition NOT NULL DEFAULT 'new',
    sku VARCHAR(100) UNIQUE,
    upc VARCHAR(20),
    ean VARCHAR(20),
    price DECIMAL(10, 2) NOT NULL,
    compare_at_price DECIMAL(10, 2),
    cost_per_item DECIMAL(10, 2),
    quantity INTEGER NOT NULL DEFAULT 0,
    weight DECIMAL(10, 2),
    weight_unit VARCHAR(10) DEFAULT 'g',
    length DECIMAL(10, 2),
    width DECIMAL(10, 2),
    height DECIMAL(10, 2),
    dimension_unit VARCHAR(10) DEFAULT 'cm',
    requires_shipping BOOLEAN DEFAULT TRUE,
    is_taxable BOOLEAN DEFAULT TRUE,
    is_digital BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    CONSTRAINT fk_user
        FOREIGN KEY(user_id) 
        REFERENCES auth.users(id)
        ON DELETE CASCADE
);

-- Product images table
CREATE TABLE product_images (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    alt_text VARCHAR(255),
    position INTEGER DEFAULT 0,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_product
        FOREIGN KEY(product_id) 
        REFERENCES products(id)
        ON DELETE CASCADE
);

-- Product variants
CREATE TABLE product_variants (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    sku VARCHAR(100) UNIQUE,
    option1_name VARCHAR(50),
    option1_value VARCHAR(100),
    option2_name VARCHAR(50),
    option2_value VARCHAR(100),
    option3_name VARCHAR(50),
    option3_value VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    compare_at_price DECIMAL(10, 2),
    cost_per_item DECIMAL(10, 2),
    quantity INTEGER NOT NULL DEFAULT 0,
    weight DECIMAL(10, 2),
    barcode VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    CONSTRAINT fk_product
        FOREIGN KEY(product_id) 
        REFERENCES products(id)
        ON DELETE CASCADE
);

-- Marketplace accounts
CREATE TABLE marketplace_accounts (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    marketplace marketplace_type NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    credentials JSONB NOT NULL,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    CONSTRAINT fk_user
        FOREIGN KEY(user_id) 
        REFERENCES auth.users(id)
        ON DELETE CASCADE,
    CONSTRAINT unique_user_marketplace
        UNIQUE(user_id, marketplace, name)
);

-- Product listings
CREATE TABLE product_listings (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    marketplace_account_id INTEGER NOT NULL,
    marketplace_listing_id VARCHAR(100),
    marketplace_listing_url TEXT,
    status listing_status NOT NULL DEFAULT 'draft',
    price DECIMAL(10, 2),
    quantity INTEGER,
    title VARCHAR(255),
    description TEXT,
    category_id VARCHAR(100),
    category_name VARCHAR(100),
    error_message TEXT,
    synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    CONSTRAINT fk_product
        FOREIGN KEY(product_id) 
        REFERENCES products(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_marketplace_account
        FOREIGN KEY(marketplace_account_id) 
        REFERENCES marketplace_accounts(id)
        ON DELETE CASCADE,
    CONSTRAINT unique_marketplace_listing
        UNIQUE(marketplace_account_id, marketplace_listing_id)
);

-- Create indexes for better query performance
CREATE INDEX idx_products_user_id ON products(user_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_product_images_product_id ON product_images(product_id);
CREATE INDEX idx_product_variants_product_id ON product_variants(product_id);
CREATE INDEX idx_product_variants_sku ON product_variants(sku);
CREATE INDEX idx_marketplace_accounts_user_id ON marketplace_accounts(user_id);
CREATE INDEX idx_product_listings_product_id ON product_listings(product_id);
CREATE INDEX idx_product_listings_marketplace_account_id ON product_listings(marketplace_account_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;   
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_products_updated_at
BEFORE UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_variants_updated_at
BEFORE UPDATE ON product_variants
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_marketplace_accounts_updated_at
BEFORE UPDATE ON marketplace_accounts
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_listings_updated_at
BEFORE UPDATE ON product_listings
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
