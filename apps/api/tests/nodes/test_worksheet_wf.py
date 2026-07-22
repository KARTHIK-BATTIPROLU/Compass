import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agent.nodes.worksheet_wf import worksheet_wf_node
from langchain_core.messages import HumanMessage, AIMessage

@pytest.mark.asyncio
@patch("agent.nodes.worksheet_wf.get_llm")
@patch("agent.nodes.worksheet_wf.uuid.uuid4")
async def test_worksheet_wf_node_success(mock_uuid, mock_get_llm):
    mock_uuid.return_value = "worksheet-uuid"
    
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="<artifact type=\"worksheet\">\n## Student Worksheet\n</artifact>"))
    mock_get_llm.return_value = mock_llm
    
    state = {
        "class_level": "10th",
        "messages": [HumanMessage(content="Math Worksheet")],
        "artifacts": []
    }
    
    result = await worksheet_wf_node(state)
    
    assert mock_llm.ainvoke.call_count == 1
    
    assert len(result["artifacts"]) == 1
    assert result["artifacts"][0]["id"] == "worksheet-uuid"
    assert result["artifacts"][0]["type"] == "worksheet"
    assert "Student Worksheet" in result["artifacts"][0]["content"]

@pytest.mark.asyncio
@patch("agent.nodes.worksheet_wf.get_llm")
async def test_worksheet_wf_node_degraded(mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Here is a worksheet with no tags."))
    mock_get_llm.return_value = mock_llm
    
    state = {
        "messages": [HumanMessage(content="Math Worksheet")],
        "artifacts": []
    }
    
    result = await worksheet_wf_node(state)
    
    assert len(result["artifacts"]) == 1
    assert "_Notice:" in result["messages"][0].content
    assert "Here is a worksheet with no tags." in result["messages"][0].content
