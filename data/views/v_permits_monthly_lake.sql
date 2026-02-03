-- Monthly permit rows from the lake (year/month are hive partitions + we also injected columns)
CREATE OR REPLACE VIEW v_permits_monthly_lake AS
SELECT
  CAST(CBSA AS BIGINT) AS code,
  CAST(year AS INTEGER) AS year,
  CAST(month AS INTEGER) AS month,
  -- "Total" is the monthly total permits in the file
  CAST("Total" AS BIGINT) AS total_permits_month
FROM read_parquet(
  'data/lake/census_permits/**/data.parquet',
  hive_partitioning=1
);