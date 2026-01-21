from __future__ import annotations

import pathlib
import subprocess
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from nexus.config import get_settings


class OCRError(Exception):
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type(subprocess.CalledProcessError),
    reraise=True,
)
def run_ocr(
    source: pathlib.Path, collection: str, relative_root: Optional[pathlib.Path] = None
) -> pathlib.Path:
    settings = get_settings()
    processed_root = settings.processed_dir / collection
    processed_root.mkdir(parents=True, exist_ok=True)
    rel_path: pathlib.Path
    if relative_root and source.is_absolute() and source.is_relative_to(relative_root):
        rel_path = source.relative_to(relative_root)
    else:
        rel_path = pathlib.Path(source.name)
    dest = processed_root / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ocrmypdf",
        "--skip-text",
        "--rotate-pages",
        "--deskew",
        "-j",
        "4",
        str(source),
        str(dest),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
    except subprocess.TimeoutExpired:
        raise OCRError(f"OCR timed out after 5 minutes for {source}")
    except subprocess.CalledProcessError as e:
        raise OCRError(f"OCR failed for {source}: {e.stderr.decode()[:200]}")
    return dest
