from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.config import get_settings
from app.db.mongo_client import close_client, get_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    db = get_db()
    await db.users.create_index("email", unique=True)
    await db.weak_spots.create_index([("user_id", 1), ("concept", 1)])
    await db.generated_docs.create_index([("user_id", 1), ("created_at", -1)])
    print(f"Connected to MongoDB ({settings.mongodb_uri.split('@')[-1] if '@' in settings.mongodb_uri else 'local'})")
    yield
    await close_client()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AI Education Content Platform", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)

    # Late imports for agent routes (added in later phases)
    from app.sse.stream import router as agent_router
    from app.routes.student import router as student_router
    from app.routes.teacher import router as teacher_router

    app.include_router(agent_router)
    app.include_router(student_router)
    app.include_router(teacher_router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
