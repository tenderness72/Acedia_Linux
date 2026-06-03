from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QThread, Signal

from ..models.paper import Paper
from ..services.doi_service import DoiMetadataService
from ..services.jstage_service import JStageMetadataService
from ..services.openAlex_service import OpenAlexMetadataService


class MetadataWorker(QThread):
    """Background thread that fetches metadata from DOI / J-Stage / OpenAlex."""

    finished = Signal(object)   # emits Paper | None
    error = Signal(str)

    def __init__(self, doi: str = "", title: str = "", parent=None):
        super().__init__(parent)
        self._doi = doi.strip()
        self._title = title.strip()

    def run(self):
        result: Optional[Paper] = None

        if self._doi:
            result = DoiMetadataService().fetch(self._doi)
            if result is None:
                result = JStageMetadataService().search_by_doi(self._doi)
            if result is None:
                result = OpenAlexMetadataService().fetch_by_doi(self._doi)

        if result is None and self._title:
            papers = JStageMetadataService().search_by_title(self._title, max_results=1)
            if papers:
                result = papers[0]
            else:
                papers = OpenAlexMetadataService().search_by_title(self._title, max_results=1)
                if papers:
                    result = papers[0]

        self.finished.emit(result)
