-- rebuild.sql

CREATE OR REPLACE MACRO project_path(p) AS 
  getvariable('project_root') || p;

-- safety check
SELECT
  CASE
    WHEN getvariable('project_root') IS NULL
    THEN error('project_root variable must be set before using this database')
    ELSE 1
  END;
  
-- include: data/ingest/ingest_dim_metro_full.sql
-- include: data/ingest/ingest_cbsa_population.sql
-- include: data/ingest/ingest_cpi_annual.sql
-- include: data/ingest/ingest_dim_cbsa.sql

-- include: data/views/v_permits_monthly_lake.sql
-- include: data/views/v_annual_permits_lake.sql

-- include: data/views/v_census_permits_units_monthly_metro.sql
-- include: data/views/v_annual_permits_mix.sql
-- include: data/views/v_qcew_quarterly_lake.sql
-- include: data/views/v_qcew_quarterly_filtered.sql
-- include: data/views/v_qcew_quarterly_window.sql
-- include: data/views/v_annual_wages_nominal_lake.sql
-- include: data/views/v_annual_wages_real_lake.sql
-- inputs_percap should come after wages+permits views exist:
-- include: data/views/inputs_percap.sql
