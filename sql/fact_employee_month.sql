-- Monthly employee fact: one row per employee per month in scope.
-- Built from dim_employee + bronze in a real pipeline; here it is the
-- target schema for the monthly headcount / joins / exits grain.
-- attrition for a month = exits / average headcount (see
-- sql/attrition_metrics.sql).
CREATE TABLE IF NOT EXISTS fact_employee_month (
    employee_id TEXT    NOT NULL,
    month       DATE    NOT NULL,  -- first day of the month
    department  TEXT    NOT NULL,
    is_headcount INTEGER NOT NULL CHECK (is_headcount IN (0, 1)),
    joined      INTEGER NOT NULL CHECK (joined IN (0, 1)),
    exited      INTEGER NOT NULL CHECK (exited IN (0, 1)),
    PRIMARY KEY (employee_id, month)
);
CREATE INDEX IF NOT EXISTS idx_fact_month_dept
    ON fact_employee_month (month, department);
