CREATE OR REPLACE VIEW v_annual_wages_nominal_lake AS
SELECT
  cbsa_code AS code,
  year,
  SUM(total_qtrly_wages) AS total_wages_nominal
FROM v_qcew_quarterly_window
GROUP BY 1,2;