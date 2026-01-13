from __future__ import annotations

from typing import Iterator, TextIO

from .kinds import CharKind, Token, TokenKind


class LexerError(RuntimeError):
    pass


def lexalise(fp: TextIO) -> Iterator[Token]:
    """
    Streaming Lexer for Clausewitz text:
    - ignores whitespace
    - emits ATOM tokens for barewords and numbers (keep raw lexeme)
    - emits STRING tokens for "..."
    """
    line = 1
    col = 0

    def read_char() -> str:
        nonlocal line, col
        ch = fp.read(1)
        if ch == "":
            return ""
        if ch == "\n":
            line += 1
            col = 0
        else:
            col += 1
        return ch

    def peek_char() -> str:
        pos = fp.tell()
        ch = fp.read(1)
        fp.seek(pos)
        return ch

    def token(kind: TokenKind, text: str = "", quoted: bool = False) -> Token:
        # Token position points to end-ish of col. Might need revisit
        return Token(kind=kind, text=text, quoted=quoted, line=line, col=max(col, 1))

    while True:
        ch = read_char()
        # EOF
        if ch == CharKind.EOF.value:
            yield token(TokenKind.EOF)
            return

        # Whitespace
        if ch.isspace():
            continue

        # LBRACE
        if ch == CharKind.LBRACE.value:
            yield token(TokenKind.LBRACE, CharKind.LBRACE.value)
            continue
        # RBRACE
        if ch == CharKind.RBRACE.value:
            yield token(TokenKind.RBRACE, CharKind.RBRACE.value)
            continue
        # EQUALS
        if ch == CharKind.EQUALS.value:
            yield token(TokenKind.EQUALS, CharKind.EQUALS.value)
            continue

        # Quoted String
        if ch == CharKind.QUOTED_STRING.value:
            buf: list[str] = []
            while True:
                c = read_char()
                if c == CharKind.EOF.value:
                    raise LexerError(f"Unterminated string at {line}:{col}")
                if c == CharKind.QUOTED_STRING.value:
                    break
                if c == CharKind.SEQ_ESCAPE.value:
                    # Handling escapes in a simple mostly-lossless manner
                    # store backslash + next character as-is.
                    _next = read_char()
                    if _next == CharKind.EOF.value:
                        raise LexerError(f"Unterminated escape at {line}:{col}")
                    buf.append(CharKind.SEQ_ESCAPE.value)
                    buf.append(_next)
                else:
                    buf.append(c)

            yield token(TokenKind.STRING, "".join(buf), quoted=True)
            continue

        # ATOM: Read until whitespace or delimiter
        buf = [ch]
        while True:
            p = peek_char()
            if p == "" or p.isspace() or p in "{}=":
                break
            if p == CharKind.EQUALS.value:
                break
            buf.append(read_char())
        yield token(TokenKind.ATOM, "".join(buf), quoted=False)  #
