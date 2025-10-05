from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from core.database.models.product import (
    Product as DBProduct,
    ProductImage as DBProductImage,
    ProductVariant as DBProductVariant,
    MarketplaceAccount as DBMarketplaceAccount,
    ProductListing as DBProductListing,
    MarketplaceType,
    ListingStatus
)
from core.models.product import (
    ProductCreate, ProductUpdate, Product,
    ProductImage as ProductImageModel,
    ProductVariant as ProductVariantModel,
    MarketplaceAccountCreate, MarketplaceAccountUpdate, MarketplaceAccount,
    ProductListingCreate, ProductListingUpdate, ProductListing
)

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    # Product CRUD Operations
    def create_product(self, user_id: str, product: ProductCreate) -> Product:
        db_product = DBProduct(
            user_id=user_id,
            **product.dict(exclude={"images", "variants"}, exclude_none=True)
        )
        
        self.db.add(db_product)
        self.db.flush()  # Flush to get the product ID
        
        # Add images if provided
        if product.images:
            for img in product.images:
                db_img = DBProductImage(
                    product_id=db_product.id,
                    **img.dict(exclude_none=True)
                )
                self.db.add(db_img)
        
        # Add variants if provided
        if product.variants:
            for variant in product.variants:
                db_variant = DBProductVariant(
                    product_id=db_product.id,
                    **variant.dict(exclude_none=True)
                )
                self.db.add(db_variant)
        
        self.db.commit()
        self.db.refresh(db_product)
        return Product.from_orm(db_product)

    def get_product(self, user_id: str, product_id: int) -> Optional[Product]:
        db_product = self.db.query(DBProduct).filter(
            and_(
                DBProduct.id == product_id,
                DBProduct.user_id == user_id,
                DBProduct.deleted_at.is_(None)
            )
        ).first()
        
        if not db_product:
            return None
            
        return Product.from_orm(db_product)

    def list_products(
        self, 
        user_id: str,
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Product]:
        query = self.db.query(DBProduct).filter(
            and_(
                DBProduct.user_id == user_id,
                DBProduct.deleted_at.is_(None)
            )
        )
        
        if search:
            search_filter = or_(
                DBProduct.title.ilike(f"%{search}%"),
                DBProduct.description.ilike(f"%{search}%"),
                DBProduct.sku.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
            
        if category:
            query = query.filter(DBProduct.category == category)
            
        if is_active is not None:
            query = query.filter(DBProduct.is_active == is_active)
            
        products = query.offset(skip).limit(limit).all()
        return [Product.from_orm(p) for p in products]

    def update_product(
        self, 
        user_id: str, 
        product_id: int, 
        product: ProductUpdate
    ) -> Optional[Product]:
        db_product = self.db.query(DBProduct).filter(
            and_(
                DBProduct.id == product_id,
                DBProduct.user_id == user_id,
                DBProduct.deleted_at.is_(None)
            )
        ).first()
        
        if not db_product:
            return None
            
        update_data = product.dict(exclude_unset=True, exclude={"images", "variants"})
        
        for field, value in update_data.items():
            setattr(db_product, field, value)
            
        # Update images if provided
        if product.images is not None:
            # Delete existing images
            self.db.query(DBProductImage).filter(
                DBProductImage.product_id == product_id
            ).delete()
            
            # Add new images
            for img in product.images:
                db_img = DBProductImage(
                    product_id=product_id,
                    **img.dict(exclude_none=True)
                )
                self.db.add(db_img)
        
        # Update variants if provided
        if product.variants is not None:
            # Delete existing variants
            self.db.query(DBProductVariant).filter(
                DBProductVariant.product_id == product_id
            ).delete()
            
            # Add new variants
            for variant in product.variants:
                db_variant = DBProductVariant(
                    product_id=product_id,
                    **variant.dict(exclude_none=True)
                )
                self.db.add(db_variant)
        
        db_product.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_product)
        return Product.from_orm(db_product)

    def delete_product(self, user_id: str, product_id: int) -> bool:
        db_product = self.db.query(DBProduct).filter(
            and_(
                DBProduct.id == product_id,
                DBProduct.user_id == user_id,
                DBProduct.deleted_at.is_(None)
            )
        ).first()
        
        if not db_product:
            return False
            
        db_product.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    # Marketplace Account CRUD Operations
    def create_marketplace_account(
        self, 
        user_id: str, 
        account: MarketplaceAccountCreate
    ) -> MarketplaceAccount:
        db_account = DBMarketplaceAccount(
            user_id=user_id,
            **account.dict(exclude_none=True)
        )
        
        self.db.add(db_account)
        self.db.commit()
        self.db.refresh(db_account)
        return MarketplaceAccount.from_orm(db_account)

    def get_marketplace_account(
        self, 
        user_id: str, 
        account_id: int
    ) -> Optional[MarketplaceAccount]:
        db_account = self.db.query(DBMarketplaceAccount).filter(
            and_(
                DBMarketplaceAccount.id == account_id,
                DBMarketplaceAccount.user_id == user_id
            )
        ).first()
        
        if not db_account:
            return None
            
        return MarketplaceAccount.from_orm(db_account)

    def list_marketplace_accounts(
        self, 
        user_id: str,
        marketplace: Optional[MarketplaceType] = None,
        is_active: Optional[bool] = None
    ) -> List[MarketplaceAccount]:
        query = self.db.query(DBMarketplaceAccount).filter(
            DBMarketplaceAccount.user_id == user_id
        )
        
        if marketplace:
            query = query.filter(DBMarketplaceAccount.marketplace == marketplace)
            
        if is_active is not None:
            query = query.filter(DBMarketplaceAccount.is_active == is_active)
            
        accounts = query.all()
        return [MarketplaceAccount.from_orm(a) for a in accounts]

    def update_marketplace_account(
        self, 
        user_id: str, 
        account_id: int, 
        account: MarketplaceAccountUpdate
    ) -> Optional[MarketplaceAccount]:
        db_account = self.db.query(DBMarketplaceAccount).filter(
            and_(
                DBMarketplaceAccount.id == account_id,
                DBMarketplaceAccount.user_id == user_id
            )
        ).first()
        
        if not db_account:
            return None
            
        update_data = account.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_account, field, value)
            
        db_account.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_account)
        return MarketplaceAccount.from_orm(db_account)

    def delete_marketplace_account(self, user_id: str, account_id: int) -> bool:
        db_account = self.db.query(DBMarketplaceAccount).filter(
            and_(
                DBMarketplaceAccount.id == account_id,
                DBMarketplaceAccount.user_id == user_id
            )
        ).first()
        
        if not db_account:
            return False
            
        self.db.delete(db_account)
        self.db.commit()
        return True

    # Product Listing Operations
    def create_product_listing(
        self, 
        user_id: str, 
        listing: ProductListingCreate
    ) -> Optional[ProductListing]:
        # Verify product belongs to user
        product = self.db.query(DBProduct).filter(
            and_(
                DBProduct.id == listing.product_id,
                DBProduct.user_id == user_id,
                DBProduct.deleted_at.is_(None)
            )
        ).first()
        
        if not product:
            return None
            
        # Verify marketplace account belongs to user
        account = self.db.query(DBMarketplaceAccount).filter(
            and_(
                DBMarketplaceAccount.id == listing.marketplace_account_id,
                DBMarketplaceAccount.user_id == user_id
            )
        ).first()
        
        if not account:
            return None
            
        db_listing = DBProductListing(**listing.dict(exclude_none=True))
        
        self.db.add(db_listing)
        self.db.commit()
        self.db.refresh(db_listing)
        return ProductListing.from_orm(db_listing)

    def update_product_listing(
        self, 
        user_id: str, 
        listing_id: int, 
        listing: ProductListingUpdate
    ) -> Optional[ProductListing]:
        db_listing = self.db.query(DBProductListing).join(
            DBProduct,
            DBProductListing.product_id == DBProduct.id
        ).filter(
            and_(
                DBProductListing.id == listing_id,
                DBProduct.user_id == user_id
            )
        ).first()
        
        if not db_listing:
            return None
            
        update_data = listing.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_listing, field, value)
            
        db_listing.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_listing)
        return ProductListing.from_orm(db_listing)

    def list_product_listings(
        self,
        user_id: str,
        product_id: Optional[int] = None,
        marketplace_account_id: Optional[int] = None,
        status: Optional[ListingStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProductListing]:
        query = self.db.query(DBProductListing).join(
            DBProduct,
            DBProductListing.product_id == DBProduct.id
        ).filter(
            DBProduct.user_id == user_id
        )
        
        if product_id is not None:
            query = query.filter(DBProductListing.product_id == product_id)
            
        if marketplace_account_id is not None:
            query = query.filter(
                DBProductListing.marketplace_account_id == marketplace_account_id
            )
            
        if status is not None:
            query = query.filter(DBProductListing.status == status)
            
        listings = query.offset(skip).limit(limit).all()
        return [ProductListing.from_orm(l) for l in listings]

    def sync_product_to_marketplace(
        self,
        user_id: str,
        product_id: int,
        marketplace_account_id: int
    ) -> Optional[ProductListing]:
        """
        Synchronize a product to a marketplace.
        This is a placeholder for the actual marketplace integration logic.
        """
        # Verify product and marketplace account belong to user
        product = self.db.query(DBProduct).filter(
            and_(
                DBProduct.id == product_id,
                DBProduct.user_id == user_id,
                DBProduct.deleted_at.is_(None)
            )
        ).first()
        
        if not product:
            return None
            
        account = self.db.query(DBMarketplaceAccount).filter(
            and_(
                DBMarketplaceAccount.id == marketplace_account_id,
                DBMarketplaceAccount.user_id == user_id
            )
        ).first()
        
        if not account:
            return None
            
        # Check if listing already exists
        listing = self.db.query(DBProductListing).filter(
            and_(
                DBProductListing.product_id == product_id,
                DBProductListing.marketplace_account_id == marketplace_account_id
            )
        ).first()
        
        try:
            # TODO: Implement actual marketplace API integration
            # This is a placeholder for the actual implementation
            
            listing_data = {
                "marketplace_account_id": marketplace_account_id,
                "product_id": product_id,
                "status": ListingStatus.ACTIVE,
                "price": float(product.price),
                "quantity": product.quantity,
                "title": product.title,
                "description": product.description,
                "synced_at": datetime.utcnow()
            }
            
            if listing:
                # Update existing listing
                for key, value in listing_data.items():
                    setattr(listing, key, value)
                listing.updated_at = datetime.utcnow()
            else:
                # Create new listing
                listing = DBProductListing(**listing_data)
                self.db.add(listing)
            
            # Update marketplace account last sync time
            account.last_sync_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(listing)
            
            return ProductListing.from_orm(listing)
            
        except Exception as e:
            self.db.rollback()
            
            # Update or create listing with error status
            error_data = {
                "marketplace_account_id": marketplace_account_id,
                "product_id": product_id,
                "status": ListingStatus.ERROR,
                "error_message": str(e),
                "synced_at": datetime.utcnow()
            }
            
            if listing:
                for key, value in error_data.items():
                    setattr(listing, key, value)
                listing.updated_at = datetime.utcnow()
            else:
                listing = DBProductListing(**error_data)
                self.db.add(listing)
                
            self.db.commit()
            return None
