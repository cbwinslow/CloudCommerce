from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from litellm import completion
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
# from bitwarden import BitwardenClient  # CLI wrapper - commented out for mock mode
import os
# import sentry_sdk  # Commented out for mock mode
from typing import Optional

# Import routers
from core.routers import subscriptions, webhooks, products

app = FastAPI(
    title="CloudCommerce API",
    description="API for CloudCommerce - AI-Powered E-commerce Listing Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(subscriptions.router)
app.include_router(webhooks.router)
app.include_router(products.router)

# Sentry initialization commented out for mock mode
# if os.getenv("SENTRY_DSN"):
#     sentry_sdk.init(
#         dsn=os.getenv("SENTRY_DSN"),
#         traces_sample_rate=1.0,
#         profiles_sample_rate=1.0,
#         enable_tracing=True,
#         enable_profiling=True,
#         integrations=[sentry_sdk.integrations.fastapi.FastApiIntegration()],
#         send_default_pii=False,  # No PII
#         release=f"{os.getenv('npm_package_version', '1.0.0')}",
#     )

# Mock mode secret rotation
@app.post("/rotate-secrets")
async def rotate_secrets():
    # Mock implementation for development
    return {"status": "success", "message": "Mock mode - no real secrets to rotate"}

# Mock secret retrieval for development
async def get_secret(name: str):
    # Return mock keys for development
    mock_keys = {
        "OPENROUTER": "sk-or-v1-mock-key-for-development-only",
        "STRIPE": "sk_test_mock_stripe_key",
        "SUPABASE": "mock_supabase_key"
    }
    return mock_keys.get(name, f"mock_{name}_key")

# LlamaIndex for RAG (lazy load to avoid blocking startup)
embed_model = None
index = None

def get_embed_model():
    global embed_model
    if embed_model is None:
        embed_model = OpenAIEmbedding(model="text-embedding-3-small", api_key=os.getenv("OPENAI_API_KEY"))
    return embed_model

def get_index():
    global index
    if index is None:
        index = VectorStoreIndex.from_documents([])  # Load from Supabase
    return index

class InputData(BaseModel):
    images: list[str]
    summary: str
    category: str = None
    condition: str = None

@app.post("/submit")
async def submit_item(request: Request, data: dict):
    # Mock implementation for development
    return {
        "analysis": "Mock AI analysis response - AI agent would analyze the submitted item here",
        "rag": "Mock RAG response - AI agent would use vector search for similar items",
        "confidence": 85,
        "suggested_price": "$25.00",
        "recommended_platforms": ["eBay", "Facebook Marketplace", "Mercari"]
    }
