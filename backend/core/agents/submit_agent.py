from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from playwright.async_api import async_playwright
from letta import LettaClient  # For stateful agents
import os
from supabase import create_client, Client  # Add Supabase import
from fastapi import APIRouter  # Move import to top

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# OpenRouter via LangChain (low-cost models)
llm = ChatOpenAI(
    model="llava-13b-v1.6",  # Vision for images
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0.7,
)

# Letta client for stateful memory
letta = LettaClient(token=os.getenv("LETTA_API_KEY"))

# Prompt chain for analysis
prompt = ChatPromptTemplate.from_template(
    "Analyze images {images} and summary: {summary}. Category: {category}. Condition: {condition}. "
    "Extract: name, desc, price range, damage, age, usage. Use scraped data: {scraped}."
)
chain = prompt | llm | StrOutputParser()

async def scrape_sites(query):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers({"User-Agent": "ItemAnalyzerBot/1.0"})
        results = []
        sites = ["ebay.com/sch/i.html?_nkw=" + query, "amazon.com/s?k=" + query]  # Add more
        for site in sites:
            await page.goto("https://" + site, wait_until="networkidle", timeout=10000)
            await page.wait_for_timeout(1000)  # Rate limit
            titles = await page.locator(".s-item__title").all_text_contents()[:5]
            prices = await page.locator(".s-item__price").all_text_contents()[:5]
            results.extend(zip(titles, prices))
        await browser.close()
    # Average price
    prices = [float(p.replace('$', '')) for p in [r[1] for r in results] if p.startswith('$')]
    avg = sum(prices) / len(prices) if prices else 0
    arbitrage = [r for r in results if float(r[1].replace('$', '')) < avg * 0.7]
    return {"similar": results, "avg_price": avg, "arbitrage": arbitrage}

async def process_submission(images, summary, category="", condition=""):
    # Letta agent for stateful workflow
    agent_id = os.getenv("LETTA_AGENT_ID")
    agent = letta.agents.get(agent_id)
    
    # Scrape
    scraped = await scrape_sites(summary)
    
    # Chain via LangChain
    analysis = await chain.ainvoke({
        "images": images,
        "summary": summary,
        "category": category,
        "condition": condition,
        "scraped": scraped,
    })
    
    # Generate listings (chain to text model)
    listing_prompt = ChatPromptTemplate.from_template(
        "Based on {analysis} and scraped {scraped}, generate listings for eBay, Amazon, FB. Output JSON + CSV."
    )
    listing_chain = listing_prompt | ChatOpenAI(model="meta-llama/llama-3.1-8b-instruct:free") | StrOutputParser()
    listings = await listing_chain.ainvoke({"analysis": analysis, "scraped": scraped})
    
    # Return raw data for CSV generation
    return {
        "analysis": analysis,
        "listings": listings,
        "price_data": {
            "avg_price": scraped["avg_price"],
            "arbitrage": scraped["arbitrage"]
        },
        "condition": condition
    }
    
    # Store in Letta memory (transient)
    await agent.messages.create(content=analysis, role="assistant")
    
    return {"analysis": analysis, "listings": listings, "csv": csv_lines, "price": scraped["avg_price"], "arbitrage": scraped["arbitrage"]}

# API endpoint (integrate with Suna/FastAPI)
router = APIRouter()

@router.post("/submit")
async def submit_item(data: dict):
    # Clerk/Stripe check (pseudo)
    if not data.get("credits", 0) > 0:
        return {"error": "Insufficient credits"}
    
    # Deduct 1 credit atomically from Supabase
    user_id = data.get("user_id")
    response = (
        supabase.table("users")
        .update({"credits": "credits - 1"})
        .eq("id", user_id)
        .execute()
    )
    
    if response.error:
        return {"error": f"Credit deduction failed: {response.error.message}"}
    
    result = await process_submission(data["images"], data["summary"], data.get("category"), data.get("condition"))
    
    return result