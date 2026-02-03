-- Assumes you have a table/view like cpi_annual(year, cpi_index)
-- and a chosen base year for indexing (or a real-dollar conversion factor)

CREATE OR REPLACE VIEW v_annual_wages_real_lake AS
WITH params AS (SELECT 2023::INT AS cpi_base_year),
base AS (
  SELECT cpi_index AS base_cpi
  FROM cpi_annual, params
  WHERE year = params.cpi_base_year
),
adj AS (
  SELECT
    w.code,
    w.year,
    w.total_wages_nominal,
    c.cpi_index,
    b.base_cpi,
    (w.total_wages_nominal * (b.base_cpi / NULLIF(c.cpi_index, 0))) AS real_total_wages
  FROM v_annual_wages_nominal_lake w
  JOIN cpi_annual c USING (year)
  CROSS JOIN base b
)
SELECT * FROM adj;