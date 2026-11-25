-- Bronze layer: raw synthetic employee records, kept immutable so any
-- curated table can be rebuilt from source. Loaded by src/loader.py.
-- One row per employee; re-loads replace the table (idempotent).
CREATE TABLE IF NOT EXISTS bronze_employees (
    employee_id   TEXT    NOT NULL PRIMARY KEY,
    department    TEXT    NOT NULL,
    tenure_months INTEGER NOT NULL CHECK (tenure_months >= 0),
    exited        INTEGER NOT NULL CHECK (exited IN (0, 1)),
    manager_id    TEXT
);

-- Records rejected by src/validation.py, kept for audit (never dropped).
CREATE TABLE IF NOT EXISTS quarantine_employees (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_json   TEXT NOT NULL,
    reason     TEXT NOT NULL,
    loaded_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
