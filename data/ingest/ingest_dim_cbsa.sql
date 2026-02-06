CREATE OR REPLACE TABLE dim_cbsa AS
SELECT
  CAST(CBSA AS BIGINT) AS cbsa_code,
  CASE
    WHEN LSAD = 'Metropolitan Statistical Area' THEN 'Metro'
    WHEN LSAD = 'Micropolitan Statistical Area' THEN 'Micro'
    ELSE NULL
  END AS cbsa_type,
  NAME AS cbsa_name,
  -- CAST(STCOU AS BIGINT) AS stcou  -- optional, might be blank for MSA rows
FROM 'data/raw/cbsa-est2024-alldata.utf8.csv'
WHERE LSAD IN ('Metropolitan Statistical Area', 'Micropolitan Statistical Area');


-- sanity: should be ~925
SELECT count(*) FROM dim_cbsa;

-- sanity: no dupes
SELECT cbsa_code, count(*) c
FROM dim_cbsa
GROUP BY 1
HAVING c > 1;