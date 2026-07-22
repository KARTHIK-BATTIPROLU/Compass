import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from agent.nodes.lecture_wf import lecture_wf_node
from langchain_core.messages import AIMessage

@pytest.fixture
def mock_flow_json():
    return json.dumps({
        "topic": "Photosynthesis",
        "class_level": "9th",
        "hook": "Ever wonder how plants eat?",
        "segments": [
            {
                "title": "Light Reactions",
                "objective": "Understand sunlight capture",
                "example": "Like solar panels",
                "timing_minutes": 15
            }
        ],
        "close": "Plants are amazing."
    })

@pytest.mark.asyncio
@patch("agent.nodes.lecture_wf.get_llm")
@patch("agent.nodes.lecture_wf.uuid.uuid4")
async def test_lecture_wf_node_success(mock_uuid, mock_get_llm, mock_flow_json):
    mock_uuid.return_value = "flow-uuid"
    
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content=mock_flow_json))
    mock_get_llm.return_value = mock_llm
    
    state = {
        "prompt": "Photosynthesis",
        "class_level": "9th",
        "curriculum_ctx": [{"metadata": {"topic": "Bio"}, "content": "Bio 101"}],
        "artifacts": []
    }
    
    result = await lecture_wf_node(state)
    
    # Check that it returns structured lecture_flow in state
    assert "lecture_flow" in result
    flow = result["lecture_flow"]
    assert flow["topic"] == "Photosynthesis"
    assert flow["hook"] == "Ever wonder how plants eat?"
    
    # Check that it builds the markdown artifact
    assert len(result["artifacts"]) == 1
    artifact = result["artifacts"][0]
    assert artifact["id"] == "flow-uuid"
    assert artifact["type"] == "flow"
    
    # Verify the markdown includes our json values
    content = artifact["content"]
    assert "<artifact type=\"flow\">" in content
    assert "## 🎣 Opening Hook" in content
    assert "Ever wonder how plants eat?" in content
    
    # The message content should be identical to the artifact content
    assert result["messages"][0].content == content

@pytest.mark.asyncio
@patch("agent.nodes.lecture_wf.get_llm")
async def test_lecture_wf_node_degraded(mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="I can't format this as JSON."))
    mock_get_llm.return_value = mock_llm
    
    state = {
        "prompt": "Photosynthesis",
        "artifacts": []
    }
    
    result = await lecture_wf_node(state)
    
    # Should fall back gracefully
    assert "lecture_flow" in result
    flow = result["lecture_flow"]
    # Check that it provides the fallback dict
    assert flow["topic"] == "Photosynthesis"
    
    # Should not produce an artifact, but should append fallback notice to message
    assert len(result["artifacts"]) == 0
    assert "_Notice:" in result["messages"][0].content
    assert "I can't format this as JSON." in result["messages"][0].content
