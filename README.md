# paradox-parsers

A collection of parsers for Paradox Interacive's gamestate files to a SQLite database so that it is possible to modify and regenerate a gamestate file with as little data loss as possible.

# Installation

Can be defined as a dependency in the project's pyproject.toml as:
```
paradox-parsers
```

# Usage

```python
from paradox_parsers import cli_parse, parse_gamestate_to_sqlite
```