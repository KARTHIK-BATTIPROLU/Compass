import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from routers.memory import router, get_current_user, user_owns_session

app = FastAPI()
app.include_router(router)

mock_user = MagicMock(id="test-user")
app.dependency_overrides[get_current_user] = lambda: mock_user
app.dependency_overrides[user_owns_session] = lambda user_id, session_id: True

client = TestClient(app)

@pytest.fixture
def mock_memory_utils():
    with patch("routers.memory.search_my_history", new_callable=AsyncMock) as mock_search, \
         patch("routers.memory.topics_in_session") as mock_topics, \
         patch("routers.memory.sessions_for_topic") as mock_sessions, \
         patch("routers.memory.get_weakness_profile") as mock_weakness, \
         patch("routers.memory.maybe_summarize_session", new_callable=AsyncMock) as mock_summary, \
         patch("agent.auth.get_supabase") as mock_sb:
             
         yield mock_search, mock_topics, mock_sessions, mock_weakness, mock_summary, mock_sb

def test_list_my_sessions(mock_memory_utils):
    _, _, _, _, mock_summary, mock_sb = mock_memory_utils
    
    sb_instance = MagicMock()
    # Mock returning 2 sessions
    sb_instance.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=[
        {"id": "s1", "title": "Math 101", "summary": None, "started_at": "2024-01-01", "class_level": "UG"},
        {"id": "s2", "title": "Bio 101", "summary": "Old summary", "started_at": "2024-01-02", "class_level": "UG"}
    ])
    mock_sb.return_value = sb_instance
    
    mock_summary.side_effect = ["New Summary", "Old summary"]
    
    response = client.get("/api/memory/sessions/mine")
    
    assert response.status_code == 200
    sessions = response.json()["sessions"]
    assert len(sessions) == 2
    assert sessions[0]["summary"] == "New Summary"
    assert sessions[1]["summary"] == "Old summary"
    
    assert mock_summary.call_count == 2

@patch("routers.memory.user_owns_session", return_value=True)
def test_get_topics_in_session(mock_owns, mock_memory_utils):
    _, mock_topics, _, _, _, _ = mock_memory_utils
    mock_topics.return_value = ["Math", "Physics"]
    
    response = client.get("/api/memory/topics/s1")
    assert response.status_code == 200
    assert response.json() == {"session_id": "s1", "topics": ["Math", "Physics"]}

@patch("routers.memory.user_owns_session", return_value=False)
def test_get_topics_in_session_forbidden(mock_owns, mock_memory_utils):
    response = client.get("/api/memory/topics/s1")
    assert response.status_code == 403

def test_get_sessions_for_topic(mock_memory_utils):
    _, _, mock_sessions, _, _, _ = mock_memory_utils
    mock_sessions.return_value = [{"session_id": "s1"}]
    
    response = client.get("/api/memory/sessions?topic=Math")
    assert response.status_code == 200
    assert response.json() == {"topic": "Math", "sessions": [{"session_id": "s1"}]}

def test_get_history(mock_memory_utils):
    mock_search, _, _, _, _, _ = mock_memory_utils
    mock_search.return_value = [{"content": "Result 1"}]
    
    response = client.get("/api/memory/history?q=query")
    assert response.status_code == 200
    assert response.json() == {"query": "query", "results": [{"content": "Result 1"}]}
    mock_search.assert_called_once_with("test-user", "query", 5)

def test_get_weakness(mock_memory_utils):
    _, _, _, mock_weakness, _, _ = mock_memory_utils
    mock_weakness.return_value = [{"topic": "Math", "mastery": 0.5}]
    
    response = client.get("/api/memory/weakness")
    assert response.status_code == 200
    assert response.json() == {"user_id": "test-user", "weakness": [{"topic": "Math", "mastery": 0.5}]}
