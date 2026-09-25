import pytest
from app.ranker import chunk_text

def test_chunk_text():
    text = "word " * 450
    chunks = chunk_text(text, max_words=200)
    assert len(chunks) == 3
    assert len(chunks[0].split()) == 200
    assert len(chunks[2].split()) == 50
