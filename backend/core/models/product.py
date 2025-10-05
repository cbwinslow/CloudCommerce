from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator
from enum import Enum

class ProductCondition(str, Enum):
    NEW = "new"
    USED_LIKE_NEW = "used_like_new"
    USED_GOOD = "used_good"
    USED_FAIR = "used_fair"
    REFURBISHED = "refurbished"

class ListingStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    ERROR = "error"

class MarketplaceType(str, Enum):
    AMAZON = "amazon"
    EBAY = "ebay"
    SHOPIFY = "shopify"
    ETSY = "etsy"
    WOOCOMMERCE = "woocommerce"
    WALMART = "walmart"
    OTHER = "other"

class ProductImageBase(BaseModel):
    url: str
    alt_text: Optional[str] = None
    position: int = 0
    is_primary: bool = False

class ProductImageCreate(ProductImageBase):
    pass

class ProductImageUpdate(ProductImageBase):
    id: Optional[int] = None

class ProductImage(ProductImageBase):
    id: int
    product_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class ProductVariantBase(BaseModel):
    sku: Optional[str] = None
    option1_name: Optional[str] = None
    option1_value: Optional[str] = None
    option2_name: Optional[str] = None
    option2_value: Optional[str] = None
    option3_name: Optional[str] = None
    option3_value: Optional[str] = None
    price: float
    compare_at_price: Optional[float] = None
    cost_per_item: Optional[float] = None
    quantity: int = 0
    weight: Optional[float] = None
    barcode: Optional[str] = None
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None

class ProductVariantCreate(ProductVariantBase):
    pass

class ProductVariantUpdate(ProductVariantBase):
    id: Optional[int] = None

class ProductVariant(ProductVariantBase):
    id: int
    product_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    brand: Optional[str] = None
    category: str
    condition: ProductCondition = ProductCondition.NEW
    sku: Optional[str] = None
    upc: Optional[str] = None
    ean: Optional[str] = None
    price: float
    compare_at_price: Optional[float] = None
    cost_per_item: Optional[float] = None
    quantity: int = 0
    weight: Optional[float] = None
    weight_unit: str = "g"
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    dimension_unit: str = "cm"
    requires_shipping: bool = True
    is_taxable: bool = True
    is_digital: bool = False
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None
    images: Optional[List[ProductImageBase]] = None
    variants: Optional[List[ProductVariantBase]] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    id: Optional[int] = None

class Product(ProductBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    images: List[ProductImage] = []
    variants: List[ProductVariant] = []

    class Config:
        orm_mode = True

class MarketplaceAccountBase(BaseModel):
    marketplace: MarketplaceType
    name: str
    is_active: bool = True
    credentials: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class MarketplaceAccountCreate(MarketplaceAccountBase):
    pass

class MarketplaceAccountUpdate(MarketplaceAccountBase):
    id: Optional[int] = None

class MarketplaceAccount(MarketplaceAccountBase):
    id: int
    user_id: str
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ProductListingBase(BaseModel):
    marketplace_account_id: int
    marketplace_listing_id: Optional[str] = None
    marketplace_listing_url: Optional[str] = None
    status: ListingStatus = ListingStatus.DRAFT
    price: Optional[float] = None
    quantity: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ProductListingCreate(ProductListingBase):
    product_id: int

class ProductListingUpdate(ProductListingBase):
    id: Optional[int] = None

class ProductListing(ProductListingBase):
    id: int
    product_id: int
    synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    marketplace_account: Optional[MarketplaceAccount] = None

    class Config:
        orm_mode = True
