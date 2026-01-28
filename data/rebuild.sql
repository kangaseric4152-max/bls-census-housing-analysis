-- rebuild.sql

-- include: data/ingest/ingest_dim_metro_full.sql

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