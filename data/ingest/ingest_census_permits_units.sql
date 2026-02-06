-- ingest/ingest_census_permits_units.sql
-- Builds monthly permits with unit breakdown from cached CSVs
-- 
CREATE OR REPLACE TABLE census_permits_units_monthly AS
WITH raw AS (
  SELECT
    filename,
    *
  FROM read_csv_auto(
    project_path('/data/cache/census/csv/*.csv'),
    union_by_name=true,
    filename=true
  )
  WHERE regexp_matches(filename, 'CBSA_\d{4}_\d{2}\.csv$')
),
tagged AS (
  SELECT
    TRY_CAST(regexp_extract(filename, 'CBSA_(\d{4})_(\d{2})\.csv$', 1) AS INTEGER) AS year,
    TRY_CAST(regexp_extract(filename, 'CBSA_(\d{4})_(\d{2})\.csv$', 2) AS INTEGER) AS month,

    TRY_CAST("CBSA" AS BIGINT) AS code,

    TRY_CAST("Total" AS BIGINT) AS total_permits_month,
    TRY_CAST("1 Unit" AS BIGINT) AS permits_1_unit,
    TRY_CAST("2 Units" AS BIGINT) AS permits_2_unit,
    TRY_CAST("3 and 4 Units" AS BIGINT) AS permits_3_4_units,
    TRY_CAST("5 Units or More" AS BIGINT) AS permits_5_plus,
    TRY_CAST("Num of Structures With 5 Units or More" AS BIGINT) AS structures_5_plus

  FROM raw
)
SELECT *
FROM tagged
WHERE code IS NOT NULL
  AND year IS NOT NULL
  AND month IS NOT NULL;