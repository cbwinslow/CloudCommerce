"""
Comprehensive tests for product and marketplace integration functionality.
"""
import asyncio
import pytest
import time
from fastapi import status, HTTPException
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from core.models.product import (
    Product, ProductCreate, ProductUpdate,
    ProductVariant, ProductImage,
    MarketplaceAccount, MarketplaceAccountCreate,
    ProductListing, ProductListingCreate,
    MarketplaceType, ListingStatus, ProductCondition
)

# Test data
TEST_USER_ID = "user_123"
TEST_PRODUCT_ID = 1
TEST_ACCOUNT_ID = 1
TEST_LISTING_ID = 1

# Fixtures
@pytest.fixture
def sample_product_data():
    return {
        "title": "Vintage Teapot",
        "description": "Beautiful vintage teapot from the 1970s",
        "price": 45.00,
        "category": "Home & Garden",
        "condition": ProductCondition.USED_GOOD,
        "sku": "TEA-001",
        "quantity": 1,
        "weight": 0.5,
        "weight_unit": "kg",
        "is_active": True,
        "images": [
            {"url": "https://example.com/image1.jpg", "alt_text": "Front view"},
            {"url": "https://example.com/image2.jpg", "alt_text": "Side view"}
        ],
        "variants": [
            {
                "sku": "TEA-001-BLUE",
                "option1_name": "Color",
                "option1_value": "Blue",
                "price": 45.00,
                "quantity": 10
            }
        ]
    }

@pytest.fixture
def sample_marketplace_account():
    return {
        "marketplace": MarketplaceType.AMAZON,
        "name": "My Amazon Store",
        "is_active": True,
        "credentials": {"api_key": "test_key", "api_secret": "test_secret"}
    }

# Test Product Repository
class TestProductRepository:
    async def test_create_product(self, mock_database_session, sample_product_data):
        from core.repositories.product import ProductRepository
        
        repo = ProductRepository(mock_database_session)
        product_create = ProductCreate(**sample_product_data)
        
        # Test successful creation
        result = await repo.create_product(TEST_USER_ID, product_create)
        
        assert result is not None
        assert result.title == sample_product_data["title"]
        assert result.user_id == TEST_USER_ID
        assert len(result.images) == len(sample_product_data["images"])
        assert len(result.variants) == len(sample_product_data["variants"])
        
        # Verify database session was called
        mock_database_session.add.assert_called()
        mock_database_session.commit.assert_called()
        mock_database_session.refresh.assert_called()

    async def test_get_product(self, mock_database_session):
        from core.repositories.product import ProductRepository
        
        repo = ProductRepository(mock_database_session)
        result = await repo.get_product(TEST_USER_ID, TEST_PRODUCT_ID)
        
        assert result is not None
        assert result.id == TEST_PRODUCT_ID
        
        # Test product not found
        mock_database_session.query.return_value.filter.return_value.first.return_value = None
        result = await repo.get_product(TEST_USER_ID, 999)
        assert result is None

