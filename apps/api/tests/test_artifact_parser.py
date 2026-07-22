import pytest
from agent.artifact_parser import extract_json_payload, extract_artifact, generate_fallback_notice

def test_extract_json_payload_markdown():
    text = "Here is the data:\n```json\n{\"key\": \"value\"}\n```\nMore text."
    result = extract_json_payload(text)
    assert result == {"key": "value"}

def test_extract_json_payload_raw_braces():
    text = "No markdown, just raw { \"list\": [1, 2, 3] } right here."
    result = extract_json_payload(text)
    assert result == {"list": [1, 2, 3]}

def test_extract_json_payload_raw_brackets():
    text = "Array time: [{\"a\": 1}, {\"b\": 2}] is good."
    result = extract_json_payload(text)
    assert result == [{"a": 1}, {"b": 2}]

def test_extract_json_payload_invalid():
    text = "This is just a regular string with no JSON { broken "
    result = extract_json_payload(text)
    assert result is None

def test_extract_artifact_prose_with_tag():
    text = "Intro\n<artifact type=\"lecture_flow\">\n# Flow\n1. Start\n</artifact>\nOutro"
    wrapped, has_tag, degraded = extract_artifact(text, expected_type="lecture_flow", is_json_only=False)
    assert has_tag is True
    assert degraded is False
    assert wrapped == '<artifact type="lecture_flow">\n# Flow\n1. Start\n</artifact>'

def test_extract_artifact_prose_missing_tag():
    text = "# Flow\n1. Start\nNo tag here."
    wrapped, has_tag, degraded = extract_artifact(text, expected_type="lecture_flow", is_json_only=False)
    assert has_tag is False
    assert degraded is True
    assert wrapped == '<artifact type="lecture_flow">\n# Flow\n1. Start\nNo tag here.\n</artifact>'

def test_extract_artifact_json_only_valid():
    text = "```json\n{\"q\": \"a\"}\n```"
    wrapped, has_tag, degraded = extract_artifact(text, expected_type="quiz", is_json_only=True)
    assert has_tag is False
    assert degraded is False
    assert wrapped == '<artifact type="quiz">\n{"q": "a"}\n</artifact>'

def test_extract_artifact_json_only_with_unnecessary_tag():
    text = "<artifact type=\"quiz\">\n{\"q\": \"a\"}\n</artifact>"
    wrapped, has_tag, degraded = extract_artifact(text, expected_type="quiz", is_json_only=True)
    assert has_tag is True
    assert degraded is False
    assert wrapped == '<artifact type="quiz">\n{"q": "a"}\n</artifact>'

def test_extract_artifact_json_only_invalid():
    text = "I couldn't generate the JSON."
    wrapped, has_tag, degraded = extract_artifact(text, expected_type="quiz", is_json_only=True)
    assert wrapped is None
    assert degraded is True

def test_generate_fallback_notice():
    notice = generate_fallback_notice()
    assert "_Notice:" in notice
