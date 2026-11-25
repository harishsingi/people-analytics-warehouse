# People Analytics Warehouse

Synthetic HR records, dimensional models (SCD Type 1 and 2), and
attrition metrics, implemented the way a production people-analytics
pipeline is built: validated bronze data, a governed dimension with
preserved history, row/column access controls, and logged row counts at
every step.

**All data is synthetic.** Employee ids, departments, tenure, and exit
flags are generated from a fixed seed (`config.yaml`, seed 3). No real
employee data, no company names, no locations, and no proprietary code,
schema names, or internal system details from any employer are included.

## What this demonstrates

- Employee lifecycle data loaded into governed, dimensionally modelled
  layers (SCD Type 2) powering attrition, headcount, and workforce
  reporting, with row- and column-level access controls.
- History preserved on department / manager changes, so past headcount
  can be reconstructed instead of overwritten.
- Attrition and churn metrics by department, flagging high-risk
  segments from the data rather than after people leave.

## Setup

Requires Python 3.10+.

```bash
python -m pip install -r requirements.txt        # runtime: PyYAML
python -m pip install -r requirements-dev.txt    # + pytest, for tests
```

No credentials, no network access, and no external services are needed.
The warehouse is a local SQLite file (`people.db` in the repo root by
default; override with `PEOPLE_ANALYTICS_DB` or `--db`).

## How to run

```bash
python -m src.load_synthetic          # generate + validate + load (500 rows, seed 3)
python -m src.load_synthetic --rows 100 --seed 42 --db /tmp/demo.db
python -m src.scd2_demo               # SCD2 close/open example for one employee
python -m pytest tests/ -q            # full test suite
```

Re-running a load is safe: the bronze and dimension tables are rebuilt
inside one transaction from the same deterministic seed, so counts do
not grow (idempotency is covered by `tests/test_loader.py`).

## Architecture

```
config.yaml                tunables: seed, row count, departments, db file
        |
src/config.py              typed WarehouseConfig (YAML + env overrides)
src/synthetic.py           deterministic synthetic generator (seeded Random)
src/validation.py          schema validation; bad rows -> quarantine, not dropped
src/loader.py              SQLite: bronze -> quarantine -> dim_employee (SCD2)
src/scd2.py                pure close/open logic for department/manager changes
src/metrics.py             headcount / exits / attrition rate by department
src/access.py              row filter by department + column masking by role
src/models.py              EmployeeRecord / SCD2Row dataclasses (validated)
src/errors.py              custom exceptions (Config/Validation/Load/SCD2)
src/logging_config.py      logging setup; modules log, none use print()
sql/                       DDL + metric queries (single source of truth for schema)
```

Flow: HR lifecycle sources -> ingestion/validation -> bronze (immutable
raw) -> `dim_employee` SCD2 -> `fact_employee_month` -> attrition
metrics, governed throughout by the row + column controls in
`docs/access_controls.md`.

![Before / After architecture](docs/before-after-elaborated.svg)
<details>
<summary><b>SCD2 + access controls — click to expand the 4 steps</b></summary>

Collapsed, this is just: HR lifecycle sources -> Ingestion -> Bronze raw -> dim_employee SCD2

1. Employee lifecycle and HR operational data is the governed source.
2. Data is loaded and cleaned into the warehouse, so downstream models start clean.
3. The raw bronze layer is kept immutable, so any curated table can be rebuilt from source.
4. dim_employee uses SCD Type 2, so department and manager changes keep history.

Governed by the Row + column controls step that follows in the flow: row-level access by org and column masking for sensitive fields.
</details>

## Models

- `bronze_employees` — raw synthetic records, one row per employee
- `quarantine_employees` — rejected records with the reason, for audit
- `dim_employee` (SCD2: history preserved on department / manager change)
- `fact_employee_month` (headcount, joins, exits, attrition rate)

SQL definitions live in `sql/`; `src/loader.py` applies those files
rather than duplicating the DDL in code.

## Data quality

See `docs/data_quality.md`. In short: schema validation on every row,
null/duplicate handling (first duplicate wins, later ones quarantined),
quarantine of bad records with reasons, and logged rows-in / rows-out /
rejected counts on every load. No null imputation and no invented
metrics: attrition rates are computed from the loaded rows, and an
empty slice reports no rate rather than zero.

## Configuration

`config.yaml` holds the defaults (seed, employee count, departments,
exit probability, database filename). Environment overrides:
`PEOPLE_ANALYTICS_CONFIG`, `PEOPLE_ANALYTICS_DB`,
`PEOPLE_ANALYTICS_SEED`, `PEOPLE_ANALYTICS_ROWS`. The CLI also accepts
`--db`, `--rows`, and `--seed`.

## How to test

```bash
python -m pytest tests/ -q
```

Every module has tests: config, models, validation, synthetic data,
SCD2, loader (including idempotency and rollback), metrics, access
controls, logging, and the CLI end to end against a temporary database.

## Honest scope note

This is a portfolio implementation on SQLite with synthetic data. It
does not connect to any HR system, does not handle real PII, and the
access controls are an in-memory demonstration of the pattern, not a
substitute for warehouse-level grants on production data.
