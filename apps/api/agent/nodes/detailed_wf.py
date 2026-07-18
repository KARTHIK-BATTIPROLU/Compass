from agent.state import AppState
from agent.llm import get_llm
from agent.prompt_utils import trim_history, summary_preamble
from langchain_core.messages import SystemMessage
from langfuse import observe

@observe()
async def detailed_wf_node(state: AppState):
    llm = get_llm(temperature=0.2)

    user = state.get("user", {})
    role = user.get("role", "learner")
    class_level = state.get("class_level", "")
    weakness_ctx = state.get("weakness_ctx")
    curriculum_ctx = state.get("curriculum_ctx", [])

    # Build weakness injection for learners
    weakness_section = ""
    if role == "learner" and weakness_ctx:
        topics = weakness_ctx.get("identified_topics", [])
        if topics:
            weakness_section = (
                f"\n\nWEAK TOPICS FOR THIS LEARNER (target these in your explanation): "
                f"{', '.join(topics[:5])}\n"
                f"Ensure your explanation particularly addresses and reinforces these weak areas."
            )

    # Build curriculum context for faculty
    curriculum_section = ""
    if role == "faculty" and curriculum_ctx:
        ctx_str = "\n".join([c["content"][:300] for c in curriculum_ctx[:3]])
        curriculum_section = f"\n\nCURRICULUM CONTEXT:\n{ctx_str}"

    system_prompt = f"""You are LearnForge, an advanced AI learning assistant.
The user is a {role}. Class level: {class_level if class_level else 'not specified'}.
Provide a highly detailed, step-by-step, well-structured explanation. Use markdown headers, bullet points, and examples.{weakness_section}{curriculum_section}{summary_preamble(state.get("session_summary"))}"""

    messages = [SystemMessage(content=system_prompt)] + trim_history(state.get("messages", []))
    response = await llm.ainvoke(messages)

    return {"messages": [response]}
