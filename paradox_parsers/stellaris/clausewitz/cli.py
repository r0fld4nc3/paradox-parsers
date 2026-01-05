import argparse
import logging
import time
from pathlib import Path

from paradox_parsers.stellaris.clausewitz.importer import parse_gamestate_to_sqlite

log = logging.getLogger(__name__)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Serialise Stellaris gamestate files to an SQLite Database.")
    p.add_argument("filepath", help="Path to gamestate file")
    p.add_argument("db", help="Output SQLite database path")
    return p.parse_args(argv)


def cli_parse(argv=None) -> int:
    """
    Provide a filepath to a Stellaris `gamestate` file to serialise to a SQLite database.

    Note:
        The database file will be created if it doesn't exist.

    Arguments:
        filepath: The filepath to the Stellaris `gamestate` file.
        db: The filepath where to output a SQLite database file, containing the serialised information from `gamestate`.
    """
    args = parse_args(argv)

    _arg_fp = args.filepath
    _db = args.db

    gamestate: Path = None
    db: Path = None

    if _arg_fp:
        gamestate = Path(_arg_fp)
    else:
        raise RuntimeError(f"Filepath is required")

    if _db:
        db = Path(_db)
    else:
        raise RuntimeError(f"Database path is required")

    log.info(f"Parsing gamestate file: '{gamestate}'")
    log.info(f"Building SQLite DB at:  '{db}'")
    log.info("Please wait...")

    start = time.time()

    root_id = parse_gamestate_to_sqlite(gamestate, db)

    time_taken = round(time.time() - start, 3)
    log.info(f"Done in {time_taken}s")

    return root_id


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] [%(name)s] [%(message)s]")
    cli_parse()
