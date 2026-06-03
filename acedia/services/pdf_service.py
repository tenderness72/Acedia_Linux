from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from ..models.paper import Paper


class PdfMetadataService:
    def extract(self, path: str | Path) -> Optional[Paper]:
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return None

        path = Path(path)
        try:
            doc = fitz.open(str(path))
        except Exception:
            return None

        p = Paper()
        p.file_path = str(path)

        meta = doc.metadata or {}
        if meta.get("title"):
            p.title = meta["title"].strip()
        if meta.get("author"):
            raw = meta["author"].strip()
            p.authors = "，".join(a.strip() for a in re.split(r"[;,]", raw) if a.strip())

        if not p.title:
            p.title = path.stem

        text_pages = []
        for page_num in range(min(3, len(doc))):
            text_pages.append(doc[page_num].get_text())
        full_text = "\n".join(text_pages)

        if not p.title and full_text:
            lines = [l.strip() for l in full_text.splitlines() if l.strip()]
            if lines:
                p.title = lines[0][:200]

        doi_m = re.search(r"(?:doi[:\s]+|https?://doi\.org/)(10\.\d{4,}/\S+)", full_text, re.IGNORECASE)
        if doi_m:
            p.doi = doi_m.group(1).rstrip(".,)")

        year_m = re.search(r"\b(19|20)\d{2}\b", full_text)
        if year_m:
            p.year = int(year_m.group(0))

        doc.close()
        return p
