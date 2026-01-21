from __future__ import annotations

from dataclasses import dataclass
from typing import List

from pypdf import PdfReader


@dataclass
class PageText:
    page: int
    text: str


def extract_text(path: str) -> List[PageText]:
    reader = PdfReader(path)
    pages: list[PageText] = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append(PageText(page=idx + 1, text=text))
    return pages
