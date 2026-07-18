"""
routers/curriculum.py — API endpoints for curriculum upload and management.

POST /api/curriculum/upload
GET  /api/curriculum/files
"""
import os
import uuid
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
import fitz  # PyMuPDF
import docx
from agent.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/curriculum", tags=["curriculum"])

# ── Lazy singletons ──────────────────────────────────────────────────────────

_supabase = None
def get_supabase():
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
        if url and key:
            try:
                from supabase import create_client
                _supabase = create_client(url, key)
            except Exception as e:
                logger.warning(f"Supabase init failed: {e}")
    return _supabase

_embeddings = None
def get_embeddings():
    global _embeddings
    if _embeddings is None:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            _embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        except Exception as e:
            logger.warning(f"Embeddings init failed: {e}")
    return _embeddings

_qdrant = None
def get_qdrant():
    global _qdrant
    if _qdrant is None:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import VectorParams, Distance
            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            client = QdrantClient(url=url, timeout=3)
            
            # Ensure curriculum_chunks collection exists
            existing = {c.name for c in client.get_collections().collections}
            if "curriculum_chunks" not in existing:
                client.create_collection(
                    collection_name="curriculum_chunks",
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
                )
            _qdrant = client
        except Exception as e:
            logger.warning(f"Qdrant unavailable: {e}")
    return _qdrant


# ── Text Extraction ──────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text() + "\n\n"
        return text
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""

def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        from io import BytesIO
        doc = docx.Document(BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        return ""


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_curriculum(
    file: UploadFile = File(...),
    topic: str = Form(...),
    user = Depends(get_current_user)
):
    """
    Parses PDF/DOCX, splits into chunks, embeds, and upserts to Qdrant.
    Records file metadata in Supabase `curriculum_files` table.
    """
    sb = get_supabase()
    qdrant = get_qdrant()
    emb = get_embeddings()

    if not sb or not qdrant or not emb:
        raise HTTPException(status_code=503, detail="Database/Vector DB unavailable")

    contents = await file.read()
    filename = file.filename.lower()
    
    # 1. Extract text
    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(contents)
    elif filename.endswith(".docx"):
        text = extract_text_from_docx(contents)
    else:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    # 2. Chunking
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_text(text)

    if not chunks:
        raise HTTPException(status_code=400, detail="File resulted in 0 chunks")

    # 3. Create File Record in Supabase
    file_id = str(uuid.uuid4())
    try:
        # Seed topic if it doesn't exist
        topic_res = sb.table("topics").select("id").eq("name", topic).execute()
        if not topic_res.data:
            sb.table("topics").insert({"name": topic}).execute()

        sb.table("curriculum_files").insert({
            "id": file_id,
            "user_id": user.id,
            "filename": file.filename,
            "topic": topic,
            "chunk_count": len(chunks)
        }).execute()
    except Exception as e:
        logger.error(f"Failed to insert file record: {e}")
        raise HTTPException(status_code=500, detail="Failed to record file metadata")

    # 4. Embed & Upsert to Qdrant — skip re-embedding chunks whose exact text
    # was already indexed (e.g. re-uploading the same syllabus, or two files
    # sharing a boilerplate section). Point IDs are deterministic (uuid5 of
    # the chunk text), so a Qdrant retrieve-by-ID check is enough to know
    # what's already there without touching the embedding API.
    try:
        import hashlib
        from qdrant_client.models import PointStruct

        chunk_ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, hashlib.sha256(c.encode()).hexdigest())) for c in chunks]

        existing = qdrant.retrieve(collection_name="curriculum_chunks", ids=chunk_ids, with_vectors=False, with_payload=False)
        existing_ids = {str(p.id) for p in existing}

        to_embed_indices = [i for i, cid in enumerate(chunk_ids) if cid not in existing_ids]
        skipped = len(chunks) - len(to_embed_indices)
        if skipped:
            logger.info(f"Embedding cache: skipped {skipped}/{len(chunks)} chunk(s) already indexed with identical text")

        if to_embed_indices:
            new_vectors = await emb.aembed_documents([chunks[i] for i in to_embed_indices])
            points = [
                PointStruct(
                    id=chunk_ids[i],
                    vector=vector,
                    payload={
                        "file_id": file_id,
                        "user_id": user.id,
                        "filename": file.filename,
                        "topic": topic,
                        "page_content": chunks[i], # Keep schema matched with langchain QdrantVectorStore
                        "metadata": {               # which reads page_content and metadata
                            "topic": topic,
                            "filename": file.filename,
                            "chunk_index": i
                        }
                    }
                )
                for i, vector in zip(to_embed_indices, new_vectors)
            ]
            qdrant.upsert(collection_name="curriculum_chunks", points=points)
    except Exception as e:
        logger.error(f"Failed to upsert chunks: {e}")
        # Cleanup file record on failure
        sb.table("curriculum_files").delete().eq("id", file_id).execute()
        raise HTTPException(status_code=500, detail="Failed to store curriculum chunks")

    return {
        "success": True, 
        "file_id": file_id, 
        "filename": file.filename, 
        "chunks": len(chunks)
    }


@router.get("/files")
def list_curriculum_files(user = Depends(get_current_user)):
    """List all curriculum files uploaded by the user."""
    sb = get_supabase()
    if not sb:
        return {"files": []}
        
    try:
        res = sb.table("curriculum_files")\
                .select("*")\
                .eq("user_id", user.id)\
                .order("created_at", desc=True)\
                .execute()
        return {"files": res.data or []}
    except Exception as e:
        logger.error(f"Failed to list curriculum files: {e}")
        return {"files": []}
