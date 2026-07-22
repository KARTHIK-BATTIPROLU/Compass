import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agent.nodes.detailed_wf import detailed_wf_node
from langchain_core.messages import HumanMessage, AIMessage

@pytest.mark.asyncio
@patch("agent.nodes.detailed_wf.get_llm")
@patch("agent.nodes.detailed_wf.uuid.uuid4")
async def test_detailed_wf_node_success(mock_uuid, mock_get_llm):
    mock_uuid.return_value = "fake-uuid"
    
    # Setup mock LLM
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="<artifact type=\"detailed_explanation\">\nHere is a detailed explanation.\n</artifact>"))
    mock_get_llm.return_value = mock_llm
    
    # Input state
    state = {
        "user": {"role": "learner"},
        "class_level": "UG",
        "messages": [HumanMessage(content="Explain X")],
        "artifacts": []
    }
    
    # Run node
    result = await detailed_wf_node(state)
    
    # Assert LLM was called
    mock_get_llm.assert_called_once()
    mock_llm.ainvoke.assert_called_once()
    
    # Check messages output
    assert len(result["messages"]) == 1
    assert result["messages"][0].content == '<artifact type="detailed_explanation">\nHere is a detailed explanation.\n</artifact>'
    
    # Check artifacts output
    assert len(result["artifacts"]) == 1
    assert result["artifacts"][0]["id"] == "fake-uuid"
    assert result["artifacts"][0]["type"] == "detailed_explanation"
    assert "Here is a detailed explanation." in result["artifacts"][0]["content"]

@pytest.mark.asyncio
@patch("agent.nodes.detailed_wf.get_llm")
async def test_detailed_wf_node_degraded(mock_get_llm):
    # Setup mock LLM returning missing tag
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Here is a detailed explanation without tags."))
    mock_get_llm.return_value = mock_llm
    
    state = {
        "user": {"role": "learner"},
        "messages": [HumanMessage(content="Explain Y")]
    }
    
    result = await detailed_wf_node(state)
    
    # Should wrap in tag and add fallback notice
    content = result["messages"][0].content
    assert "<artifact type=\"detailed_explanation\">" in content
    assert "_Notice:" in content
    assert "Here is a detailed explanation without tags." in content

@pytest.mark.asyncio
@patch("agent.nodes.detailed_wf.get_llm")
async def test_detailed_wf_node_faculty_curriculum(mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="<artifact type=\"detailed_explanation\">Test</artifact>"))
    mock_get_llm.return_value = mock_llm
    
    state = {
        "user": {"role": "faculty"},
        "curriculum_ctx": [{"content": "Important context chunk"}],
        "messages": []
    }
    
    await detailed_wf_node(state)
    
    # Verify the system prompt included curriculum
    call_args = mock_llm.ainvoke.call_args[0][0]
    system_prompt = call_args[0].content
    assert "CURRICULUM CONTEXT:" in system_prompt
    assert "Important context chunk" in system_prompt

@pytest.mark.asyncio
@patch("agent.nodes.detailed_wf.get_llm")
async def test_detailed_wf_node_learner_weakness(mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="<artifact type=\"detailed_explanation\">Test</artifact>"))
    mock_get_llm.return_value = mock_llm
    
    state = {
        "user": {"role": "learner"},
        "weakness_ctx": {"identified_topics": ["Math", "Physics"]},
        "messages": []
    }
    
    await detailed_wf_node(state)
    
    call_args = mock_llm.ainvoke.call_args[0][0]
    system_prompt = call_args[0].content
    assert "WEAK TOPICS FOR THIS LEARNER" in system_prompt
    assert "Math, Physics" in system_prompt
