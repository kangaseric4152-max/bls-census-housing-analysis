CREATE OR REPLACE TABLE cpi_annual AS
SELECT
  CAST(year AS BIGINT) AS year,
  CAST(cpi_index AS DOUBLE) as cpi_index,

FROM read_csv_auto('data/raw/cpi_annual.csv', header=true);

