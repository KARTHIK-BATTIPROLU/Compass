import pytest
from agent.prompt_utils import trim_history, summary_preamble

def test_trim_history_short():
    messages = ["m1", "m2", "m3"]
    result = trim_history(messages, max_turns=2)
    assert result == ["m1", "m2", "m3"]

def test_trim_history_long():
    messages = ["m1", "m2", "m3", "m4", "m5"]
    result = trim_history(messages, max_turns=2)
    assert result == ["m2", "m3", "m4", "m5"]

def test_trim_history_exact():
    messages = ["m1", "m2", "m3", "m4"]
    result = trim_history(messages, max_turns=2)
    assert result == ["m1", "m2", "m3", "m4"]

def test_summary_preamble_none():
    assert summary_preamble(None) == ""

def test_summary_preamble_empty():
    assert summary_preamble("") == ""

def test_summary_preamble_with_text():
    summary = "We discussed X."
    result = summary_preamble(summary)
    assert "EARLIER IN THIS SESSION (summary): We discussed X." in result
