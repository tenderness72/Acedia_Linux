import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

_data_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "acedia"
_data_dir.mkdir(parents=True, exist_ok=True)
DB_PATH = _data_dir / "papers.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

@event.listens_for(engine, "connect")
def _set_sqlite_pragma(conn, _):
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db():
    Base.metadata.create_all(bind=engine)
