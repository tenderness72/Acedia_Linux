import re
import unicodedata
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    authors: Mapped[str] = mapped_column(Text, nullable=False, default="")
    authors_kana: Mapped[str] = mapped_column(Text, nullable=False, default="")
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    journal: Mapped[str] = mapped_column(Text, nullable=False, default="")
    doi: Mapped[str] = mapped_column(Text, nullable=False, default="")
    volume: Mapped[str] = mapped_column(Text, nullable=False, default="")
    issue: Mapped[str] = mapped_column(Text, nullable=False, default="")
    pages: Mapped[str] = mapped_column(Text, nullable=False, default="")
    keywords: Mapped[str] = mapped_column(Text, nullable=False, default="")
    file_path: Mapped[str] = mapped_column(Text, nullable=False, default="")
    paper_type: Mapped[str] = mapped_column(Text, nullable=False, default="")
    clinical_area: Mapped[str] = mapped_column(Text, nullable=False, default="")
    approach: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="")
    abstract: Mapped[str] = mapped_column(Text, nullable=False, default="")
    additional_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    notes: Mapped[list["PaperNote"]] = relationship(  # noqa: F821
        "PaperNote", back_populates="paper", cascade="all, delete-orphan", lazy="select"
    )

    __table_args__ = (
        Index("ix_papers_title", "title"),
        Index("ix_papers_authors", "authors"),
        Index("ix_papers_year", "year"),
        Index("ix_papers_journal", "journal"),
    )

    # ── Parsed helpers ─────────────────────────────────────────────────────────

    @property
    def author_list(self) -> list[str]:
        if not self.authors:
            return []
        raw = re.split(r"[,，、;；\n]+", self.authors)
        return [a.strip() for a in raw if a.strip()]

    @property
    def tag_list(self) -> list[str]:
        if not self.tags:
            return []
        return [t.strip() for t in re.split(r"[,，、]+", self.tags) if t.strip()]

    @property
    def clinical_area_list(self) -> list[str]:
        if not self.clinical_area:
            return []
        return [c.strip() for c in re.split(r"[,，、]+", self.clinical_area) if c.strip()]

    @property
    def approach_list(self) -> list[str]:
        if not self.approach:
            return []
        return [a.strip() for a in re.split(r"[,，、]+", self.approach) if a.strip()]

    @property
    def has_japanese_authors(self) -> bool:
        return bool(re.search(r"[぀-ヿ一-鿿]", self.authors))

    @property
    def normalized_pages(self) -> str:
        return self.pages.replace("-", "–").replace("–", "–")

    @property
    def doi_url(self) -> str:
        if not self.doi:
            return ""
        d = self.doi.strip()
        if d.startswith("http"):
            return d
        return f"https://doi.org/{d}"

    @property
    def first_author_sort_key(self) -> str:
        parts = self.author_list
        if not parts:
            return ""
        first = parts[0]
        kana = self.authors_kana.strip() if self.authors_kana else ""
        if kana:
            return kana.split(",")[0].strip()
        return unicodedata.normalize("NFKC", first).lower()

    # ── J-APA citation ─────────────────────────────────────────────────────────

    def in_text_citation(self) -> str:
        authors = self.author_list
        year = str(self.year) if self.year else "年不明"
        if not authors:
            return f"（{year}）"
        if len(authors) == 1:
            a = self._format_author_short(authors[0])
            return f"{a}（{year}）"
        if len(authors) == 2:
            a1 = self._format_author_short(authors[0])
            a2 = self._format_author_short(authors[1])
            sep = "・" if self.has_japanese_authors else " & "
            return f"{a1}{sep}{a2}（{year}）"
        a1 = self._format_author_short(authors[0])
        et_al = "ら" if self.has_japanese_authors else " et al."
        return f"{a1}{et_al}（{year}）"

    def full_citation(self) -> str:
        authors = self.author_list
        year = str(self.year) if self.year else "年不明"
        pages = self.normalized_pages
        doi = self.doi_url

        if self.has_japanese_authors:
            author_str = self._format_authors_ja(authors)
            parts = [f"{author_str}（{year}）．{self.title}"]
            if self.journal:
                vol_issue = self._format_vol_issue()
                pg = f"，{pages}" if pages else ""
                parts[0] += f"　{self.journal}，{vol_issue}{pg}．"
            else:
                parts[0] += "．"
        else:
            author_str = self._format_authors_en(authors)
            parts = [f"{author_str} ({year}). {self.title}."]
            if self.journal:
                vol_issue = self._format_vol_issue()
                pg = f", {pages}" if pages else ""
                parts[0] += f" {self.journal}, {vol_issue}{pg}."

        if doi:
            parts.append(doi)
        return " ".join(parts)

    def _format_authors_ja(self, authors: list[str]) -> str:
        if not authors:
            return ""
        if len(authors) >= 21:
            listed = authors[:19]
            return "・".join(listed) + "・…・" + authors[-1]
        return "・".join(authors)

    def _format_authors_en(self, authors: list[str]) -> str:
        if not authors:
            return ""
        formatted = []
        for a in authors:
            parts = a.split()
            if len(parts) >= 2:
                last = parts[0]
                initials = "".join(p[0].upper() + "." for p in parts[1:])
                formatted.append(f"{last}, {initials}")
            else:
                formatted.append(a)
        if len(formatted) == 1:
            return formatted[0]
        if len(formatted) <= 20:
            return ", ".join(formatted[:-1]) + ", & " + formatted[-1]
        listed = ", ".join(formatted[:19])
        return f"{listed}, ... {formatted[-1]}"

    def _format_author_short(self, author: str) -> str:
        return author.split(",")[0].strip()

    def _format_vol_issue(self) -> str:
        if self.volume and self.issue:
            return f"{self.volume}（{self.issue}）"
        if self.volume:
            return self.volume
        return ""

    def __repr__(self) -> str:
        return f"<Paper id={self.id} title={self.title!r}>"
