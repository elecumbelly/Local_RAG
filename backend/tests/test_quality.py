from nexus.ingest.quality import QualityReport


def test_quality_needs_ocr_based_on_thresholds(monkeypatch):
    monkeypatch.setenv("NEXUS_MIN_CHARS", "200")
    monkeypatch.setenv("NEXUS_MAX_EMPTY_RATIO", "0.3")
    report = QualityReport(extracted_chars=100, empty_page_ratio=0.1, pages=[])
    assert report.needs_ocr
