CREATE OR REPLACE VIEW v_census_permits_units_monthly_metro AS
SELECT
  c.*,
  d.cbsa_name,
  d.cbsa_type
FROM read_parquet(project_path('/data/derived/census_permits_units.parquet')) c
JOIN dim_cbsa d ON d.cbsa_code = c.code
WHERE d.cbsa_type = 'Metro';