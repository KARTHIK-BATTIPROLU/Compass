import re
import json
import logging
from typing import Tuple, Optional, Any

logger = logging.getLogger(__name__)

def extract_json_payload(text: str) -> Optional[dict | list]:
    """Extracts JSON from markdown fences or finds the first { or [."""
    # 1. Try markdown blocks
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        content = match.group(1).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

    # 2. Fallback: find first { or [ and last } or ]
    start_obj = text.find('{')
    start_arr = text.find('[')
    
    start = -1
    if start_obj != -1 and start_arr != -1:
        start = min(start_obj, start_arr)
    else:
        start = max(start_obj, start_arr)
        
    if start != -1:
        if text[start] == '{':
            end = text.rfind('}')
        else:
            end = text.rfind(']')
            
        if end != -1 and end >= start:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
                
    return None

def extract_artifact(
    text: str, 
    expected_type: str, 
    is_json_only: bool = False, 
    workflow_name: str = "unknown"
) -> Tuple[Optional[str], bool, bool]:
    """
    Extracts an artifact from LLM output.
    Returns (artifact_content, tag_present, degraded)
    
    If `is_json_only=True`, we don't expect a tag, just JSON.
    Returns JSON string wrapped in <artifact type="..."> if successful.
    
    If `is_json_only=False`, we expect <artifact type="...">.
    If tag is missing, we wrap the whole text as an artifact anyway.
    
    - artifact_content: The fully formed `<artifact type="...">...</artifact>` string, or None if extraction completely failed.
    - tag_present: True if the tag was explicitly in the output (always False if is_json_only).
    - degraded: True if we had to wrap prose because the tag was missing, or if JSON parsing failed.
    """
    
    # If it's a JSON-only workflow, we don't care about tags. We just extract JSON.
    if is_json_only:
        # Check if the model incorrectly added a tag anyway
        tag_pattern = rf'<artifact[^>]*type=["\']{expected_type}["\'][^>]*>(.*?)</artifact>'
        match = re.search(tag_pattern, text, re.DOTALL)
        content_to_parse = match.group(1) if match else text
        
        parsed = extract_json_payload(content_to_parse)
        if parsed is not None:
            wrapped = f'<artifact type="{expected_type}">\n{json.dumps(parsed)}\n</artifact>'
            return wrapped, bool(match), False
        else:
            logger.warning(f"[{workflow_name}] Intended JSON artifact but couldn't parse any JSON.")
            return None, bool(match), True
            
    # For prose/tagged workflows
    tag_pattern = rf'<artifact[^>]*type=["\']{expected_type}["\'][^>]*>(.*?)</artifact>'
    match = re.search(tag_pattern, text, re.DOTALL)
    
    if match:
        content = match.group(1).strip()
        wrapped = f'<artifact type="{expected_type}">\n{content}\n</artifact>'
        return wrapped, True, False
        
    # Tag is absent, wrap the whole cleaned text
    logger.warning(f"[{workflow_name}] Missing <artifact type=\"{expected_type}\"> tag. Degrading to wrapped prose.")
    # Remove any other random tags to be safe, but preserve text formatting
    cleaned = re.sub(r'</?artifact[^>]*>', '', text).strip()
    wrapped = f'<artifact type="{expected_type}">\n{cleaned}\n</artifact>'
    return wrapped, False, True

def generate_fallback_notice() -> str:
    return "\n\n_Notice: Couldn't structure that into a downloadable artifact — showing the raw response._"
