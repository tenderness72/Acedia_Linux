from __future__ import annotations

from datetime import datetime
from typing import Optional

import re

from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload

from ..models.base import SessionLocal
from ..models.paper import Paper
from ..models.note import PaperNote


class PaperService:
    def _session(self) -> Session:
        return SessionLocal()

    # ── CRUD ───────────────────────────────────────────────────────────────────

    def get_all(self) -> list[Paper]:
        with self._session() as s:
            return s.query(Paper).order_by(Paper.updated_at.desc()).all()

    def get_by_id(self, paper_id: int) -> Optional[Paper]:
        with self._session() as s:
            return s.query(Paper).options(joinedload(Paper.notes)).filter(Paper.id == paper_id).first()

    def create(self, paper: Paper) -> Paper:
        with self._session() as s:
            now = datetime.now()
            paper.created_at = now
            paper.updated_at = now
            s.add(paper)
            s.commit()
            s.refresh(paper)
            return paper

    def update(self, paper: Paper) -> Paper:
        with self._session() as s:
            paper.updated_at = datetime.now()
            merged = s.merge(paper)
            s.commit()
            s.refresh(merged)
            return merged

    def delete(self, paper_id: int) -> None:
        with self._session() as s:
            p = s.query(Paper).filter(Paper.id == paper_id).first()
            if p:
                s.delete(p)
                s.commit()

    def toggle_favorite(self, paper_id: int) -> bool:
        with self._session() as s:
            p = s.query(Paper).filter(Paper.id == paper_id).first()
            if p:
                p.is_favorite = not p.is_favorite
                p.updated_at = datetime.now()
                s.commit()
                return p.is_favorite
            return False

    # ── Search & Filter ────────────────────────────────────────────────────────

    def search(
        self,
        query: str = "",
        year: Optional[int] = None,
        journal: str = "",
        tag: str = "",
        favorites_only: bool = False,
    ) -> list[Paper]:
        with self._session() as s:
            q = s.query(Paper)

            if query:
                like = f"%{query}%"
                q = q.filter(
                    or_(
                        Paper.title.ilike(like),
                        Paper.authors.ilike(like),
                        Paper.journal.ilike(like),
                        Paper.abstract.ilike(like),
                        Paper.keywords.ilike(like),
                        Paper.tags.ilike(like),
                        Paper.additional_notes.ilike(like),
                    )
                )

            if year is not None:
                q = q.filter(Paper.year == year)

            if journal:
                q = q.filter(Paper.journal.ilike(f"%{journal}%"))

            if tag:
                q = q.filter(Paper.tags.ilike(f"%{tag}%"))

            if favorites_only:
                q = q.filter(Paper.is_favorite == True)  # noqa: E712

            return q.order_by(Paper.updated_at.desc()).all()

    # ── Aggregates ─────────────────────────────────────────────────────────────

    def get_distinct_years(self) -> list[int]:
        with self._session() as s:
            rows = (
                s.query(Paper.year)
                .filter(Paper.year.isnot(None))
                .distinct()
                .order_by(Paper.year.desc())
                .all()
            )
            return [r[0] for r in rows]

    def get_distinct_journals(self) -> list[str]:
        with self._session() as s:
            rows = (
                s.query(Paper.journal)
                .filter(Paper.journal != "")
                .distinct()
                .order_by(Paper.journal)
                .all()
            )
            return [r[0] for r in rows]

    def get_all_tags(self) -> list[str]:
        with self._session() as s:
            rows = s.query(Paper.tags).filter(Paper.tags != "").all()
        tag_set: set[str] = set()
        for (raw,) in rows:
            for t in re.split(r"[,，、]+", raw):
                t = t.strip()
                if t:
                    tag_set.add(t)
        return sorted(tag_set)

    def count(self) -> int:
        with self._session() as s:
            return s.query(func.count(Paper.id)).scalar() or 0

    # ── Notes ──────────────────────────────────────────────────────────────────

    def get_notes(self, paper_id: int) -> list[PaperNote]:
        with self._session() as s:
            return (
                s.query(PaperNote)
                .filter(PaperNote.paper_id == paper_id)
                .order_by(PaperNote.created_at.asc())
                .all()
            )

    def create_note(self, note: PaperNote) -> PaperNote:
        with self._session() as s:
            now = datetime.now()
            note.created_at = now
            note.updated_at = now
            s.add(note)
            s.commit()
            s.refresh(note)
            return note

    def update_note(self, note: PaperNote) -> PaperNote:
        with self._session() as s:
            note.updated_at = datetime.now()
            merged = s.merge(note)
            s.commit()
            s.refresh(merged)
            return merged

    def delete_note(self, note_id: int) -> None:
        with self._session() as s:
            n = s.query(PaperNote).filter(PaperNote.id == note_id).first()
            if n:
                s.delete(n)
                s.commit()

    # ── Bulk import ────────────────────────────────────────────────────────────

    def bulk_create(self, papers: list[Paper]) -> list[Paper]:
        with self._session() as s:
            now = datetime.now()
            for p in papers:
                p.created_at = now
                p.updated_at = now
                s.add(p)
            s.commit()
            for p in papers:
                s.refresh(p)
            return papers
