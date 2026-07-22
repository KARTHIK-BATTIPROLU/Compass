import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agent.nodes.context_loader import context_loader_node

@pytest.mark.asyncio
@patch("agent.nodes.context_loader.get_supabase")
@patch("agent.nodes.context_loader.get_vector_store")
async def test_context_loader_node_learner_success(mock_vs, mock_get_supabase):
    mock_sb = MagicMock()
    # Mock session
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        MagicMock(data=[{"user_id": "u1", "class_level": "UG", "summary": "test"}]),
        MagicMock(data=[{"role": "learner", "region": "US"}]),
        MagicMock(data=[{"topic_id": "Math"}])  # weakness
    ]
    mock_get_supabase.return_value = mock_sb
    mock_vs.return_value = None
    
    state = {
        "session_id": "s1",
        "prompt": "Test",
        "jwt": "fake"
    }
    
    result = await context_loader_node(state)
    
    assert result["user"]["role"] == "learner"
    assert result["class_level"] == "UG"
    assert result["session_summary"] == "test"
    assert "Math" in result["weakness_ctx"]["identified_topics"]
    assert result["curriculum_ctx"] == [] # Learner shouldn't retrieve curriculum

@pytest.mark.asyncio
@patch("agent.nodes.context_loader.get_supabase")
@patch("agent.nodes.context_loader.get_vector_store")
async def test_context_loader_node_faculty_success(mock_vs, mock_get_supabase):
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        MagicMock(data=[{"user_id": "u2", "class_level": "10th"}]),
        MagicMock(data=[{"role": "faculty"}])
    ]
    mock_get_supabase.return_value = mock_sb
    
    # Mock Vector Store
    mock_vs_instance = AsyncMock()
    mock_doc = MagicMock(page_content="Curriculum content", metadata={"topic": "Bio"})
    mock_vs_instance.asimilarity_search.return_value = [mock_doc]
    mock_vs.return_value = mock_vs_instance
    
    state = {
        "session_id": "s2",
        "prompt": "Test prompt"
    }
    
    result = await context_loader_node(state)
    
    assert result["user"]["role"] == "faculty"
    assert len(result["curriculum_ctx"]) == 1
    assert result["curriculum_ctx"][0]["content"] == "Curriculum content"
    
    # Check that filter was applied
    call_args = mock_vs_instance.asimilarity_search.call_args[1]
    assert "filter" in call_args
    assert call_args["filter"].must[0].key == "user_id"
    assert call_args["filter"].must[0].match.value == "u2"

@pytest.mark.asyncio
@patch("agent.nodes.context_loader.get_supabase")
async def test_context_loader_node_no_supabase(mock_get_supabase):
    mock_get_supabase.return_value = None
    
    state = {
        "session_id": "s3",
        "prompt": "Test"
    }
    
    result = await context_loader_node(state)
    
    assert result["user"] == {}
    assert result["class_level"] is None
    assert result["curriculum_ctx"] == []
    assert result["weakness_ctx"] is None
    assert result["session_summary"] is None
