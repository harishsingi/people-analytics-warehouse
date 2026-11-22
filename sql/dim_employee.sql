-- SCD Type 2 dimension (dialect-neutral sketch)
CREATE TABLE dim_employee (employee_key INTEGER, employee_id TEXT, department TEXT, manager_id TEXT, valid_from DATE, valid_to DATE, is_current INTEGER);