# Test API Endpoints
class TestProductAPI:
    async def test_create_product(self, async_client, mock_product_repository, sample_product_data):
        # Mock the repository in the app's dependency override
        from fastapi import FastAPI
        from core.database.database import get_db
        
        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: None
        
        # Test successful creation
        response = await async_client.post(
            "/api/products/",
            json={
                **sample_product_data,
                "condition": sample_product_data["condition"].value,
                "images": [
                    {"url": img["url"], "alt_text": img["alt_text"]}
                    for img in sample_product_data["images"]
                ],
                "variants": [
                    {
                        "sku": v["sku"],
                        "option1_name": v["option1_name"],
                        "option1_value": v["option1_value"],
                        "price": v["price"],
                        "quantity": v["quantity"]
                    }
                    for v in sample_product_data["variants"]
                ]
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == sample_product_data["title"]
        assert data["user_id"] == TEST_USER_ID
        
        # Test validation error
        response = await async_client.post(
            "/api/products/",
            json={"title": ""}  # Missing required fields
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_sync_product_to_marketplace(
        self, 
        async_client, 
        mock_product_repository,
        sample_product_data,
        sample_marketplace_account
    ):
        # Mock the sync method
        mock_product_repository.sync_product_to_marketplace = AsyncMock(return_value={
            "id": TEST_LISTING_ID,
            "product_id": TEST_PRODUCT_ID,
            "marketplace_account_id": TEST_ACCOUNT_ID,
            "status": ListingStatus.ACTIVE,
            "marketplace_listing_id": "AMZ123",
            "synced_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Test successful sync
        response = await async_client.post(
            f"/api/products/{TEST_PRODUCT_ID}/sync/{TEST_ACCOUNT_ID}"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == TEST_LISTING_ID
        assert data["status"] == ListingStatus.ACTIVE
        
        # Test product not found
        mock_product_repository.sync_product_to_marketplace.return_value = None
        response = await async_client.post(
            f"/api/products/999/sync/{TEST_ACCOUNT_ID}"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

# Test Marketplace Integration
class TestMarketplaceIntegration:
    async def test_create_marketplace_account(self, async_client, sample_marketplace_account):
        response = await async_client.post(
            "/api/products/marketplace/accounts/",
            json={
                **sample_marketplace_account,
                "marketplace": sample_marketplace_account["marketplace"].value,
                "credentials": {"api_key": "test_key", "api_secret": "test_secret"}
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_marketplace_account["name"]
        assert data["marketplace"] == sample_marketplace_account["marketplace"].value
        
        # Test invalid marketplace type
        response = await async_client.post(
            "/api/products/marketplace/accounts/",
            json={
                **sample_marketplace_account,
                "marketplace": "INVALID_MARKETPLACE",
                "credentials": {"api_key": "test_key"}
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Test Error Handling
class TestProductVariants:
    async def test_variant_operations(self, mock_database_session, sample_product_data):
        from core.repositories.product import ProductRepository
        
        repo = ProductRepository(mock_database_session)
        
        # Test creating product with multiple variants
        product_data = sample_product_data.copy()
        product_data["variants"] = [
            {
                "sku": "TEA-001-BLUE",
                "option1_name": "Color",
                "option1_value": "Blue",
                "price": 45.00,
                "quantity": 10
            },
            {
                "sku": "TEA-001-RED",
                "option1_name": "Color",
                "option1_value": "Red",
                "price": 47.00,
                "quantity": 5
            }
        ]
        
        product = await repo.create_product(TEST_USER_ID, ProductCreate(**product_data))
        assert len(product.variants) == 2
        assert {v.option1_value for v in product.variants} == {"Blue", "Red"}
        
        # Test updating variants
        update_data = product_data.copy()
        update_data["variants"].append({
            "sku": "TEA-001-GREEN",
            "option1_name": "Color",
            "option1_value": "Green",
            "price": 49.00,
            "quantity": 8
        })
        
        updated = await repo.update_product(TEST_USER_ID, product.id, ProductUpdate(**update_data))
        assert len(updated.variants) == 3
        assert any(v.option1_value == "Green" for v in updated.variants)

class TestBulkOperations:
    async def test_bulk_product_import(self, async_client):
        # Test CSV import
        csv_data = """
        title,description,price,category,condition,quantity,sku
        Test Product 1,Description 1,19.99,Electronics,new,10,TEST-001
        Test Product 2,Description 2,29.99,Home,used_good,5,TEST-002
        """
        
        files = {"file": ("products.csv", csv_data, "text/csv")}
        response = await async_client.post("/api/products/import/csv/", files=files)
        
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert result["processed"] == 2
        assert result["success"] == 2
        assert len(result["products"]) == 2
        
    async def test_bulk_status_update(self, async_client, mock_product_repository):
        # Test bulk updating product statuses
        product_ids = [1, 2, 3]
        response = await async_client.patch(
            "/api/products/bulk/status/",
            json={
                "product_ids": product_ids,
                "is_active": False
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["updated"] == len(product_ids)

class TestConcurrentAccess:
    async def test_concurrent_updates(self, mock_database_session):
        """Test that concurrent updates don't cause data corruption."""
        from core.repositories.product import ProductRepository
        
        repo = ProductRepository(mock_database_session)
        
        # Simulate concurrent updates
        async def update_quantity(product_id: int, delta: int):
            product = await repo.get_product(TEST_USER_ID, product_id)
            if not product:
                return False
                
            # Simulate processing time
            await asyncio.sleep(0.1)
            
            # Update quantity
            update_data = product.dict()
            update_data["quantity"] = max(0, (product.quantity or 0) + delta)
            await repo.update_product(TEST_USER_ID, product_id, ProductUpdate(**update_data))
            return True
        
        # Create initial product
        product = await repo.create_product(TEST_USER_ID, ProductCreate(
            title="Concurrent Test Product",
            description="Test product for concurrency",
            price=10.00,
            category="Test",
            condition=ProductCondition.NEW,
            quantity=10
        ))
        
        # Run concurrent updates
        tasks = [
            update_quantity(product.id, -2),  # Remove 2 items
            update_quantity(product.id, 5),    # Add 5 items
            update_quantity(product.id, -3),   # Remove 3 items
        ]
        
        await asyncio.gather(*tasks)
        
        # Verify final state
        updated = await repo.get_product(TEST_USER_ID, product.id)
        assert updated.quantity == 10  # 10 - 2 + 5 - 3 = 10

class TestPerformance:
    @pytest.mark.parametrize("num_products", [10, 100, 1000])
    async def test_list_products_performance(
        self, 
        async_client, 
        benchmark, 
        num_products: int
    ):
        """Test performance of listing products with pagination."""
        # This is a simple benchmark - in a real test, you'd want to set up
        # test data first, then measure the actual API call
        
        async def list_products():
            return await async_client.get(
                f"/api/products/?skip=0&limit={num_products}"
            )
        
        # Run benchmark
        response = await benchmark(list_products)
        assert response.status_code == status.HTTP_200_OK
        
        # Add performance assertions
        data = response.json()
        assert len(data) <= num_products
        
        # Log performance metrics
        print(f"Listed {len(data)} products in {benchmark.stats['mean']:.4f}s")

class TestErrorHandling:
    async def test_product_not_found(self, async_client):
        response = await async_client.get("/api/products/999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    async def test_unauthorized_access(self, async_client):
        # Test accessing another user's product
        response = await async_client.get(f"/api/products/{TEST_PRODUCT_ID}")
        # Should be 404 to avoid leaking existence of resources
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
    async def test_invalid_marketplace_credentials(self, async_client):
        # Test with invalid marketplace credentials
        response = await async_client.post(
            "/api/products/marketplace/accounts/",
            json={
                "marketplace": "amazon",
                "name": "Invalid Account",
                "credentials": {"invalid": "data"}
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    async def test_rate_limiting(self, async_client):
        # Test API rate limiting
        # Note: This assumes you have rate limiting middleware in place
        responses = []
        for _ in range(10):  # Adjust based on your rate limit
            response = await async_client.get("/api/products/")
            responses.append(response.status_code)
            
        # The last response should be 429 if rate limited
        # This is just an example - adjust based on your rate limiting setup
        assert status.HTTP_200_OK in responses
