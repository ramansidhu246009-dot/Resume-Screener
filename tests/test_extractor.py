import pytest
from app.extractor import normalize_text

def test_normalize_text():
    raw_text = "This   is \n a \t test."
    cleaned = normalize_text(raw_text)
    assert cleaned == "This is a test."
