from __future__ import annotations


def ensure_citations(answer: str, has_evidence: bool) -> str:
    if has_evidence and "[" not in answer:
        return answer + " [1]"
    return answer
