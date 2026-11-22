# People Analytics Warehouse

Portfolio implementation based on production work experience. All data is synthetic, all code is original and clean-room, and no proprietary code, data, schema names, or internal system details from any employer are included.

**Original context:** Pipelines for People (HR) teams: employee lifecycle and HR operational data into governed, dimensionally modelled curated layers (SCD Type 1 and 2) powering attrition, headcount and workforce reporting, with row and column level access controls. Plus earlier consulting work on a multi-class model to explain and predict employee churn by performance tier and attrition risk.

**This portfolio version:** Synthetic HR records only, SQL dimensional models that run on SQLite, SCD2 logic in Python, and attrition metrics.

## Run
```bash
python -m src.load_synthetic
python -m src.scd2_demo
python -m pytest tests/ -q
```
## Models
- `dim_employee` (SCD2: history preserved on department / manager change)
- `fact_employee_month` (headcount, joins, exits, attrition rate)
- Access model documented in `docs/access_controls.md`: row level by org, column masking for sensitive fields
