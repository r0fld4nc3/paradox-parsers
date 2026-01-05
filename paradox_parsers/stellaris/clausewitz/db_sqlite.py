from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import Enum
from importlib import resources
from typing import Optional


class InsertKind(Enum):
    assign = "assign"
    val = "value"


class ValueKind(Enum):
    scalar = "scalar"
    block = "block"


@dataclass
class BlockContext:
    block_id: int
    next_order_index: int = 0


class SqliteSink:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.stack: list[BlockContext] = []

    def init_schema(self) -> None:
        schema = resources.files(__package__).joinpath("schema.sql").read_text()
        self.db.executescript(schema)

    def start_block(self) -> int:
        cur = self.db.execute("INSERT INTO block DEFAULT VALUES")
        block_id = cur.lastrowid
        self.stack.append(BlockContext(block_id=block_id))
        return block_id

    def end_block(self) -> int:
        ctx = self.stack.pop()
        return ctx.block_id

    def _push_item(
        self,
        kind: str,
        key_text: Optional[str],
        value_kind: str,
        scalar_text: Optional[str],
        scalar_quoted: int,
        child_block_id: Optional[int],
    ) -> None:
        ctx = self.stack[-1]
        self.db.execute(
            """
            INSERT INTO item(block_id, order_index, kind, key_text, value_kind, scalar_text, scalar_quoted, child_block_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ctx.block_id,
                ctx.next_order_index,
                kind,
                key_text,
                value_kind,
                scalar_text,
                scalar_quoted,
                child_block_id,
            ),
        )
        ctx.next_order_index += 1

    def assign_scalar(self, key_text: str, scalar_text: str, scalar_quoted: bool) -> None:
        self._push_item(
            kind=InsertKind.assign.value,
            key_text=key_text,
            value_kind=ValueKind.scalar.value,
            scalar_text=scalar_text,
            scalar_quoted=1 if scalar_quoted else 0,
            child_block_id=None,
        )

    def assign_block(self, key_text: str, child_block_id: int) -> None:
        self._push_item(
            kind=InsertKind.assign.value,
            key_text=key_text,
            value_kind=ValueKind.block.value,
            scalar_text=None,
            scalar_quoted=0,
            child_block_id=child_block_id,
        )

    def value_scalar(self, scalar_text: str, scalar_quoted: bool) -> None:
        self._push_item(
            kind=InsertKind.val.value,
            key_text=None,
            value_kind=ValueKind.scalar.value,
            scalar_text=scalar_text,
            scalar_quoted=1 if scalar_quoted else 0,
            child_block_id=None,
        )

    def value_block(self, child_block_id: int) -> None:
        self._push_item(
            kind=InsertKind.val.value,
            key_text=None,
            value_kind=ValueKind.block.value,
            scalar_text=None,
            scalar_quoted=0,
            child_block_id=child_block_id,
        )
