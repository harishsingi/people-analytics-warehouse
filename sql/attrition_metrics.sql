-- Monthly attrition: exits / average headcount
SELECT month, COUNT(DISTINCT CASE WHEN exit_date IS NOT NULL THEN employee_id END)*1.0 / COUNT(DISTINCT employee_id) AS attrition_rate FROM fact_employee_month GROUP BY month;
