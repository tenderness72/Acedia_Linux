from __future__ import annotations

import re
from typing import Optional
from xml.etree import ElementTree as ET

import httpx

from ..models.paper import Paper


class JStageMetadataService:
    _BASE = "https://api.jstage.jst.go.jp/searchapi/do"
    _TIMEOUT = 10.0

    def search_by_title(self, title: str, max_results: int = 10) -> list[Paper]:
        params = {
            "service": "3",
            "text": title,
            "count": str(max_results),
            "lang": "0",
        }
        try:
            resp = httpx.get(self._BASE, params=params, timeout=self._TIMEOUT)
            resp.raise_for_status()
        except Exception:
            return []

        return self._parse_xml(resp.text)

    def search_by_doi(self, doi: str) -> Optional[Paper]:
        clean = doi.strip().lstrip("https://doi.org/")
        params = {"service": "3", "publ": clean, "count": "1"}
        try:
            resp = httpx.get(self._BASE, params=params, timeout=self._TIMEOUT)
            resp.raise_for_status()
        except Exception:
            return None

        papers = self._parse_xml(resp.text)
        return papers[0] if papers else None

    def _parse_xml(self, xml_text: str) -> list[Paper]:
        papers = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        ns = {
            "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
            "prism": "http://prismstandard.org/namespaces/basic/2.0/",
            "dc": "http://purl.org/dc/elements/1.1/",
        }

        for entry in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
            p = Paper()

            title_el = entry.find("{http://www.w3.org/2005/Atom}title")
            p.title = title_el.text.strip() if title_el is not None and title_el.text else ""

            authors = []
            for author_el in entry.findall("{http://www.w3.org/2005/Atom}author"):
                name_el = author_el.find("{http://www.w3.org/2005/Atom}name")
                if name_el is not None and name_el.text:
                    authors.append(name_el.text.strip())
            p.authors = "，".join(authors)

            journal_el = entry.find("{http://prismstandard.org/namespaces/basic/2.0/}publicationName")
            p.journal = journal_el.text.strip() if journal_el is not None and journal_el.text else ""

            year_el = entry.find("{http://prismstandard.org/namespaces/basic/2.0/}publicationDate")
            if year_el is not None and year_el.text:
                m = re.search(r"\d{4}", year_el.text)
                if m:
                    p.year = int(m.group(0))

            vol_el = entry.find("{http://prismstandard.org/namespaces/basic/2.0/}volume")
            p.volume = vol_el.text.strip() if vol_el is not None and vol_el.text else ""

            num_el = entry.find("{http://prismstandard.org/namespaces/basic/2.0/}number")
            p.issue = num_el.text.strip() if num_el is not None and num_el.text else ""

            sp_el = entry.find("{http://prismstandard.org/namespaces/basic/2.0/}startingPage")
            ep_el = entry.find("{http://prismstandard.org/namespaces/basic/2.0/}endingPage")
            sp = sp_el.text.strip() if sp_el is not None and sp_el.text else ""
            ep = ep_el.text.strip() if ep_el is not None and ep_el.text else ""
            if sp and ep:
                p.pages = f"{sp}–{ep}"
            elif sp:
                p.pages = sp

            doi_el = entry.find("{http://prismstandard.org/namespaces/basic/2.0/}doi")
            p.doi = doi_el.text.strip() if doi_el is not None and doi_el.text else ""

            papers.append(p)

        return papers
