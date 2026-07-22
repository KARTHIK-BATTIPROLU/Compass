import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from agent.nodes.research_wf import research_wf_node
from langchain_core.messages import HumanMessage, AIMessage

@pytest.fixture
def mock_research_json():
    return json.dumps({
        "title": "Brief",
        "brief_markdown": "Markdown",
        "citations": [
            {"id": "1", "title": "A", "url": "http://a"}
        ]
    })

@pytest.mark.asyncio
@patch("agent.nodes.research_wf.get_llm")
@patch("agent.nodes.research_wf.uuid.uuid4")
@patch("agent.nodes.research_wf.search_web")
@patch("agent.nodes.research_wf.search_arxiv")
@patch("agent.nodes.research_wf.search_semantic_scholar")
async def test_research_wf_node_success(mock_scholar, mock_arxiv, mock_web, mock_uuid, mock_get_llm, mock_research_json):
    mock_uuid.return_value = "research-uuid"
    
    mock_web.return_value = [{"title": "Web", "url": "web.url", "content": "web content"}]
    mock_arxiv.return_value = [{"title": "Arxiv", "url": "arxiv.url", "content": "arxiv content"}]
    mock_scholar.return_value = [{"title": "Scholar", "url": "scholar.url", "content": "scholar content"}]
    
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content=f"<artifact type=\"research_brief\">\n{mock_research_json}\n</artifact>"))
    mock_get_llm.return_value = mock_llm
    
    state = {
        "prompt": "Test Prompt",
        "class_level": "UG",
        "messages": [HumanMessage(content="Test Prompt")],
        "artifacts": []
    }
    
    result = await research_wf_node(state)
    
    mock_web.assert_called_once_with("Test Prompt")
    mock_arxiv.assert_called_once_with("Test Prompt")
    mock_scholar.assert_called_once_with("Test Prompt")
    
    assert len(result["artifacts"]) == 1
    assert result["artifacts"][0]["id"] == "research-uuid"
    assert result["artifacts"][0]["type"] == "research_brief"
    assert "Brief" in result["artifacts"][0]["content"]

@pytest.mark.asyncio
@patch("agent.nodes.research_wf.get_llm")
@patch("agent.nodes.research_wf.search_web")
@patch("agent.nodes.research_wf.search_arxiv")
@patch("agent.nodes.research_wf.search_semantic_scholar")
async def test_research_wf_node_degraded(mock_scholar, mock_arxiv, mock_web, mock_get_llm):
    mock_web.return_value = []
    mock_arxiv.return_value = []
    mock_scholar.return_value = []
    
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="I can't format this."))
    mock_get_llm.return_value = mock_llm
    
    state = {
        "prompt": "Test Prompt",
        "messages": [HumanMessage(content="Test Prompt")],
        "artifacts": []
    }
    
    result = await research_wf_node(state)
    
    assert len(result["artifacts"]) == 1
    assert "_Notice:" in result["messages"][0].content
    assert "I can't format this." in result["messages"][0].content
