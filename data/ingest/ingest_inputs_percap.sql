-- inputs_percap: committed derived mart, baseline-free
CREATE OR REPLACE TABLE inputs_percap AS
SELECT
  area,
  code::BIGINT AS code,
  year::INTEGER AS year,
  real_total_wages::DOUBLE AS real_total_wages,
  total_permits::DOUBLE AS total_permits,
  population::BIGINT AS population,
  permits_per_1k::DOUBLE AS permits_per_1k
FROM read_parquet('data/derived/inputs_percap.parquet');

-- helpful constraints-ish checks (DuckDB doesn’t enforce like Postgres, but we can assert via queries)
-- optional: create a unique index if you want (DuckDB supports indexes but they’re not always necessary)
-- CREATE UNIQUE INDEX IF NOT EXISTS ux_inputs_percap ON inputs_percap(code, year);