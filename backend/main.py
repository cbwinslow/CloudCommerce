from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from crewai import Agent, Task, Crew
from openai import OpenAI
import os

app = FastAPI()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

class InputData(BaseModel):
    images: list[str]
    summary: str
    category: str = None
    condition: str = None

# Define Agents
vision_agent = Agent(
    role='Vision Analyst',
    goal='Analyze images for item details',
    backstory="You specialize in computer vision for item evaluation.",
    llm="llava-13b-v1.6",  # Low-cost via OpenRouter
    verbose=True
)

research_agent = Agent(
    role='Market Researcher',
    goal='Scrape public sites for similar items and prices',
    backstory="You ethically scrape marketplaces for pricing data.",
    llm="meta-llama/llama-3.1-8b-instruct:free",
    verbose=True
)

pricing_agent = Agent(
    role='Pricing Expert',
    goal='Recommend price based on research and analysis',
    backstory="You calculate optimal selling prices.",
    llm="meta-llama/llama-3.1-8b-instruct:free",
    verbose=True
)

listing_agent = Agent(
    role='Listing Generator',
    goal='Create platform-specific listings',
    backstory="You format listings for eBay, Amazon, etc.",
    llm="meta-llama/llama-3.1-8b-instruct:free",
    verbose=True
)

@app.post("/crew")
async def run_crew(data: InputData):
    try:
        # Tasks
        vision_task = Task(
            description=f"Analyze images: {data.images} and summary: {data.summary}. Extract name, condition, damage, etc.",
            agent=vision_agent
        )

        research_task = Task(
            description=f"Research similar items for '{data.summary}' on eBay, Amazon, etc. Get prices.",
            agent=research_agent,
            context=[vision_task]  # Depends on vision
        )

        pricing_task = Task(
            description="Recommend price and check arbitrage opportunities.",
            agent=pricing_agent,
            context=[research_task]
        )

        listing_task = Task(
            description="Generate listings for Facebook Marketplace, eBay, Amazon. Output JSON and CSV.",
            agent=listing_agent,
            context=[pricing_task]
        )

        # Crew
        crew = Crew(
            agents=[vision_agent, research_agent, pricing_agent, listing_agent],
            tasks=[vision_task, research_task, pricing_task, listing_task],
            verbose=2
        )

        result = crew.kickoff()
        return {"analysis": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
