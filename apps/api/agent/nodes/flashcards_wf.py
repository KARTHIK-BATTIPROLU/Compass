from agent.state import AppState
from agent.llm import get_llm
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
Format your output EXACTLY as a JSON string inside `<artifact type="flashcards">...</artifact>`.
Schema:
<artifact type="flashcards">
{{
  "title": "Topic Name",
  "cards": [
    {{
      "front": "Question?",
      "back": "Answer."
    }}
  ]
}}
</artifact>
"""

    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])
    response = await llm.ainvoke(messages)
    
    artifacts = state.get("artifacts", [])
    response_text = response.text
    if "<artifact type=\"flashcards\">" in response_text:
        # Extract the JSON to build the APKG
        raw = response_text.split('<artifact type="flashcards">')[1].split('</artifact>')[0]
        try:
            data = json.loads(raw)
            filename = create_apkg(data.get("title", "LearnForge Deck"), data.get("cards", []))

            # Inject download link into the artifact payload
            data["download_url"] = f"/api/download/anki/{filename}"

            new_content = f'<artifact type="flashcards">\n{json.dumps(data)}\n</artifact>'
            response.content = new_content
        except Exception as e:
            logger.warning(f"Failed to generate Anki deck: {e}")
            new_content = response_text
            response.content = new_content

        artifacts.append({
            "id": str(uuid.uuid4()),
            "type": "flashcards",
            "content": new_content,
            "created_at": "now"
        })
        
    return {
        "messages": [response],
        "artifacts": artifacts
    }
