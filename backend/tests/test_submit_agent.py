
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Since the file to be tested is in a different directory, we need to add the parent directory to the path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.agents import submit_agent

@pytest.mark.asyncio
@patch('core.agents.submit_agent.scrape_sites', new_callable=AsyncMock)
@patch('core.agents.submit_agent.chain.ainvoke', new_callable=AsyncMock)
@patch('core.agents.submit_agent.listing_chain.ainvoke', new_callable=AsyncMock)
@patch('core.agents.submit_agent.letta.agents.get')
async def test_process_submission_success(mock_letta_get, mock_listing_chain, mock_analysis_chain, mock_scrape_sites):
    # Arrange: Set up the mock return values
    mock_scrape_sites.return_value = {
        "similar": [("Fake Item 1", "$10.00"), ("Fake Item 2", "$12.00")],
        "avg_price": 11.00,
        "arbitrage": []
    }
    mock_analysis_chain.return_value = "This is a mock analysis."
    mock_listing_chain.return_value = "{'ebay': 'mock listing'}"

    # Mock the Letta agent and its methods
    mock_agent = MagicMock()
    mock_agent.messages.create = AsyncMock()
    mock_letta_get.return_value = mock_agent

    # Act: Call the function with test data
    result = await submit_agent.process_submission(
        images=["image1.jpg"],
        summary="A test summary",
        category="Electronics",
        condition="New"
    )

    # Assert: Check that the mocks were called and the result is as expected
    mock_scrape_sites.assert_called_once_with("A test summary")
    mock_analysis_chain.assert_called_once()
    mock_listing_chain.assert_called_once()
    mock_agent.messages.create.assert_called_once_with(content="This is a mock analysis.", role="assistant")

    assert result["analysis"] == "This is a mock analysis."
    assert result["listings"] == "{'ebay': 'mock listing'}"
    assert result["price"] == 11.00
    assert "Platform,Title,Desc,Price,Condition" in result["csv"]
    assert "ebay,AI Item,Generated desc,11.0,New" in result["csv"]
