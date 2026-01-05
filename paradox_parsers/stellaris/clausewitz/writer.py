from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import IO, Optional, Union
import sqlite3
from .kinds import ValueKind, InsertKind
import logging

log = logging.getLogger(__name__)

@dataclass(frozen=True)
class WriterStyle:
    indent: str = "\t"
    newline: str = "\n"
    brace_on_new_line_for_assign: bool = True
    space_around_equals: bool = False # key=value vs key = value

class GamestateWriter:
    def __init__(self, db: Union[sqlite3.Connection, str, Path], style: Optional[WriterStyle] = None):
        self.db = db
        self.style = style or WriterStyle()

        if isinstance(db, sqlite3.Connection):
            self.db = db
            self._owns_connection = False
        else:
            self.db = sqlite3.connect(str(db))
            self._owns_connection = True

    def close(self) -> None:
        if self._owns_connection:
            self.db.close()

    def write_to_path(self, root_block_id: int, out_path: str) -> None:
        log.info(f"Write {out_path} from root_block_id: {root_block_id}")
        with open(out_path, 'w', encoding="utf-8", newline="") as f:
            self.write(root_block_id, f)

    def write(self, root_block_id: int, out: IO[str]) -> None:
        """
        Write the implicit root block contents (no surrounding braces)
        """

        for row in self._iter_items(root_block_id):
            log.info(f"Write: {root_block_id}: {row=}")
            self._write_item(row, out, indent_level=0)


    # --- Helpers ---
    def _iter_items(self, block_id: int):
        cur = self.db.execute(
            """
            SELECT kind, key_text, value_kind, scalar_text, scalar_quoted, child_block_id
            FROM item
            WHERE block_id = ?
            ORDER BY order_index
            """, (block_id,)
        )
        yield from cur

    def _write_item(self, row, out: IO[str], indent_level: int) -> None:
        kind, key_text, value_kind, scalar_text, scalar_quoted, child_block_id = row
        indent = self.style.indent * indent_level
        eq = " = " if self.style.space_around_equals else "="
        nl = self.style.newline

        if kind == InsertKind.assign.value:
            if key_text is None:
                raise ValueError("DB invariant violated: assign item with NULL key_text")

            if value_kind == ValueKind.scalar.value:
                out.write(f"{indent}{key_text}{eq}{self._format_scalar(scalar_text, scalar_quoted)}{nl}")
                return
            
            if value_kind == ValueKind.block.value:
                if child_block_id is None:
                    raise ValueError("DB invariant violated: block value with NULL child_block_id")
            
                if self.style.brace_on_new_line_for_assign:
                    out.write(f"{indent}{key_text}{eq}{nl}")
                    out.write(f"{indent}{{{nl}")
                else:
                    out.write(f"{indent}{key_text}{eq}{{{nl}")

                self._write_block(child_block_id, out, indent_level + 1)
                out.write(f"{indent}}}{nl}")
                return
            
            raise ValueError(f"Unknown value_kind: {value_kind!r}")
    
        if InsertKind.val.value:
            if value_kind == ValueKind.scalar.value:
                out.write(f"{indent}{self._format_scalar(scalar_text, scalar_quoted)}{nl}")
                return
            
            if value_kind == ValueKind.block.value:
                if child_block_id is None:
                    raise ValueError("DB invariant violated: block value with NULL child_block_id")
                
                out.write(f"{indent}{{{nl}")
                self._write_block(child_block_id, out, indent_level + 1)
                out.write(f"{indent}}}{nl}")
                return
            
            raise ValueError(f"Unknown value_kind: {value_kind!r}")

        raise ValueError(f"Unknown kind: {kind!r}")
        
    def _write_block(self, block_id: int, out: IO[str], indent_level: int) -> None:
        for row in self._iter_items(block_id):
            self._write_item(row, out, indent_level)
    
    def _format_scalar(self, text: Optional[str], quoted: int) -> str:
        if text is None:
            return ""
        
        if not quoted:
            return text
        
        # Best attempt at escaping Clausewitz strings.
        # Since we are currently not storing raw lexems, original
        # escape is not guaranteed
        escaped = (
            text.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\t", "\\t")
        )
        return f'"{escaped}"'