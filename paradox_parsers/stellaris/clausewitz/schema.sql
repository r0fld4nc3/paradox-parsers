-- schema for Clausewitz Stellaris gamestate parsing and serialisation.

PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS block (
    id INTEGER PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS item (
    id INTEGER PRIMARY KEY,
    block_id INTEGER NOT NULL REFERENCES block(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ("assign", "value")),
    key_text TEXT, -- for kind='assign', raw key lexeme (e.g. 0, name, "key")                 
    value_kind TEXT NOT NULL CHECK(value_kind IN ("scalar", "block")),
    scalar_text TEXT, -- for value_kind='scalar', raw scalar lexeme (unquoted for strings)
    scalar_quoted INTEGER NOT NULL DEFAULT 0, -- 1 if original was "..."
    child_block_id INTEGER REFERENCES block(id) ON DELETE CASCADE -- for value_kind="block"
);

CREATE INDEX IF NOT EXISTS idx_item_block_order ON item(block_id, order_index);
CREATE INDEX IF NOT EXISTS idx_item_key ON item(key_text);