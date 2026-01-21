from nexus.generate.validate import ensure_citations


def test_ensure_citations_appends_when_missing():
    assert ensure_citations("answer text", has_evidence=True).endswith("[1]")


def test_ensure_citations_noop_without_evidence():
    assert ensure_citations("answer text", has_evidence=False) == "answer text"
