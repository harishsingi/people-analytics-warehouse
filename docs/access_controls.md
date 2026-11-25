# Access controls

Enforced in code by `src/access.py` (`apply_access`, `mask_sensitive`,
`filter_by_department`); this document is the policy that code implements.
All data in this repo is synthetic, so these controls are a demonstration
of the pattern, not protection of real employee data.

## Row level: who sees which rows

| Role | Rows visible |
|---|---|
| `hr_admin` | All departments |
| `people_analyst` | All departments |
| `manager` | Only the manager's own department(s); `own_departments` is required |
| `executive` | All departments (aggregates in practice; no sensitive fields) |

Unknown roles are rejected with `ValueError`; a `manager` call without
`own_departments` is rejected the same way, so a missing scope can never
silently widen to "all rows".

## Column level: which fields are masked

Fields in `SENSITIVE_FIELDS` (`compensation_band`, `national_id`,
`salary`) are replaced with `***` for every role except `hr_admin`.
Non-sensitive fields (employee id, department, tenure) are never masked
by this step. Masking returns new dicts; input rows are not mutated.

## Logging

`apply_access` logs the role and the number of rows returned. It does
not log row contents, so sensitive values never land in logs.
