-- cbsa population fact table (derived artifact committed to repo)
-- Grain: (cbsa_code, year)
-- Source artifact: data/derived/cbsa_population.parquet

DROP TABLE IF EXISTS cbsa_population;

CREATE TABLE cbsa_population AS
SELECT
  cbsa_code::BIGINT AS cbsa_code,
  year::INTEGER     AS year,
  population::BIGINT AS population
FROM read_parquet('data/derived/cbsa_population.parquet');

-- Fail-fast checks (will throw if violated)
-- 1) no nulls
SELECT
  CASE WHEN COUNT(*) FILTER (WHERE cbsa_code IS NULL OR year IS NULL OR population IS NULL) = 0
       THEN 1
       ELSE error('cbsa_population has NULLs')
  END AS ok_nulls
FROM cbsa_population;

-- 2) uniqueness
SELECT
  CASE WHEN COUNT(*) = 0
       THEN 1
       ELSE error('cbsa_population has duplicate (cbsa_code, year)')
  END AS ok_dupes
FROM (
  SELECT cbsa_code, year
  FROM cbsa_population
  GROUP BY 1,2
  HAVING COUNT(*) > 1
);

-- Optional: cheap sanity checks (non-fatal if you prefer)
-- SELECT min(year), max(year), count(*) rows, count(distinct cbsa_code) metros FROM cbsa_population;