CREATE OR REPLACE VIEW inputs_percap AS
SELECT
  d.area,                -- from dim table
  w.code,
  CAST(w.year AS INTEGER) AS year,
  w.real_total_wages,
  p.total_permits,
  pop.population,
  (1000.0 * p.total_permits) / NULLIF(pop.population, 0) AS permits_per_1k
FROM v_annual_wages_real_lake AS w
JOIN v_annual_permits_lake AS p
  ON p.code = w.code AND p.year = w.year
JOIN cbsa_population AS pop
  ON pop.cbsa_code = w.code AND pop.year = w.year
JOIN dim_metro_full d
  ON d.code = w.code;