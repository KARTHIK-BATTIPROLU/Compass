from agent.state import AppState
from langfuse import observe

@observe()
async def composer_node(state: AppState):
    return {}
