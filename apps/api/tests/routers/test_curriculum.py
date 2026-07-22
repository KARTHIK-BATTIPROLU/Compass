import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from routers.curriculum import router, get_current_user
import uuid

# Setup test app
app = FastAPI()
app.include_router(router)

# Mock user for dependency override
mock_user = MagicMock(id="test-user-id")
app.dependency_overrides[get_current_user] = lambda: mock_user

client = TestClient(app)

@pytest.fixture
def mock_dependencies():
    with patch("routers.curriculum.get_supabase") as mock_sb, \
         patch("routers.curriculum.get_qdrant") as mock_qdrant, \
         patch("routers.curriculum.get_embeddings") as mock_emb:
        
        sb_instance = MagicMock()
        mock_sb.return_value = sb_instance
        
        qdrant_instance = MagicMock()
        mock_qdrant.return_value = qdrant_instance
        
        emb_instance = AsyncMock()
        mock_emb.return_value = emb_instance
        
        yield sb_instance, qdrant_instance, emb_instance

def test_list_curriculum_files(mock_dependencies):
    sb, qdrant, emb = mock_dependencies
    
    # Setup Supabase response
    mock_data = [{"id": "1", "filename": "test.pdf"}]
    sb.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=mock_data)
    
    response = client.get("/api/curriculum/files")
    
    assert response.status_code == 200
    assert response.json() == {"files": mock_data}
    
    # Check if table called
    sb.table.assert_called_with("curriculum_files")

def test_upload_curriculum_invalid_ext(mock_dependencies):
    response = client.post(
        "/api/curriculum/upload",
        data={"topic": "Math"},
        files={"file": ("test.txt", b"Hello", "text/plain")}
    )
    
    assert response.status_code == 400
    assert "Only PDF and DOCX files are supported" in response.json()["detail"]

@patch("routers.curriculum.extract_text_from_pdf")
def test_upload_curriculum_pdf_success(mock_extract_pdf, mock_dependencies):
    sb, qdrant, emb = mock_dependencies
    
    mock_extract_pdf.return_value = "This is a test curriculum text that is long enough."
    
    # Mock qdrant retrieve to say nothing exists
    qdrant.retrieve.return_value = []
    
    # Mock embed documents
    emb.aembed_documents.return_value = [[0.1, 0.2]]
    
    response = client.post(
        "/api/curriculum/upload",
        data={"topic": "Math"},
        files={"file": ("test.pdf", b"fake pdf data", "application/pdf")}
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["filename"] == "test.pdf"
    assert res_data["chunks"] > 0
    
    # Check supabase inserts
    sb.table.assert_any_call("topics")
    sb.table.assert_any_call("curriculum_files")
    
    # Check qdrant upsert
    qdrant.upsert.assert_called_once()

@patch("routers.curriculum.extract_text_from_pdf")
def test_upload_curriculum_embedding_cache_hit(mock_extract_pdf, mock_dependencies):
    sb, qdrant, emb = mock_dependencies
    
    mock_extract_pdf.return_value = "This is a test curriculum text."
    
    # Mock qdrant retrieve to pretend the chunk is ALREADY there
    # the chunk_ids logic is deterministic so we just return a mock point that has an id
    mock_point = MagicMock()
    # we don't know the exact uuid, but retrieve returns existing points. 
    # we need the id to match what's generated. We can't easily guess it here, 
    # so we'll mock uuid5 to return a fixed id.
    with patch("routers.curriculum.uuid.uuid5", return_value=uuid.UUID("12345678-1234-5678-1234-567812345678")):
        mock_point.id = "12345678-1234-5678-1234-567812345678"
        qdrant.retrieve.return_value = [mock_point]
        
        response = client.post(
            "/api/curriculum/upload",
            data={"topic": "Math"},
            files={"file": ("test.pdf", b"fake pdf data", "application/pdf")}
        )
        
        assert response.status_code == 200
        
        # embed documents should NOT be called because cache hit
        emb.aembed_documents.assert_not_called()
        qdrant.upsert.assert_not_called()
