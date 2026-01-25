# • helper: duck_con(db_path), register_parquet_views(con) etc.
from typing import List
from pathlib import Path
import duckdb
import pandas as pd

DBPATH = Path("../data/analysis.duckdb") 
def get_analysis_db_connection(dbpath: str | Path = DBPATH):
    return duckdb.connect(Path(dbpath))


def list_metros(con: duckdb.DuckDBPyConnection, codes: List[int]) -> pd.DataFrame:
    return con.execute("""
        SELECT Code, Area, Title
        FROM dim_metro_full
        WHERE Code IN (SELECT * FROM UNNEST(?))
        ORDER BY Area, Title
    """, [codes]).df()


def update_db(con: duckdb.DuckDBPyConnection, 
              final_df: pd.DataFrame, 
              cumulative_df: pd.DataFrame, 
              wages_df: pd.DataFrame, 
              permits_df: pd.DataFrame):
    con.execute("""
            CREATE OR REPLACE TABLE annual_metrics_stage AS SELECT * FROM final_df;
            BEGIN TRANSACTION;
            DELETE FROM annual_metrics t
            USING annual_metrics_stage s
            WHERE t.Code = s.Code AND t.Year = s.Year;
            INSERT INTO annual_metrics (
                Area, Code, Year, Total_Wages, Real_Total_Wages, Change_Real_Wage,
                Total_Permits, Change_Permit, Wage_Index, Permit_Index, Zoning_Pressure
            )
            SELECT
                Area, Code, Year, Total_Wages, Real_Total_Wages, Change_Real_Wage,
                Total_Permits, Change_Permit, Wage_Index, Permit_Index, Zoning_Pressure
            FROM annual_metrics_stage;
            COMMIT;
            """)
    con.execute("""
            CREATE OR REPLACE TABLE cumulative_metrics_stage AS SELECT * FROM cumulative_df;
            BEGIN TRANSACTION;
            DELETE FROM cumulative_metrics t
            USING cumulative_metrics_stage s
            WHERE t.Code = s.Code AND t.Year = s.Year;
            INSERT INTO cumulative_metrics (
                Area, Code, Year, Real_Total_Wages, Total_Permits, Base_Wage, 
                Base_Permits, Cumul_Wage_Index, Cumul_Permit_Index, Structural_Gap
            )
            SELECT
                Area, Code, Year, Real_Total_Wages, Total_Permits, Base_Wage, 
                Base_Permits, Cumul_Wage_Index, Cumul_Permit_Index, Structural_Gap
            FROM cumulative_metrics_stage;
            COMMIT;
            """)
    if(wages_df.size>0):
        con.execute("""
            CREATE OR REPLACE TABLE wages_metrics_stage AS SELECT * FROM wages_df;
            BEGIN TRANSACTION;
            DELETE FROM wages_metrics t
            USING wages_metrics_stage s
            WHERE t.Code = s.Code 
                AND t.Year = s.Year
                AND t.Quarter = s.Quarter;
            INSERT INTO wages_metrics (
                Area, Code, Year, Quarter, Total_Wages
            )
            SELECT
                Area, Code, Year, Quarter, Total_Wages
            FROM wages_metrics_stage;
            COMMIT;
            """)
    if(permits_df.size>0):
        con.execute("""
            CREATE OR REPLACE TABLE permits_metrics_stage AS SELECT * FROM permits_df;
            BEGIN TRANSACTION;
            DELETE FROM permits_metrics t
            USING   permits_metrics_stage s
            WHERE   t.Code = s.Code 
                    AND t.Year = s.Year
                    AND t.Quarter = s.Quarter;
                    AND t.Month = s.Month;
            INSERT INTO permits_metrics (
                Area, Code, Year, Quarter, Month, Total_Permits
            )
            SELECT
                Area, Code, Year, Quarter, Month, Total_Permits
            FROM permits_metrics_stage;
            COMMIT;    
            """)

    con.execute(
"""
CREATE TABLE IF NOT EXISTS build_meta (
  table_name VARCHAR,
  last_built TIMESTAMP
);
""")


# def list_metros_2(con, title_like: str | None = None):
#     if title_like:
#         return con.sql("""
#             SELECT Code, Area, Title
#             FROM dim_metro_full
#             WHERE Title LIKE ?
#             ORDER BY Title, Area
#         """, [title_like]).df()

#     return con.sql("""
#         SELECT Code, Area, Title
#         FROM dim_metro_full
#         ORDER BY Title, Area
#     """).df()