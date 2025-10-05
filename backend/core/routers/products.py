from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session

from core.database.database import get_db
from core.repositories.product import ProductRepository
from core.models.product import (
    Product, ProductCreate, ProductUpdate,
    ProductImage as ProductImageModel,
    ProductVariant as ProductVariantModel,
    MarketplaceAccount, MarketplaceAccountCreate, MarketplaceAccountUpdate,
    ProductListing, ProductListingCreate, ProductListingUpdate,
    MarketplaceType, ListingStatus
)
from core.auth import get_current_user

router = APIRouter(prefix="/api/products", tags=["products"])

# Helper function to get current user's ID
def get_current_user_id(current_user: dict = Depends(get_current_user)) -> str:
    return str(current_user["id"])

# Products Endpoints
@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new product
    """
    repo = ProductRepository(db)
    return repo.create_product(user_id, product)

@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get a product by ID
    """
    repo = ProductRepository(db)
    product = repo.get_product(user_id, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/", response_model=List[Product])
def list_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    List all products with optional filtering
    """
    repo = ProductRepository(db)
    return repo.list_products(
        user_id,
        skip=skip,
        limit=limit,
        search=search,
        category=category,
        is_active=is_active
    )

@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    product: ProductUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update a product
    """
    repo = ProductRepository(db)
    updated_product = repo.update_product(user_id, product_id, product)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Delete a product (soft delete)
    """
    repo = ProductRepository(db)
    success = repo.delete_product(user_id, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return None

# Marketplace Accounts Endpoints
@router.post("/marketplace/accounts/", response_model=MarketplaceAccount, status_code=status.HTTP_201_CREATED)
def create_marketplace_account(
    account: MarketplaceAccountCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new marketplace account
    """
    repo = ProductRepository(db)
    return repo.create_marketplace_account(user_id, account)

@router.get("/marketplace/accounts/{account_id}", response_model=MarketplaceAccount)
def get_marketplace_account(
    account_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get a marketplace account by ID
    """
    repo = ProductRepository(db)
    account = repo.get_marketplace_account(user_id, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Marketplace account not found")
    return account

@router.get("/marketplace/accounts/", response_model=List[MarketplaceAccount])
def list_marketplace_accounts(
    marketplace: Optional[MarketplaceType] = None,
    is_active: Optional[bool] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    List all marketplace accounts with optional filtering
    """
    repo = ProductRepository(db)
    return repo.list_marketplace_accounts(user_id, marketplace, is_active)

@router.put("/marketplace/accounts/{account_id}", response_model=MarketplaceAccount)
def update_marketplace_account(
    account_id: int,
    account: MarketplaceAccountUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update a marketplace account
    """
    repo = ProductRepository(db)
    updated_account = repo.update_marketplace_account(user_id, account_id, account)
    if not updated_account:
        raise HTTPException(status_code=404, detail="Marketplace account not found")
    return updated_account

@router.delete("/marketplace/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_marketplace_account(
    account_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Delete a marketplace account
    """
    repo = ProductRepository(db)
    success = repo.delete_marketplace_account(user_id, account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Marketplace account not found")
    return None

# Product Listings Endpoints
@router.post("/listings/", response_model=ProductListing, status_code=status.HTTP_201_CREATED)
def create_product_listing(
    listing: ProductListingCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new product listing
    """
    repo = ProductRepository(db)
    created_listing = repo.create_product_listing(user_id, listing)
    if not created_listing:
        raise HTTPException(status_code=400, detail="Failed to create listing. Check if product and marketplace account exist and belong to you.")
    return created_listing

@router.get("/listings/", response_model=List[ProductListing])
def list_product_listings(
    product_id: Optional[int] = None,
    marketplace_account_id: Optional[int] = None,
    status: Optional[ListingStatus] = None,
    skip: int = 0,
    limit: int = 100,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    List all product listings with optional filtering
    """
    repo = ProductRepository(db)
    return repo.list_product_listings(
        user_id,
        product_id=product_id,
        marketplace_account_id=marketplace_account_id,
        status=status,
        skip=skip,
        limit=limit
    )

@router.put("/listings/{listing_id}", response_model=ProductListing)
def update_product_listing(
    listing_id: int,
    listing: ProductListingUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update a product listing
    """
    repo = ProductRepository(db)
    updated_listing = repo.update_product_listing(user_id, listing_id, listing)
    if not updated_listing:
        raise HTTPException(status_code=404, detail="Product listing not found")
    return updated_listing

@router.post("/{product_id}/sync/{marketplace_account_id}", response_model=ProductListing)
def sync_product_to_marketplace(
    product_id: int,
    marketplace_account_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Sync a product to a marketplace
    """
    repo = ProductRepository(db)
    listing = repo.sync_product_to_marketplace(user_id, product_id, marketplace_account_id)
    if not listing:
        raise HTTPException(status_code=400, detail="Failed to sync product to marketplace")
    return listing

# Marketplace Integration Endpoints
@router.get("/marketplace/categories/{marketplace}")
def get_marketplace_categories(
    marketplace: MarketplaceType,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get available categories for a marketplace
    """
    # TODO: Implement actual marketplace API integration
    # This is a placeholder response
    return {
        "marketplace": marketplace,
        "categories": [
            {"id": "1", "name": "Electronics"},
            {"id": "2", "name": "Clothing"},
            {"id": "3", "name": "Home & Garden"},
            # Add more categories as needed
        ]
    }

@router.get("/marketplace/attributes/{marketplace}/{category_id}")
def get_marketplace_attributes(
    marketplace: MarketplaceType,
    category_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get required attributes for a marketplace category
    """
    # TODO: Implement actual marketplace API integration
    # This is a placeholder response
    return {
        "marketplace": marketplace,
        "category_id": category_id,
        "attributes": [
            {
                "name": "Brand",
                "type": "TEXT",
                "required": True,
                "description": "The brand of the product"
            },
            {
                "name": "Model",
                "type": "TEXT",
                "required": True,
                "description": "The model number or name"
            },
            # Add more attributes as needed
        ]
    }
