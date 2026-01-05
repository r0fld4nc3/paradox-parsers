from enum import Enum

class InsertKind(Enum):
    assign = "assign"
    val = "value"


class ValueKind(Enum):
    scalar = "scalar"
    block = "block"