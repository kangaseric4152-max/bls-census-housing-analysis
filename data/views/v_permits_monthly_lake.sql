-- Monthly permit rows from the lake (year/month are hive partitions + we also injected columns)
CREATE OR REPLACE VIEW v_permits_monthly_lake AS
SELECT
  CAST(code AS BIGINT) AS code,
  CAST(year AS INTEGER) AS year,
  CAST(month AS INTEGER) AS month,
  CAST(total_permits_month AS BIGINT) AS total_permits_month
FROM read_parquet(getvariable('project_root') || '/data/derived/census_permits.parquet');