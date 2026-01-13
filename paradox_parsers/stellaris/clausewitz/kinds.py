from dataclasses import dataclass
from enum import Enum, auto


class InsertKind(Enum):
    assign = "assign"
    val = "value"


class ValueKind(Enum):
    scalar = "scalar"
    block = "block"


class CharKind(Enum):
    LBRACE = "{"
    RBRACE = "}"
    EQUALS = "="
    QUOTED_STRING = '"'
    EOF = ""
    SEQ_ESCAPE = "\\"


class TokenKind(Enum):
    LBRACE = auto()  # {
    RBRACE = auto()  # }
    EQUALS = auto()  # =
    ATOM = auto()  # identifier/number/bareword (as raw text)
    STRING = auto()  # "..."
    EOF = auto()


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    text: str  # Raw token text for ATOM, decoded inner for STRING
    quoted: bool = False  # Set to True only for STRING
    line: int = 1
    col: int = 0
