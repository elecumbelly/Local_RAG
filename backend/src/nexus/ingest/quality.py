from __future__ import annotations

from dataclasses import dataclass, field

from nexus.config import get_settings


@dataclass
class QualityReport:
    extracted_chars: int
    empty_page_ratio: float
    pages: list[dict] = field(default_factory=list)

    @property
    def needs_ocr(self) -> bool:
        settings = get_settings()
        return self.extracted_chars < settings.min_chars or self.empty_page_ratio > settings.max_empty_ratio
