import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agent.nodes.was_wf import was_wf_node
from langchain_core.messages import AIMessage

@pytest.mark.asyncio
async def test_was_wf_node_blocked():
    # If no lecture_flow, should return a guidance message and no artifacts
    state = {
        "artifacts": []
    }
    
    result = await was_wf_node(state)
    
    assert len(result["artifacts"]) == 0
    assert "W-A-S Script Blocked" in result["messages"][0].content
    assert "Please run **Lecture Flow** first" in result["messages"][0].content

@pytest.mark.asyncio
@patch("agent.nodes.was_wf.get_llm")
@patch("agent.nodes.was_wf.uuid.uuid4")
async def test_was_wf_node_success(mock_uuid, mock_get_llm):
    mock_uuid.side_effect = ["slides-uuid", "script-uuid"]
    
    mock_llm = AsyncMock()
    # It will be called twice (gather), so we can just return a generic AIMessage or side_effect
    mock_llm.ainvoke.side_effect = [
        AIMessage(content="<artifact type=\"slides\">\nSlides\n</artifact>"),
        AIMessage(content="<artifact type=\"script\">\nScript\n</artifact>")
    ]
    mock_get_llm.return_value = mock_llm
    
    state = {
        "lecture_flow": {"segments": [{"title": "Intro"}]},
        "prompt": "Test",
        "modes": ["detailed"],
        "artifacts": []
    }
    
    result = await was_wf_node(state)
    
    assert mock_llm.ainvoke.call_count == 2
    
    assert len(result["artifacts"]) == 2
    
    # Check Slides
    assert result["artifacts"][0]["id"] == "slides-uuid"
    assert result["artifacts"][0]["type"] == "slides"
    assert "Slides" in result["artifacts"][0]["content"]
    
    # Check Script
    assert result["artifacts"][1]["id"] == "script-uuid"
    assert result["artifacts"][1]["type"] == "script"
    assert "Script" in result["artifacts"][1]["content"]
    
    # Combined message
    assert "Slides" in result["messages"][0].content
    assert "Script" in result["messages"][0].content

@pytest.mark.asyncio
@patch("agent.nodes.was_wf.get_llm")
async def test_was_wf_node_degraded(mock_get_llm):
    mock_llm = AsyncMock()
    mock_llm.ainvoke.side_effect = [
        AIMessage(content="Slides without tag"),
        AIMessage(content="Script without tag")
    ]
    mock_get_llm.return_value = mock_llm
    
    state = {
        "lecture_flow": {"segments": [{"title": "Intro"}]},
        "artifacts": []
    }
    
    result = await was_wf_node(state)
    
    assert len(result["artifacts"]) == 2
    assert "_Notice:" in result["artifacts"][0]["content"]
    assert "_Notice:" in result["artifacts"][1]["content"]
