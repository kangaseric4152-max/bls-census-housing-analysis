# • helper: duck_con(db_path), register_parquet_views(con) etc.
from typing import List
from pathlib import Path
import duckdb
import pandas as pd
import logging

PROJECT_ROOT = Path(__file__).parents[3].resolve()
DBPATH = PROJECT_ROOT / "data" / "analysis.duckdb"

def get_analysis_db_connection(dbpath: str | Path = DBPATH):
    logger = logging.getLogger(__name__)
    logger.info("Connecting to analysis DuckDB at %s", dbpath)
    con = duckdb.connect(Path(dbpath))

    # establish session context
    con.execute(
        "SET VARIABLE project_root = ?",
        [str(PROJECT_ROOT)]
    )

    return con


def list_metros(con: duckdb.DuckDBPyConnection, codes: List[int]) -> pd.DataFrame:
    df = con.execute("""
        SELECT Code, Area, Title
        FROM dim_metro_full
        WHERE Code IN (SELECT * FROM UNNEST(?))
        ORDER BY Area, Title
    """, [codes]).df()
    logging.getLogger(__name__).info("list_metros: requested=%d returned=%d", len(codes), len(df))
    return df


def build_permits_metrics(con: duckdb.DuckDBPyConnection, 
                          metros: pd.DataFrame, 
                          years: list[int] = [y for y in range(2014, 2024)]) -> pd.DataFrame:
    years = sorted(set(years))
    assert len(years) > 1
    logging.getLogger(__name__).info("build_permits_metrics: metros=%d years=%s", len(metros), years)
    df = con.execute("""
        SELECT
        i.area,
        i.code,
        cast(i.year AS INT) AS year,
        i.permits_per_1k,
        i.permits_per_1k - lag(i.permits_per_1k) over (partition by i.code order by i.year) AS delta_permits_per_1k,
        p.share_1_unit,
        p.share_5_plus
        FROM inputs_percap i
        JOIN metros USING (code) 
        JOIN v_annual_permits_mix p USING (code, year)
        WHERE i.year IN (select * from UNNEST(?))
        ORDER BY code, year;
  """, [years]).df()
    logging.getLogger(__name__).info("build_permits_metrics: returned rows=%d", len(df))
    return df


def build_cumulative_metrics(con: duckdb.DuckDBPyConnection, 
                             metros: pd.DataFrame, 
                             years: list[int] = [y for y in range(2014, 2024)], 
                             base_year: int = 2015) -> pd.DataFrame:
    years = sorted(set(years))
    assert len(years) > 1
    logging.getLogger(__name__).info("build_cumulative_metrics: metros=%d years=%s base_year=%s", len(metros), years, base_year)
    q = """
        WITH params AS (SELECT CAST(? AS INTEGER) AS base_year),

        filtered AS (
        SELECT i.*
        FROM inputs_percap i, params p
        JOIN metros m on m.code = i.code
        WHERE i.year >= p.base_year
        ),

        base AS (
        SELECT
            code,
            max(real_total_wages) FILTER (WHERE year = (SELECT base_year FROM params)) AS base_wage,
            max(total_permits)    FILTER (WHERE year = (SELECT base_year FROM params)) AS base_permits
        FROM filtered
        GROUP BY code
        )

        SELECT
        f.*,
        b.base_wage,
        b.base_permits,
        f.real_total_wages / nullif(b.base_wage, 0)      AS cumul_wage_index,
        f.total_permits    / nullif(b.base_permits, 0)  AS cumul_permit_index,
        (f.real_total_wages / nullif(b.base_wage, 0))
            / nullif((f.total_permits / nullif(b.base_permits, 0)), 0) AS structural_gap
        FROM filtered f
        JOIN base b USING (code)
        WHERE f.year IN (SELECT * FROM unnest(?))
        ORDER BY code, year;
        """
    df = con.execute(q, [base_year, years]).df()
    logging.getLogger(__name__).info("build_cumulative_metrics: returned rows=%d", len(df))
    return df
