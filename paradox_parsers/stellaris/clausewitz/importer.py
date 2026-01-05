from __future__ import annotations

import sqlite3
from pathlib import Path

from .db_sqlite import SqliteSink
from .lexer import lexalise
from .parser import Parser


def parse_gamestate_to_sqlite(gamestate_path: Path, sqlite_path: Path) -> int:
    """
    Parse a provided Stellaris `gamestate` file and serialise it do a SQLite database.

    Note:
        The database file will be created if it doesn't exist.

    Arguments:
        filepath: The filepath to the Stellaris `gamestate` file.
        db: The filepath where to output a SQLite database file, containing the serialised information from `gamestate`.
    """
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(sqlite_path)
    db.execute("PRAGMA journal_mode=WAL;")
    db.execute("PRAGMA synchronous=NORMAL;")
    db.execute("PRAGMA temp_store=MEMORY;")

    sql_sink = SqliteSink(db)
    sql_sink.init_schema()

    with gamestate_path.open("r", encoding="utf-8", errors="replace", newline="") as fp, db:
        parser = Parser(lexalise(fp))
        root_id = parser.parse_into_sql(sql_sink)

    db.close()
    return root_id
