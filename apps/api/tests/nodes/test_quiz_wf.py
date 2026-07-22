import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from agent.nodes.quiz_wf import quiz_wf_node
from langchain_core.messages import HumanMessage, AIMessage

@pytest.fixture
def mock_quiz_json():
    return json.dumps({
        "title": "Test Quiz",
        "questions": [
            {
                "id": "q1",
                "topic": "test",
                "text": "Q?",
                "options": ["A", "B", "C", "D"],
                "correctAnswer": 0,
                "explanation": "Because."
            }
        ]
    })

@pytest.mark.asyncio
@patch("agent.nodes.quiz_wf.get_fast_llm")
@patch("agent.nodes.quiz_wf.uuid.uuid4")
@patch("agent.nodes.quiz_wf.get_supabase")
async def test_quiz_wf_node_faculty_success(mock_get_supabase, mock_uuid, mock_get_llm, mock_quiz_json):
    # Setup UUIDs - first is art_id, second is token
    mock_uuid.side_effect = ["art-uuid", "token-uuid"]
    
    # Setup LLM
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content=mock_quiz_json))
    mock_get_llm.return_value = mock_llm
    
    # Setup Supabase
    mock_sb = MagicMock()
    mock_get_supabase.return_value = mock_sb
    
    state = {
        "user": {"role": "faculty"},
        "session_id": "sess-uuid",
        "messages": [HumanMessage(content="Make a quiz")],
        "artifacts": [],
        "jwt": "fake-jwt"
    }
    
    result = await quiz_wf_node(state)
    
    # Supabase checks
    mock_get_supabase.assert_called_once_with(jwt="fake-jwt")
    mock_sb.table.assert_any_call("artifacts")
    mock_sb.table.assert_any_call("quizzes")
    
    # Output checks
    assert len(result["artifacts"]) == 1
    assert result["artifacts"][0]["id"] == "art-uuid"
    assert 'type="quiz_link"' in result["artifacts"][0]["content"]
    assert 'token="token-uuid"' in result["artifacts"][0]["content"]
    assert result["messages"][0].content == result["artifacts"][0]["content"]

@pytest.mark.asyncio
@patch("agent.nodes.quiz_wf.get_fast_llm")
@patch("agent.nodes.quiz_wf.uuid.uuid4")
async def test_quiz_wf_node_learner_success(mock_uuid, mock_get_llm, mock_quiz_json):
    mock_uuid.return_value = "art-uuid"
    
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content=mock_quiz_json))
    mock_get_llm.return_value = mock_llm
    
    state = {
        "user": {"role": "learner"},
        "messages": [HumanMessage(content="Make a quiz")],
        "artifacts": []
    }
    
    result = await quiz_wf_node(state)
    
    # Learner quiz shouldn't hit Supabase or create a token
    assert mock_uuid.call_count == 1
    
    assert len(result["artifacts"]) == 1
    assert result["artifacts"][0]["id"] == "art-uuid"
    assert 'type="learner_quiz"' in result["artifacts"][0]["content"]

@pytest.mark.asyncio
@patch("agent.nodes.quiz_wf.get_fast_llm")
async def test_quiz_wf_node_invalid_json(mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="I cannot make a quiz."))
    mock_get_llm.return_value = mock_llm
    
    state = {
        "user": {"role": "learner"},
        "messages": [HumanMessage(content="Make a quiz")],
        "artifacts": []
    }
    
    result = await quiz_wf_node(state)
    
    # Should gracefully degrade
    assert len(result["artifacts"]) == 0
    assert "_Notice:" in result["messages"][0].content
    assert "I cannot make a quiz." in result["messages"][0].content
