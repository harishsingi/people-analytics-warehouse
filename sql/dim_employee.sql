-- SCD Type 2 dimension for employees (SQLite-compatible).
-- Convention, shared with src/scd2.py and src/models.py SCD2Row:
--   valid_from inclusive, valid_to is the change date;
--   a current row has valid_to IS NULL and is_current = 1;
--   a closed row has a valid_to date and is_current = 0.
-- History is never overwritten: a department/manager change closes the
-- current row and opens a new one.
CREATE TABLE IF NOT EXISTS dim_employee (
    employee_key INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id  TEXT    NOT NULL,
    department   TEXT    NOT NULL,
    manager_id   TEXT,
    valid_from   DATE    NOT NULL,
    valid_to     DATE,
    is_current   INTEGER NOT NULL CHECK (is_current IN (0, 1)),
    CHECK (valid_to IS NULL OR valid_to >= valid_from),
    CHECK ((is_current = 1 AND valid_to IS NULL)
        OR (is_current = 0 AND valid_to IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_dim_employee_id_current
    ON dim_employee (employee_id, is_current);
CREATE INDEX IF NOT EXISTS idx_dim_employee_valid
    ON dim_employee (valid_from, valid_to);
