CREATE OR REPLACE VIEW v_annual_permits_lake AS
SELECT
  code,
  year,
  SUM(total_permits_month) AS total_permits
FROM v_permits_monthly_lake
GROUP BY 1,2;