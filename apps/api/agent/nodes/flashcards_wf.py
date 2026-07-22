from agent.state import AppState
from agent.llm import get_llm
from agent.prompt_utils import trim_history, summary_preamble
from agent.artifact_parser import extract_artifact, generate_fallback_notice
from langchain_core.messages import SystemMessage
from langfuse import observe
import uuid
import json
import os
import genanki
import random
import logging

logger = logging.getLogger(__name__)

# Ensure download directory exists
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# Define Anki Model
anki_model = genanki.Model(
  1607392319,
  'LearnForge Model',
  fields=[
    {'name': 'Question'},
    {'name': 'Answer'},
  ],
  templates=[
    {
      'name': 'Card 1',
      'qfmt': '{{Question}}',
      'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
    },
  ])

def create_apkg(title: str, cards: list) -> str:
    """Generates an Anki package and returns the filename."""
    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(deck_id, title)
    
    for c in cards:
        note = genanki.Note(
            model=anki_model,
            fields=[c.get("front", ""), c.get("back", "")]
        )
        deck.add_note(note)
        
    pkg = genanki.Package(deck)
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.apkg"
    filepath = os.path.join(DOWNLOADS_DIR, filename)
    pkg.write_to_file(filepath)
    return filename

@observe()
async def flashcards_wf_node(state: AppState):
    llm = get_llm(temperature=0.2)
    prompt = state.get("prompt", "")
    class_level = state.get("class_level", "General")
    
    system_prompt = f"""You are LearnForge. Generate a set of 5 flashcards for {class_level} level based on the topic.
Format your output EXACTLY as a raw JSON string. Do not use wrapper tags.
Schema:
{{
  "title": "Topic Name",
  "cards": [
    {{
      "front": "Question?",
      "back": "Answer."
    }}
  ]
}}
{summary_preamble(state.get("session_summary"))}"""

    messages = [SystemMessage(content=system_prompt)] + trim_history(state.get("messages", []))
    response = await llm.ainvoke(messages)
    
    artifacts = state.get("artifacts", [])
    response_text = response.text
    
    wrapped_content, tag_present, degraded = extract_artifact(
        response_text, "flashcards", is_json_only=True, workflow_name="flashcards_wf"
    )
    
    if wrapped_content and not degraded:
        # Extract the inner JSON back out from our helper's wrapped format to build APKG
        raw = wrapped_content.split('<artifact type="flashcards">')[1].split('</artifact>')[0]
        try:
            data = json.loads(raw)
            filename = create_apkg(data.get("title", "LearnForge Deck"), data.get("cards", []))

            # Inject download link into the artifact payload
            data["download_url"] = f"/api/download/anki/{filename}"

            new_content = f'<artifact type="flashcards">\n{json.dumps(data)}\n</artifact>'
            response.content = new_content
            
            artifacts.append({
                "id": str(uuid.uuid4()),
                "type": "flashcards",
                "content": new_content,
                "created_at": "now"
            })
        except Exception as e:
            logger.warning(f"Failed to generate Anki deck: {e}")
            response.content = response_text + generate_fallback_notice()
    else:
        # Failed to extract JSON entirely
        response.content = response_text + generate_fallback_notice()
        
    return {
        "messages": [response],
        "artifacts": artifacts
    }

