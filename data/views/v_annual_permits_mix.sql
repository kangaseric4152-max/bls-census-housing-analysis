CREATE OR REPLACE VIEW v_annual_permits_mix AS
SELECT
  code,
  year,
  SUM(total_permits_month) AS total_permits,
  SUM(permits_1_unit)      AS permits_1_unit,
  SUM(permits_2_unit)      AS permits_2_unit,
  SUM(permits_3_4_units)   AS permits_3_4_units,
  SUM(permits_5_plus)      AS permits_5_plus,
  SUM(structures_5_plus) AS structures_5_plus,

  -- shares (guard div-by-zero)
  CASE WHEN SUM(total_permits_month) > 0
    THEN SUM(permits_1_unit)    * 1.0 / SUM(total_permits_month)
    ELSE NULL END AS share_1_unit,

  CASE WHEN SUM(total_permits_month) > 0
    THEN SUM(permits_5_plus)    * 1.0 / SUM(total_permits_month)
    ELSE NULL END AS share_5_plus,

  CASE WHEN SUM(total_permits_month) > 0
    THEN (SUM(permits_3_4_units) + SUM(permits_5_plus)) * 1.0 / SUM(total_permits_month)
    ELSE NULL END AS share_3_4_plus,

  CASE WHEN SUM(structures_5_plus) > 0
    THEN SUM(permits_5_plus) * 1.0 / SUM(structures_5_plus)
    ELSE NULL END AS avg_units_per_5plus_structure
FROM read_parquet(project_path('/data/derived/census_permits_units.parquet'))
GROUP BY code, year;