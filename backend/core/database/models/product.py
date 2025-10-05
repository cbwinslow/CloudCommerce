from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, ForeignKey, Enum as SQLEnum, JSON, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from datetime import datetime

from core.database.base import Base

class ProductCondition(str, enum.Enum):
    NEW = "new"
    USED_LIKE_NEW = "used_like_new"
    USED_GOOD = "used_good"
    USED_FAIR = "used_fair"
    REFURBISHED = "refurbished"

class ListingStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    ERROR = "error"

class MarketplaceType(str, enum.Enum):
    AMAZON = "amazon"
    EBAY = "ebay"
    SHOPIFY = "shopify"
    ETSY = "etsy"
    WOOCOMMERCE = "woocommerce"
    WALMART = "walmart"
    OTHER = "other"

class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    alt_text = Column(String(255))
    position = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="images")

class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint('product_id', 'option1_value', 'option2_value', 'option3_value', 
                        name='uix_product_variant_options'),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    sku = Column(String(100), unique=True, index=True)
    option1_name = Column(String(50))
    option1_value = Column(String(100))
    option2_name = Column(String(50))
    option2_value = Column(String(100))
    option3_name = Column(String(50))
    option3_value = Column(String(100))
    price = Column(Numeric(10, 2), nullable=False)
    compare_at_price = Column(Numeric(10, 2))
    cost_per_item = Column(Numeric(10, 2))
    quantity = Column(Integer, nullable=False, default=0)
    weight = Column(Numeric(10, 2))
    barcode = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata = Column(JSON, default=dict)

    product = relationship("Product", back_populates="variants")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # References auth.users.id
    title = Column(String(255), nullable=False)
    description = Column(Text)
    brand = Column(String(100))
    category = Column(String(100), nullable=False)
    condition = Column(SQLEnum(ProductCondition), nullable=False, default=ProductCondition.NEW)
    sku = Column(String(100), unique=True, index=True)
    upc = Column(String(20))
    ean = Column(String(20))
    price = Column(Numeric(10, 2), nullable=False)
    compare_at_price = Column(Numeric(10, 2))
    cost_per_item = Column(Numeric(10, 2))
    quantity = Column(Integer, nullable=False, default=0)
    weight = Column(Numeric(10, 2))
    weight_unit = Column(String(10), default="g")
    length = Column(Numeric(10, 2))
    width = Column(Numeric(10, 2))
    height = Column(Numeric(10, 2))
    dimension_unit = Column(String(10), default="cm")
    requires_shipping = Column(Boolean, default=True)
    is_taxable = Column(Boolean, default=True)
    is_digital = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    metadata = Column(JSON, default=dict)

    # Relationships
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    listings = relationship("ProductListing", back_populates="product", cascade="all, delete-orphan")

class MarketplaceAccount(Base):
    __tablename__ = "marketplace_accounts"
    __table_args__ = (
        UniqueConstraint('user_id', 'marketplace', 'name', name='uix_user_marketplace_name'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # References auth.users.id
    marketplace = Column(SQLEnum(MarketplaceType), nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    credentials = Column(JSON, nullable=False)
    last_sync_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata = Column(JSON, default=dict)

    listings = relationship("ProductListing", back_populates="marketplace_account")

class ProductListing(Base):
    __tablename__ = "product_listings"
    __table_args__ = (
        UniqueConstraint('marketplace_account_id', 'marketplace_listing_id', 
                        name='uix_marketplace_listing'),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    marketplace_account_id = Column(Integer, ForeignKey("marketplace_accounts.id", ondelete="CASCADE"), nullable=False)
    marketplace_listing_id = Column(String(100))
    marketplace_listing_url = Column(Text)
    status = Column(SQLEnum(ListingStatus), nullable=False, default=ListingStatus.DRAFT)
    price = Column(Numeric(10, 2))
    quantity = Column(Integer)
    title = Column(String(255))
    description = Column(Text)
    category_id = Column(String(100))
    category_name = Column(String(100))
    error_message = Column(Text)
    synced_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    metadata = Column(JSON, default=dict)

    # Relationships
    product = relationship("Product", back_populates="listings")
    marketplace_account = relationship("MarketplaceAccount", back_populates="listings")
