from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from lib.scraper import scrapeSimilarItems, findArbitrage  # Import from shared lib if possible, or duplicate logic
import os

# LLM setup (reuse from submit_agent.py)
llm = ChatOpenAI(
    model="meta-llama/llama-3.1-8b-instruct:free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0.3,
)

# Agent 1: Scraper Agent - Gathers data from platforms
scraper_agent = Agent(
    role="Market Scraper",
    goal="Scrape similar items from eBay, Amazon, FB Marketplace for given query and identify potential arbitrage opportunities.",
    backstory="You are an expert web scraper specializing in e-commerce sites. You respect rate limits and use ethical practices.",
    verbose=True,
    allow_delegation=False,
    llm=llm,
    tools=[scrapeSimilarItems, findArbitrage],
)

# Agent 2: Analyzer Agent - Analyzes scraped data for arbitrage
analyzer_agent = Agent(
    role="Arbitrage Analyzer",
    goal="Analyze scraped data to flag items priced <70% of average, calculate profit margins, and recommend actions.",
    backstory="You are a financial analyst for e-commerce arbitrage. You calculate margins, risks, and actionable insights from market data.",
    verbose=True,
    allow_delegation=False,
    llm=llm,
)

# Task 1: Scrape for opportunities
scrape_task = Task(
    description="Scrape {query} across platforms and return similar items with prices.",
    expected_output="List of similar items with site, title, price, and average price calculation.",
    agent=scraper_agent,
)

# Task 2: Analyze for arbitrage
analyze_task = Task(
    description="Analyze {scraped_data} to identify arbitrage opportunities (price < 70% avg). Output JSON with opportunities, estimated margins, and recommendations.",
    expected_output="JSON array of opportunities with platform, item, current_price, avg_price, margin_pct, and action (buy/sell).",
    agent=analyzer_agent,
    context=[scrape_task],
)

# Crew orchestration
arbitrage_crew = Crew(
    agents=[scraper_agent, analyzer_agent],
    tasks=[scrape_task, analyze_task],
    verbose=2,
)

async def run_arbitrage_crew(query: str):
    """
    Run the arbitrage crew for a given query.
    Returns crew results with opportunities.
    """
    result = await arbitrage_crew.kickoff(inputs={"query": query})
    return result