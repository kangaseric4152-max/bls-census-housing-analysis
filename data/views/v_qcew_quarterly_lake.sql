CREATE OR REPLACE VIEW v_qcew_quarterly_lake AS
SELECT
  -- hive partitions you already wrote
  cbsa_code,
  year,
  quarter,

  -- everything from the underlying parquet
  *
FROM read_parquet( --swap from demo to lake path if ingesting new data, details for updating demo in data/demo/manifest.json
  project_path('/data/demo/qcew_demo.parquet')
  --project_path('/data/lake/bls/**/*.parquet'),
  --hive_partitioning=1
);