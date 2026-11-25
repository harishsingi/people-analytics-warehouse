# Data quality

## Validation rules (`src/validation.py`)

A raw employee record is valid only if:

- `employee_id`, `department`, `tenure_months`, `exited` are present
  and non-null; `manager_id` may be null
- `employee_id` is a non-empty string
- `department` is in the configured department list (`config.yaml`)
- `tenure_months` is an integer in 0..480
- `exited` is 0 or 1
- `employee_id` has not appeared earlier in the batch (first wins)

## Quarantine, not silent drops

Every rejected record is kept in `quarantine_employees` with the raw
record (as JSON) and the reason it failed. A single bad row never fails
a load: `validate_records` returns valid records plus quarantined ones,
and `src/loader.py` loads both tables in the same transaction.

## Row-count reconciliation

Every load logs rows in, rows valid, rows quarantined, and per-table
row counts after the load (`bronze_employees`, `quarantine_employees`,
`dim_employee`). `load_warehouse` returns those counts so a caller or
a test can assert them. Re-running the same seeded load must produce
identical counts; that is the idempotency check in
`tests/test_loader.py`.

## What is deliberately not here

- No null imputation: a null required field quarantines the row instead
  of guessing a value.
- No deduplication by fuzzy matching: only exact `employee_id`
  duplicates are caught; near-duplicates are a source-system problem.
- No network source, so there is no retry/backoff in this repo; if a
  real HR source is ever added, retries belong in that source adapter,
  not in the loader.
