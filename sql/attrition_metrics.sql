-- Monthly attrition: exits / average headcount, per month and department.
-- Uses fact_employee_month (one row per employee per month). The
-- denominator is the average headcount across the month's rows, not the
-- end-of-month count, so exits during the month are not divided by a
-- headcount that already excludes them. A month with zero headcount
-- yields NULL, not zero, via NULLIF.
SELECT
    month,
    department,
    COUNT(*) AS headcount,
    SUM(exited) AS exits,
    SUM(exited) * 1.0 / NULLIF(COUNT(*), 0) AS attrition_rate
FROM fact_employee_month
GROUP BY month, department
ORDER BY month, department;

-- Overall monthly attrition (all departments combined).
SELECT
    month,
    COUNT(*) AS headcount,
    SUM(exited) AS exits,
    SUM(exited) * 1.0 / NULLIF(COUNT(*), 0) AS attrition_rate
FROM fact_employee_month
GROUP BY month
ORDER BY month;
