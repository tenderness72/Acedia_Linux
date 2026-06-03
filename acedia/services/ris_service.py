from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from ..models.paper import Paper

# RIS tag → field mapping
_TAG_MAP = {
    "TI": "title",
    "T1": "title",
    "CT": "title",
    "BT": "title",
    "AU": "authors",
    "A1": "authors",
    "A2": "authors",
    "JO": "journal",
    "JF": "journal",
    "JA": "journal",
    "T2": "journal",
    "PY": "year",
    "Y1": "year",
    "VL": "volume",
    "IS": "issue",
    "SP": "start_page",
    "EP": "end_page",
    "DO": "doi",
    "AB": "abstract",
    "N2": "abstract",
    "KW": "keywords",
    "TY": "paper_type",
    "N1": "additional_notes",
}


class RisImportService:
    def parse_file(self, path: str | Path) -> list[Paper]:
        text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
        return self.parse_text(text)

    def parse_text(self, text: str) -> list[Paper]:
        papers: list[Paper] = []
        current: dict[str, list[str]] = {}

        for line in text.splitlines():
            line = line.rstrip()
            if not line:
                continue

            if line.strip() == "ER":
                p = self._build_paper(current)
                if p.title or p.authors:
                    papers.append(p)
                current = {}
                continue

            m = re.match(r"^([A-Z][A-Z0-9])\s+-\s+(.*)", line)
            if m:
                tag, value = m.group(1), m.group(2).strip()
                field = _TAG_MAP.get(tag)
                if field:
                    current.setdefault(field, []).append(value)

        if current and (current.get("title") or current.get("authors")):
            papers.append(self._build_paper(current))

        return papers

    def _build_paper(self, d: dict[str, list[str]]) -> Paper:
        p = Paper()
        p.title = " ".join(d.get("title", []))
        p.authors = "，".join(d.get("authors", []))
        p.journal = " ".join(d.get("journal", []))
        p.volume = " ".join(d.get("volume", []))
        p.issue = " ".join(d.get("issue", []))
        p.doi = " ".join(d.get("doi", []))
        p.abstract = " ".join(d.get("abstract", []))
        p.additional_notes = "\n".join(d.get("additional_notes", []))

        kw_list = d.get("keywords", [])
        p.keywords = "，".join(kw_list)

        year_raw = " ".join(d.get("year", []))
        m = re.search(r"\d{4}", year_raw)
        p.year = int(m.group(0)) if m else None

        sp = " ".join(d.get("start_page", []))
        ep = " ".join(d.get("end_page", []))
        if sp and ep:
            p.pages = f"{sp}–{ep}"
        elif sp:
            p.pages = sp

        pt = " ".join(d.get("paper_type", []))
        p.paper_type = self._map_paper_type(pt)

        return p

    @staticmethod
    def _map_paper_type(ris_type: str) -> str:
        mapping = {
            "JOUR": "学術論文",
            "JFULL": "学術論文",
            "ABST": "抄録",
            "BOOK": "書籍",
            "CHAP": "書籍章",
            "CONF": "学会発表",
            "THES": "学位論文",
            "RPRT": "報告書",
        }
        return mapping.get(ris_type.upper(), ris_type)
