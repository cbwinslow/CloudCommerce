from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from litellm import completion
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from bitwarden import BitwardenClient  # CLI wrapper
import os
import sentry_sdk
from typing import Optional

# Import routers
from core.routers import subscriptions, webhooks

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

# Sentry init with full features
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        enable_tracing=True,
        enable_profiling=True,
        integrations=[sentry_sdk.integrations.fastapi.FastApiIntegration()],
        send_default_pii=False,  # No PII
        release=f"{os.getenv('npm_package_version', '1.0.0')}",
    )

@app.post("/rotate-secrets")
async def rotate_secrets():
    # Bitwarden setup
    bw = BitwardenClient()
    await bw.unlock(os.getenv("BITWARDEN_PASSWORD"))
    
    # Rotate secrets (pseudo code)
    # ...
    
    return {"status": "success"}

# Bitwarden for secrets
async def get_secret(name: str):
    client = BitwardenClient()
    await client.login(email=os.getenv("BITWARDEN_EMAIL"), password=os.getenv("BITWARDEN_PASSWORD"))
    item = await client.get_item("cloudcommerce-keys")
    return item.fields[name].value

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
    with sentry_sdk.start_span(op="llm.chain"):
        # LiteLLM for OpenRouter
        openrouter_key = await get_secret("OPENROUTER")
        response = completion(
            model="openrouter/llava-13b-v1.6",
            messages=[{"role": "user", "content": data["prompt"]}],
            api_key=openrouter_key,
            temperature=0.7
        )

        # LlamaIndex RAG for semantic comps
        retriever = index.as_retriever()
        comps = retriever.retrieve(data["summary"])
        rag_prompt = f"Based on comps {comps}, generate listing for {data['summary']}."
        rag_response = completion(model="openrouter/llama-3.1-8b-instruct", messages=[{"role": "user", "content": rag_prompt}], api_key=openrouter_key)

        sentry_sdk.start_span(op="db.insert")  # Trace DB
        # Supabase insert...

    return {"analysis": response.choices[0].message.content, "rag": rag_response.choices[0].message.content}

# Cron for rotation (Supabase Edge calls this)
@app.post("/rotate-secrets")
async def rotate_secrets():
    with sentry_sdk.start_span(op="secret.rotation"):
        client = BitwardenClient()
        await client.login(email=os.getenv("BITWARDEN_EMAIL"), password=os.getenv("BITWARDEN_PASSWORD"))
        new_key = os.urandom(32).hex()
        await client.set_item("cloudcommerce-keys", {"OPENROUTER": new_key})
        # Update services (e.g., env restart)
        sentry_sdk.capture_message("Secrets rotated", level="info")
    return {"status": "rotated"}
