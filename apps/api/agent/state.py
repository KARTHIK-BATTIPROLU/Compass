from typing import TypedDict, Optional, List, Dict, Any, Annotated
from langgraph.graph.message import add_messages

class UserProfile(TypedDict):
    role: str
    region: Optional[str]
    language: Optional[str]
    standard: Optional[str]

class WeaknessProfile(TypedDict):
    identified_topics: List[str]

class Artifact(TypedDict):
    type: str
    content: str

class AppState(TypedDict):
    user: UserProfile
    session_id: str
    class_level: Optional[str]
    modes: List[str]
    prompt: str
    curriculum_ctx: List[Dict[str, Any]]
    weakness_ctx: Optional[WeaknessProfile]
    lecture_flow: Optional[Dict[str, Any]]
    artifacts: List[Artifact]
    topics_touched: List[str]
    citations: List[Dict[str, Any]]
    
    messages: Annotated[list, add_messages]
    route: str
