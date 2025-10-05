"""
Comprehensive test configuration for CloudCommerce backend testing.
Provides fixtures, mocks, and utilities for 100% test coverage.
"""
import os
import sys
import pytest
import asyncio
from typing import Dict, Any, AsyncGenerator
from unittest.mock import Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from core.database.models.product import Product, ProductImage, ProductAnalysis
from core.models.product import ProductCreate, ProductUpdate
from core.repositories.product import ProductRepository
from core.agents.submit_agent import SubmitAgent
from core.auth.monetization import SubscriptionManager


@pytest.fixture
def mock_env():
    """Mock environment variables for testing."""
    original_env = os.environ.copy()

    # Set mock environment variables
    os.environ.update({
        "DEV_MOCK": "true",
        "OPENROUTER_API_KEY": "sk-or-v1-mock-key-for-testing",
        "STRIPE_SECRET_KEY": "sk_test_mock_stripe_key",
        "STRIPE_WEBHOOK_SECRET": "whsec_mock_webhook_secret",
        "SUPABASE_URL": "https://mock.supabase.co",
        "SUPABASE_ANON_KEY": "mock_anon_key",
        "SUPABASE_SERVICE_ROLE_KEY": "mock_service_role_key",
        "JWT_SECRET": "mock_jwt_secret_for_testing",
        "SENTRY_DSN": "mock_sentry_dsn"
    })

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_client(mock_env):
    """FastAPI test client with mocked dependencies."""
    return TestClient(app)


@pytest.fixture
async def async_client(mock_env):
    """Async HTTP client for testing async endpoints."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing AI functionality."""
    return {
        "choices": [
            {
                "message": {
                    "content": "Mock AI analysis: This is a vintage teapot in excellent condition, perfect for collectors. Suggested price: $45.00. Best platforms: eBay, Etsy."
                }
            }
        ],
        "usage": {
            "total_tokens": 150,
            "prompt_tokens": 100,
            "completion_tokens": 50
        }
    }


@pytest.fixture
def mock_stripe_checkout_session():
    """Mock Stripe checkout session response."""
    return {
        "id": "cs_test_mock_session_id",
        "url": "https://checkout.stripe.com/pay/cs_test_mock_session_id",
        "status": "open"
    }


@pytest.fixture
def mock_product_data():
    """Mock product data for testing."""
    return {
        "title": "Vintage Ceramic Teapot",
        "description": "Beautiful vintage teapot from the 1970s",
        "price": 45.00,
        "category": "Home & Garden",
        "condition": "Used - Excellent",
        "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
        "platform_listings": {
            "eBay": {"item_id": "eb123456", "url": "https://ebay.com/itm/eb123456"},
            "Facebook": {"listing_id": "fb789", "url": "https://facebook.com/marketplace/fb789"}
        }
    }


@pytest.fixture
def mock_user_data():
    """Mock user data for authentication testing."""
    return {
        "id": "user_123",
        "email": "test@example.com",
        "name": "Test User",
        "subscription_tier": "pro",
        "is_active": True
    }


@pytest.fixture
def mock_database_session():
    """Mock database session for testing."""
    session = MagicMock()

    # Mock product queries
    mock_product = Product(
        id="prod_123",
        title="Test Product",
        description="Test Description",
        price=25.00,
        category="Test Category",
        condition="New",
        user_id="user_123",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z"
    )

    session.query.return_value.filter.return_value.first.return_value = mock_product
    session.query.return_value.filter.return_value.all.return_value = [mock_product]
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()

    return session


@pytest.fixture
def mock_product_repository(mock_database_session):
    """Mock product repository for testing."""
    repo = MagicMock(spec=ProductRepository)
    repo.session = mock_database_session
    repo.create = AsyncMock(return_value=Product(id="prod_123", **mock_product_data()))
    repo.get_by_id = AsyncMock(return_value=Product(id="prod_123", **mock_product_data()))
    repo.update = AsyncMock(return_value=Product(id="prod_123", **mock_product_data()))
    repo.delete = AsyncMock(return_value=True)
    repo.list_by_user = AsyncMock(return_value=[Product(id="prod_123", **mock_product_data())])

    return repo


@pytest.fixture
def mock_submit_agent():
    """Mock submit agent for testing AI functionality."""
    agent = MagicMock(spec=SubmitAgent)

    mock_analysis = {
        "title": "Vintage Ceramic Teapot",
        "description": "Beautiful vintage teapot from the 1970s in excellent condition",
        "suggested_price": 45.00,
        "confidence": 85,
        "category": "Home & Garden",
        "recommended_platforms": ["eBay", "Facebook Marketplace", "Mercari"],
        "analysis_metadata": {
            "processing_time": 1.2,
            "tokens_used": 150,
            "model_used": "gpt-4"
        }
    }

    agent.analyze_product = AsyncMock(return_value=mock_analysis)
    agent.generate_listing = AsyncMock(return_value=mock_analysis)
    agent.validate_images = AsyncMock(return_value={"valid": True, "count": 2})

    return agent


