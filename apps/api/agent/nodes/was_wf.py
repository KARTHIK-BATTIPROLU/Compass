from agent.state import AppState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langfuse import observe
import uuid
import json

@observe()
async def was_wf_node(state: AppState):
    """
    W-A-S (Weak → Average → Strong) workflow.

    Gate: requires lecture_flow to be set. If not, returns a guidance message
    and generates NO script (per spec: script blocked unless lecture_flow != None).

    Always generates a Presentation artifact.
    Generates a Script artifact ONLY when lecture_flow is present, ordered:
        WEAK   → basics-first, define every term
        AVERAGE → full picture, standard depth
        STRONG  → advanced extensions / challenge close
    """
    lecture_flow = state.get("lecture_flow")
    prompt = state.get("prompt", "")
    curriculum_ctx = state.get("curriculum_ctx", [])
    modes = [m.strip().lower() for m in state.get("modes", [])]
    is_detailed = "detailed" in modes

    ctx_str = "\n\n".join(
        [f"Topic: {c['metadata'].get('topic', 'N/A')}\n{c['content']}" for c in curriculum_ctx]
    )

    artifacts = list(state.get("artifacts", []))

    # ── Gate check ──────────────────────────────────────────────────────────
    if not lecture_flow or not lecture_flow.get("segments"):
        guidance = (
            "**W-A-S Script Blocked** — No Lecture Flow found for this session.\n\n"
            "Please run **Lecture Flow** first to generate the lesson structure. "
            "Once a flow is created, W-A-S will generate:\n"
            "- 🟢 **Presentation** (slides)\n"
            "- 📝 **Script** in WEAK → AVERAGE → STRONG order\n\n"
            "The W-A-S script is grounded in your Lecture Flow and curriculum, "
            "ensuring each section targets the right learner level."
        )
        from langchain_core.messages import AIMessage
        return {
            "messages": [AIMessage(content=guidance)],
            "artifacts": artifacts,
        }

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.3)

    # ── Build flow context ──────────────────────────────────────────────────
    flow_str = json.dumps(lecture_flow, indent=2)

    depth_instruction = (
        "Use EXTRA depth and detail — this is the [Detailed] + [W-A-S] combined mode."
        if is_detailed else
        "Use standard depth appropriate for the class level."
    )

    # ── 1. Generate Presentation (slides) ──────────────────────────────────
    slides_prompt = f"""You are LearnForge, creating a classroom presentation for a faculty member.

Topic: {prompt}
{depth_instruction}

LECTURE FLOW (use this structure for slides):
{flow_str}

CURRICULUM CONTEXT:
{ctx_str if ctx_str else "No specific curriculum chunks available."}

Generate a structured presentation as slides. Wrap your entire output in:
<artifact type="slides">
# [Title]

---
## Slide 1: [Opening Hook]
[Content]

---
## Slide 2: [Segment Title]
[Content with examples]

[... continue for each segment in the Lecture Flow ...]

---
## Slide N: Summary & Recap
[Key takeaways]
</artifact>"""

    slides_response = await llm.ainvoke([SystemMessage(content=slides_prompt)])
    slides_id = str(uuid.uuid4())
    artifacts.append({
        "id": slides_id,
        "type": "slides",
        "content": slides_response.content,
    })

    # ── 2. Generate Script (WEAK → AVERAGE → STRONG) ───────────────────────
    script_prompt = f"""You are LearnForge, generating a teaching script for a faculty member.

Topic: {prompt}
{depth_instruction}

LECTURE FLOW (your script MUST follow this segment order):
{flow_str}

CURRICULUM CONTEXT:
{ctx_str if ctx_str else "No specific curriculum chunks available."}

Generate a TEACHING SCRIPT with EXACTLY three sections, in this order:

<artifact type="script">
# Teaching Script: {prompt}

## 🟢 WEAK — Foundational Level
*Assume no prior knowledge. Define every term. Use simple analogies.*

[Script for students who are struggling — basics-first, approachable language, maximum scaffolding]

---

## 🟡 AVERAGE — Standard Level
*Full picture at class-appropriate depth. Build on the WEAK section.*

[Script for the majority of students — complete explanation, examples, standard rigor]

---

## 🔴 STRONG — Advanced Level
*Extensions, edge cases, challenge questions for advanced learners.*

[Script for advanced students — deeper theory, nuance, open questions]
</artifact>"""

    script_response = await llm.ainvoke([SystemMessage(content=script_prompt)])
    script_id = str(uuid.uuid4())
    artifacts.append({
        "id": script_id,
        "type": "script",
        "content": script_response.content,
    })

    # Combine both responses for the message stream
    combined = slides_response.content + "\n\n---\n\n" + script_response.content
    from langchain_core.messages import AIMessage
    return {
        "messages": [AIMessage(content=combined)],
        "artifacts": artifacts,
    }
