# • helper: duck_con(db_path), register_parquet_views(con) etc.
from typing import List
from pathlib import Path
import duckdb
import pandas as pd

DBPATH = Path("../data/analysis.duckdb") 
def get_con(dbpath: str | Path = DBPATH):
    return duckdb.connect(Path(dbpath))


def close_con(con: duckdb.DuckDBPyConnection):
    con.close()


def list_metros(con: duckdb.DuckDBPyConnection, codes: List[int]) -> pd.DataFrame:
    return con.execute("""
        SELECT Code, Area, Title
        FROM dim_metro_full
        WHERE Code IN (SELECT * FROM UNNEST(?))
        ORDER BY Area, Title
    """, [codes]).df()


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