@pytest.fixture
def mock_subscription_manager():
    """Mock subscription manager for testing billing functionality."""
    manager = MagicMock(spec=SubscriptionManager)

    manager.get_user_subscription = MagicMock(return_value={
        "tier": "pro",
        "status": "active",
        "features": ["ai_analysis", "bulk_upload", "priority_support"]
    })

    manager.create_checkout_session = AsyncMock(return_value={
        "session_id": "cs_test_mock_session",
        "url": "https://checkout.stripe.com/pay/cs_test_mock_session"
    })

    manager.validate_subscription = MagicMock(return_value=True)
    manager.get_usage_limits = MagicMock(return_value={
        "monthly_analyses": 100,
        "used_analyses": 25,
        "remaining_analyses": 75
    })

    return manager


@pytest.fixture
def sample_product_images():
    """Sample product image data for testing."""
    return [
        {
            "url": "https://example.com/image1.jpg",
            "filename": "teapot1.jpg",
            "size": 2048576,  # 2MB
            "content_type": "image/jpeg"
        },
        {
            "url": "https://example.com/image2.jpg",
            "filename": "teapot2.jpg",
            "size": 1536000,  # 1.5MB
            "content_type": "image/jpeg"
        }
    ]


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for bulk upload testing."""
    return """title,description,price,category,condition
Vintage Teapot,Beautiful vintage teapot,45.00,Home & Garden,Excellent
Antique Vase,Rare antique vase,120.00,Antiques,Good
Modern Chair,Contemporary office chair,89.99,Furniture,New"""


@pytest.fixture
def mock_external_apis():
    """Mock external API responses for testing integrations."""
    return {
        "openrouter": {
            "status_code": 200,
            "json": lambda: {
                "choices": [{"message": {"content": "Mock AI response"}}],
                "usage": {"total_tokens": 100}
            }
        },
        "stripe": {
            "status_code": 200,
            "json": lambda: {
                "id": "cs_test_mock",
                "url": "https://checkout.stripe.com/pay/cs_test_mock"
            }
        },
        "supabase": {
            "status_code": 200,
            "json": lambda: {
                "data": [{"id": "record_123", "created": True}],
                "error": None
            }
        }
    }


@pytest.fixture
def test_performance_metrics():
    """Performance metrics for load testing."""
    return {
        "response_time_threshold": 1000,  # milliseconds
        "concurrent_users": 50,
        "requests_per_second": 10,
        "memory_limit_mb": 512,
        "cpu_usage_threshold": 80  # percentage
    }


@pytest.fixture
def security_test_payloads():
    """Security test payloads for vulnerability testing."""
    return {
        "xss_payloads": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "'; DROP TABLE users; --"
        ],
        "sql_injection": [
            "'; DROP TABLE products; --",
            "1' OR '1'='1",
            "admin'--",
            "1; SELECT * FROM users"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "/etc/passwd",
            "C:\\Windows\\System32\\drivers\\etc\\hosts"
        ]
    }


# Test utilities
class TestUtils:
    """Utility class for test helpers."""

    @staticmethod
    def assert_response_structure(response_data: Dict[str, Any], required_fields: list):
        """Assert that response contains required fields."""
        for field in required_fields:
            assert field in response_data, f"Missing required field: {field}"

    @staticmethod
    def assert_product_structure(product_data: Dict[str, Any]):
        """Assert that product data has correct structure."""
        required_fields = ["title", "description", "price", "category"]
        TestUtils.assert_response_structure(product_data, required_fields)
        assert isinstance(product_data["price"], (int, float)), "Price must be numeric"
        assert product_data["price"] > 0, "Price must be positive"

    @staticmethod
    def generate_test_image_url(width: int = 800, height: int = 600) -> str:
        """Generate a test image URL."""
        return f"https://picsum.photos/{width}/{height}?random=test"

    @staticmethod
    def create_mock_file(content: str = "test content", filename: str = "test.txt") -> Mock:
        """Create a mock file object."""
        mock_file = Mock()
        mock_file.read.return_value = content.encode()
        mock_file.name = filename
        mock_file.size = len(content)
        return mock_file


# Export commonly used fixtures
__all__ = [
    "mock_env",
    "test_client",
    "async_client",
    "mock_llm_response",
    "mock_stripe_checkout_session",
    "mock_product_data",
    "mock_user_data",
    "mock_database_session",
    "mock_product_repository",
    "mock_submit_agent",
    "mock_subscription_manager",
    "sample_product_images",
    "sample_csv_data",
    "mock_external_apis",
    "test_performance_metrics",
    "security_test_payloads",
    "TestUtils"
]
