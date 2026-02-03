-- Monthly permit rows from the lake (year/month are hive partitions + we also injected columns)
CREATE OR REPLACE VIEW v_permits_monthly_lake AS
SELECT
  CAST(cbsa_code AS BIGINT) AS code,
  CAST(year AS INTEGER) AS year,
  CAST(month AS INTEGER) AS month,
  CAST(total_permits AS BIGINT) AS total_permits_month
FROM read_parquet(
  project_path('/data/lake/census_permits/**/*.parquet'),
  hive_partitioning=1
);