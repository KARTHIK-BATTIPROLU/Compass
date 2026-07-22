import pytest
import os
os.environ["SUPABASE_URL"] = "http://fake"
os.environ["SUPABASE_SERVICE_KEY"] = "fake"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from routers.quiz import router, get_current_user, user_owns_session

app = FastAPI()
app.include_router(router)

mock_user = MagicMock(id="test-user")
app.dependency_overrides[get_current_user] = lambda: mock_user
app.dependency_overrides[user_owns_session] = lambda user_id, session_id: True

client = TestClient(app)

@pytest.fixture
def mock_supabase():
    with patch("routers.quiz.supabase") as mock_sb:
        yield mock_sb

def test_get_quiz_success(mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "q1", "questions": []}])
    
    response = client.get("/api/quiz/token123")
    assert response.status_code == 200
    assert response.json()["id"] == "q1"

def test_get_quiz_not_found(mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    
    response = client.get("/api/quiz/token123")
    assert response.status_code == 404

def test_submit_quiz_success(mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[
        {"id": "q1", "artifacts": {"session_id": "s1"}}
    ])
    
    body = {
        "respondent_name": "Alice",
        "answers": {"q1": 0},
        "score": 100,
        "per_topic": {"Math": 100}
    }
    
    response = client.post("/api/quiz/token123/submit", json=body)
    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    
    # Assert insert into quiz_responses
    mock_supabase.table.assert_any_call("quiz_responses")

def test_submit_quiz_validation_error(mock_supabase):
    body = {
        "respondent_name": "", # Invalid
        "answers": {},
        "score": 0,
        "per_topic": {}
    }
    
    response = client.post("/api/quiz/token123/submit", json=body)
    assert response.status_code == 400

@patch("routers.quiz.user_owns_session", return_value=True)
def test_get_quiz_results_success(mock_owns, mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        MagicMock(data=[{"id": "db_q1", "artifacts": {"session_id": "s1"}}]), # quiz lookup
        MagicMock(data=[{"score": 100}]) # responses lookup
    ]
    
    response = client.get("/api/quiz/token123/results")
    assert response.status_code == 200
    assert response.json() == [{"score": 100}]

@patch("routers.quiz.user_owns_session", return_value=False)
def test_get_quiz_results_forbidden(mock_owns, mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "db_q1", "artifacts": {"session_id": "s1"}}]
    )
    
    response = client.get("/api/quiz/token123/results")
    assert response.status_code == 403
