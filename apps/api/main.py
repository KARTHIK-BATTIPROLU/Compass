import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from langfuse.decorators import observe
from langchain_core.messages import HumanMessage
from agent.graph import graph
from routers import messages, health, quiz

app = FastAPI(title="LearnForge API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

app.include_router(messages.router)
app.include_router(health.router)
app.include_router(quiz.router)

async def dummy_token_generator():
    tokens = ["Hello, ", "this ", "is ", "a ", "streaming ", "test ", "from ", "the ", "agent!"]
    for token in tokens:
        yield f"data: {token}\n\n"
        await asyncio.sleep(0.3)

@app.get("/api/test/stream")
def test_stream():
    return StreamingResponse(dummy_token_generator(), media_type="text/event-stream")

@observe()
def dummy_llm_call():
    # This is a dummy function to confirm Langfuse tracing works.
    return "This is a traced dummy call."

@app.get("/api/test/trace")
def test_trace():
    result = dummy_llm_call()
    return {"result": result, "message": "Check Langfuse dashboard to confirm the trace appeared!"}

class ChatRequest(BaseModel):
    session_id: str
    prompt: str
    modes: List[str] = []

@app.post("/api/chat/stream")
async def chat_stream(req: Request, chat_req: ChatRequest):
    async def event_generator():
        inputs = {
            "session_id": chat_req.session_id,
            "prompt": chat_req.prompt,
            "modes": chat_req.modes,
            "messages": [HumanMessage(content=chat_req.prompt)]
        }
        
        try:
            async for event in graph.astream_events(inputs, version="v2"):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        yield f"data: {json.dumps({'content': chunk.content})}\n\n"
        except Exception as e:
            print("Graph execution error:", e)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    
        yield "data: [DONE]\n\n"
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")
