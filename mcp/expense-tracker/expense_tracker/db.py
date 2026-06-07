from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Literal

SeedMode = Literal["none", "categories", "test"]


def _expand_path(path: str) -> Path:
    return Path(os.path.expanduser(path)).resolve()


def get_db_path() -> Path:
    raw = os.getenv("EXPENSE_DB_PATH", "~/expenses/data/expenses.db")
    return _expand_path(raw)


def get_schema_path() -> Path:
    return Path(__file__).resolve().parent / "schema.sql"


def get_category_seed_path(locale: str | None = None) -> Path:
    raw = (locale or os.getenv("EXPENSE_LOCALE") or "es").strip().lower()
    if raw not in ("en", "es"):
        raw = "es"
    repo_root = Path(__file__).resolve().parents[3]
    path = repo_root / "shared" / f"seed-categories-{raw}.sql"
    if path.exists():
        return path
    return repo_root / "shared" / "seed-categories-es.sql"


def get_seed_path(mode: SeedMode, *, locale: str | None = None) -> Path | None:
    if mode == "none":
        return None
    if mode == "categories":
        return get_category_seed_path(locale)
    if mode == "test":
        return Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "seed-test.sql"
    raise ValueError(f"Unknown seed mode: {mode}")


def connect() -> sqlite3.Connection:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(*, seed: SeedMode | bool = "categories", locale: str | None = None) -> Path:
    if seed is True:
        seed_mode: SeedMode = "categories"
    elif seed is False:
        seed_mode = "none"
    else:
        seed_mode = seed

    db_path = get_db_path()
    schema = get_schema_path().read_text(encoding="utf-8")
    with connect() as conn:
        conn.executescript(schema)
        seed_path = get_seed_path(seed_mode, locale=locale)
        if seed_path is not None and seed_path.exists():
            conn.executescript(seed_path.read_text(encoding="utf-8"))
        conn.commit()

    from .migrations import run_migrations

    run_migrations()
    return db_path


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [row_to_dict(r) for r in rows]  # type: ignore[misc]
