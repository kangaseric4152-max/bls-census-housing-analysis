CREATE OR REPLACE TABLE dim_metro_full AS
SELECT
  CAST(Code AS INTEGER) AS Code,
  Area,
  Title
FROM read_csv_auto('data/raw/metros.csv', header=true);

-- quick sanity checks
-- Expect 260 rows
SELECT COUNT(*) AS n_rows FROM dim_metro_full;
SELECT * FROM dim_metro_full LIMIT 5;
-- CSV shape check (should return 0 rows)
SELECT
  * as raw_line,
  length(raw_line) - length(replace(raw_line, ',', '')) + 1 AS inferred_columns
FROM read_csv('data/raw/metros.csv', delim='\n')
where inferred_columns <> 3;

