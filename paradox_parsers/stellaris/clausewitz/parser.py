from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from .db_sqlite import SqliteSink
from .lexer import Token, TokenKind


class ClausewitzParserError(RuntimeError):
    pass


@dataclass
class Atom:
    text: str
    quoted: bool
    line: int
    col: int


class Parser:
    def __init__(self, tokens: Iterator[Token]):
        self.tokens = tokens
        self.buf: list[Token] = []

    def _next(self) -> Token:
        if self.buf:
            return self.buf.pop(0)
        return next(self.tokens)

    def _peek(self, k: int = 1) -> Token:
        while len(self.buf) < k:
            self.buf.append(next(self.tokens))
        return self.buf[k - 1]

    def _expect(self, kind: TokenKind) -> Token:
        t = self._next()
        if t.kind != kind:
            raise ClausewitzParserError(f"Expected {kind.name} at {t.line}:{t.col}, got {t.kind.name}({t.text!r})")
        return t

    def _parse_key_atom(self) -> tuple[str, int]:
        t = self._next()
        if t.kind == TokenKind.ATOM:
            return t.text, t.line
        if t.kind == TokenKind.STRING:
            # For keys: keep quoted to remain valid if someone uses weird keys.
            return f'"{t.text}"', t.line
        raise ClausewitzParserError(f"Invalid key token at {t.line}:{t.col}: {t.kind.name}")

    def _parse_scalar(self) -> Atom:
        t = self._next()
        if t.kind == TokenKind.ATOM:
            return Atom(text=t.text, quoted=False, line=t.line, col=t.col)
        if t.kind == TokenKind.STRING:
            return Atom(text=t.text, quoted=True, line=t.line, col=t.col)
        raise ClausewitzParserError(f"Expected scalar at {t.line}:({t.col}), got {t.kind.name}")

    def parse_into_sql(self, sql_f: SqliteSink) -> int:
        """
        Parses a full file into a sql sink. Returns root_block_id.
        The file is treated as an implicit root block containing assignments.
        """
        root_block_id = sql_f.start_block()

        while True:
            t = self._peek()
            if t.kind == TokenKind.EOF:
                break

            # Top-level must be assignments: key '=' value
            key , key_line = self._parse_key_atom()
            self._expect(TokenKind.EQUALS)
            self._parse_value_as_assign(sql_f, key, key_line)

        sql_f.end_block()
        return root_block_id

    def _parse_value_as_assign(self, sql_f: SqliteSink, key_text: str, source_line: int) -> None:
        t = self._peek()

        if t.kind == TokenKind.LBRACE:
            child = self._parse_block(sql_f)
            sql_f.assign_block(key_text, child, source_line)
        else:
            atom = self._parse_scalar()
            sql_f.assign_scalar(key_text, atom.text, atom.quoted, source_line)

    def _parse_value_item(self, sql_f: SqliteSink) -> None:
        t = self._peek()
        if t.kind == TokenKind.LBRACE:
            lbrace = self._expect(TokenKind.LBRACE)
            child = self._parse_block_after_lbrace(sql_f)
            sql_f.value_block(child, lbrace.line)
        else:
            atom = self._parse_scalar()
            sql_f.value_scalar(atom.text, atom.quoted, atom.line)

    def _parse_block(self, sql_f: SqliteSink) -> int:
        self._expect(TokenKind.LBRACE)
        return self._parse_block_after_lbrace(sql_f)

    def _parse_block_after_lbrace(self, sql_f: SqliteSink) -> int:
        block_id = sql_f.start_block()

        # `block` contents: sequence of (assign | value_item) until '}'
        while True:
            t = self._peek()

            if t.kind == TokenKind.RBRACE:
                self._next()
                break

            if t.kind == TokenKind.EOF:
                raise ClausewitzParserError(f"Unexpected EOF inside block at {t.line}:{t.col}")

            # Anonymous object inside a list, e.g.: hyperlane { {to=..} {to=..} }
            if t.kind == TokenKind.LBRACE:
                self._parse_value_item(sql_f)
                continue

            # Clarify
            # If next token is ATOM/STRING and following token is '=', it is an assignment.
            if t.kind in (TokenKind.ATOM, TokenKind.STRING):
                t2 = self._peek(2)
                if t2.kind == TokenKind.EQUALS:
                    key, key_line = self._parse_key_atom()
                    self._expect(TokenKind.EQUALS)
                    self._parse_value_as_assign(sql_f, key, key_line)
                else:
                    self._parse_value_item(sql_f)
            else:
                # Value items can start with '{' handled above. Anything else is invalid
                raise ClausewitzParserError(f"Unexpected token at {t.kind.name} at {t.line}:{t.col}")

        sql_f.end_block()
        return block_id
