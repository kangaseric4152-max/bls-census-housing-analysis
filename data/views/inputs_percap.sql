CREATE OR REPLACE VIEW inputs_percap AS
SELECT
  w.area,
  w.code,
  CAST(w.year AS INTEGER) AS year,
  w.real_total_wages,
  p.total_permits,
  pop.population,
  (1000.0 * p.total_permits) / NULLIF(pop.population, 0) AS permits_per_1k
FROM read_parquet('data/derived/annual_wages.parquet') AS w
JOIN v_annual_permits_lake AS p
  ON p.code = w.code AND p.year = w.year
JOIN cbsa_population AS pop
  ON pop.cbsa_code = w.code AND pop.year = w.year;