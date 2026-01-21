from nexus.ingest.chunking import chunk_text


def test_chunking_overlap_respects_bounds():
    text = "a" * 100
    chunks = chunk_text(text, page=1)
    assert len(chunks) == 1
    idx, content, _ = chunks[0]
    assert len(content) <= 800
    assert idx == 0


def test_chunking_longer_text_splits():
    text = "a" * 1000
    chunks = chunk_text(text, page=1)
    assert len(chunks) > 1
