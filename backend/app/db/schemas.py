from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class WeakSpotDoc(BaseModel):
    user_id: str
    topic: str
    concept: str
    failure_count: int = 0
    last_attempt_correct: bool = False
    last_strategy: Optional[str] = None
    last_updated: datetime


class GeneratedDoc(BaseModel):
    user_id: str
    content_type: str
    content: dict[str, Any]
    status: str = "approved"  # draft | approved
    created_at: datetime
    updated_at: datetime


class ScrapedSource(BaseModel):
    url: str
    title: str = ""
    markdown: str = ""
    error: Optional[str] = None


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(default_factory=list)
    correct_answer: str
    difficulty: str = "medium"
    question_type: str = "mcq"  # mcq | short_answer


class QuizPayload(BaseModel):
    topic: str = ""
    questions: list[QuizQuestion]


class Slide(BaseModel):
    title: str
    bullet_points: list[str] = Field(default_factory=list)
    speaker_notes: str = ""
    visual_suggestion: str = ""


class SlidesPayload(BaseModel):
    topic: str = ""
    slides: list[Slide]


class DiagramPayload(BaseModel):
    topic: str = ""
    mermaid: str


class NotesPayload(BaseModel):
    topic: str = ""
    title: str = ""
    body: str = ""
    strategy: str = "text-based"
