from __future__ import annotations

import re
from typing import Optional

import httpx

from ..models.paper import Paper


class OpenAlexMetadataService:
    _BASE = "https://api.openalex.org/works"
    _TIMEOUT = 10.0

    def fetch_by_doi(self, doi: str) -> Optional[Paper]:
        doi = doi.strip()
        if doi.startswith("http"):
            m = re.search(r"10\.\d{4,}/\S+", doi)
            doi = m.group(0) if m else doi

        url = f"{self._BASE}/https://doi.org/{doi}"
        try:
            resp = httpx.get(url, timeout=self._TIMEOUT, headers={"User-Agent": "Acedia/1.0"})
            resp.raise_for_status()
            return self._parse(resp.json(), doi)
        except Exception:
            return None

    def search_by_title(self, title: str, max_results: int = 5) -> list[Paper]:
        params = {
            "filter": f"title.search:{title}",
            "per-page": str(max_results),
            "select": "id,title,authorships,publication_year,primary_location,doi,abstract_inverted_index,biblio",
        }
        try:
            resp = httpx.get(self._BASE, params=params, timeout=self._TIMEOUT, headers={"User-Agent": "Acedia/1.0"})
            resp.raise_for_status()
            results = resp.json().get("results", [])
            return [self._parse(r, r.get("doi", "")) for r in results]
        except Exception:
            return []

    def _parse(self, d: dict, doi: str) -> Paper:
        p = Paper()
        p.doi = doi.replace("https://doi.org/", "")
        p.title = d.get("display_name", "") or d.get("title", "")

        authorships = d.get("authorships", [])
        names = []
        for auth in authorships:
            name = auth.get("author", {}).get("display_name", "")
            if name:
                names.append(name)
        p.authors = "，".join(names)

        year = d.get("publication_year")
        p.year = int(year) if year else None

        source = d.get("primary_location", {}).get("source") or {}
        p.journal = source.get("display_name", "")

        biblio = d.get("biblio", {})
        p.volume = biblio.get("volume", "") or ""
        p.issue = biblio.get("issue", "") or ""
        first = biblio.get("first_page", "") or ""
        last = biblio.get("last_page", "") or ""
        p.pages = f"{first}–{last}" if first and last else first

        inv_idx = d.get("abstract_inverted_index", {})
        if inv_idx:
            p.abstract = self._reconstruct_abstract(inv_idx)

        return p

    @staticmethod
    def _reconstruct_abstract(inv: dict) -> str:
        max_pos = max((pos for positions in inv.values() for pos in positions), default=-1)
        if max_pos < 0:
            return ""
        words = [""] * (max_pos + 1)
        for word, positions in inv.items():
            for pos in positions:
                words[pos] = word
        return " ".join(w for w in words if w)
