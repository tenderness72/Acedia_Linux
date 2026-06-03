from __future__ import annotations

import re
from typing import Optional

import httpx

from ..models.paper import Paper


class DoiMetadataService:
    _BASE = "https://api.crossref.org/works/"
    _TIMEOUT = 10.0

    def fetch(self, doi: str) -> Optional[Paper]:
        doi = doi.strip()
        if doi.startswith("http"):
            m = re.search(r"10\.\d{4,}/\S+", doi)
            if not m:
                return None
            doi = m.group(0)

        url = f"{self._BASE}{doi}"
        try:
            resp = httpx.get(url, timeout=self._TIMEOUT, headers={"User-Agent": "Acedia/1.0"})
            resp.raise_for_status()
            data = resp.json().get("message", {})
        except Exception:
            return None

        return self._parse(data, doi)

    def _parse(self, d: dict, doi: str) -> Paper:
        p = Paper()
        p.doi = doi

        titles = d.get("title", [])
        p.title = titles[0] if titles else ""

        authors_raw = d.get("author", [])
        author_names = []
        for a in authors_raw:
            family = a.get("family", "")
            given = a.get("given", "")
            if family and given:
                author_names.append(f"{family} {given}")
            elif family:
                author_names.append(family)
        p.authors = "，".join(author_names)

        container = d.get("container-title", [])
        p.journal = container[0] if container else ""

        issued = d.get("issued", {}).get("date-parts", [[]])
        if issued and issued[0]:
            p.year = issued[0][0]

        p.volume = d.get("volume", "")
        p.issue = d.get("issue", "")

        page = d.get("page", "")
        p.pages = page.replace("-", "–")

        abstract = d.get("abstract", "")
        p.abstract = re.sub(r"<[^>]+>", "", abstract).strip()

        return p
