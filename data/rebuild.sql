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
-- include: data/views/v_permits_monthly_lake.sql
-- include: data/views/v_annual_permits_lake.sql

-- include: data/views/v_qcew_quarterly_lake.sql
-- include: data/views/v_qcew_quarterly_filtered.sql
-- include: data/views/v_qcew_quarterly_window.sql
-- include: data/views/v_annual_wages_nominal_lake.sql
-- include: data/views/v_annual_wages_real_lake.sql
-- inputs_percap should come after wages+permits views exist:
-- include: data/views/inputs_percap.sql


DROP TABLE IF EXISTS annual_metrics_stage;
DROP TABLE IF EXISTS cumulative_metrics_stage;
DROP TABLE IF EXISTS wages_metrics_stage;
DROP TABLE IF EXISTS permits_metrics_stage;


CREATE TABLE IF NOT EXISTS annual_metrics (
  Area VARCHAR,
  Code BIGINT,
  Year BIGINT,
  Total_Wages BIGINT,
  Real_Total_Wages DOUBLE,
  Change_Real_Wage DOUBLE,
  Total_Permits DOUBLE,
  Change_Permit DOUBLE,
  Wage_Index DOUBLE,
  Permit_Index DOUBLE,
  Zoning_Pressure DOUBLE
);


CREATE TABLE IF NOT EXISTS cumulative_metrics (
  Area VARCHAR,
  Code BIGINT,
  Year BIGINT,
  Real_Total_Wages DOUBLE,
  Total_Permits DOUBLE,
  Base_Wage DOUBLE,
  Base_Permits DOUBLE,
  Cumul_Wage_Index DOUBLE,
  Cumul_Permit_Index DOUBLE,
  Structural_Gap DOUBLE
);

CREATE TABLE IF NOT EXISTS wages_metrics (
    Area VARCHAR,
    Code BIGINT,
    Year BIGINT,
    Quarter BIGINT,
    Total_Wages BIGINT
);

CREATE TABLE IF NOT EXISTS permits_metrics (
    Area VARCHAR,
    Code BIGINT,
    Year BIGINT,
    Quarter BIGINT,
    Month BIGINT,
    Total_Permits BIGINT
);

-- sanity check helpers (run manually or from build script)
-- should always return 0 rows
-- SELECT Code, Year, COUNT(*) c FROM annual_metrics GROUP BY Code, Year HAVING COUNT(*) > 1;
-- SELECT Code, Year, COUNT(*) c FROM cumulative_metrics GROUP BY Code, Year HAVING COUNT(*) > 1;