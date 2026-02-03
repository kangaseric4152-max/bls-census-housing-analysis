# bls_housing/pipeline/parquetify.py

from __future__ import annotations

from pathlib import Path
import re
from time import perf_counter
from typing import Optional

from bls_housing.pipeline.duck import get_analysis_db_connection


PROJECT_ROOT = Path(__file__).parents[3].resolve()

# -----------------------
# BLS (existing)
# -----------------------
bls_dir = PROJECT_ROOT / "data" / "cache" / "bls"
BLS_LAKE_ROOT = PROJECT_ROOT / "data" / "lake" / "bls"


def build_bls_manifest(con) -> int:
    pat = re.compile(r"C(\d{4})_(\d{4})_([1-4])\.csv$")
    rows = []
    for p in bls_dir.glob("C????_????_?.csv"):
        m = pat.search(p.name)
        if not m:
            continue
        qcew_area, year, qtr = m.groups()
        rows.append((
            f"C{qcew_area}",
            int(qcew_area) * 10,   # cbsa_code
            int(year),
            int(qtr),
            str(p.resolve()),
        ))

    con.execute("""
        CREATE OR REPLACE TABLE bls_raw_manifest(
            qcew_area VARCHAR,
            cbsa_code BIGINT,
            year BIGINT,
            quarter BIGINT,
            src_csv VARCHAR
        )
    """)
    con.executemany("INSERT INTO bls_raw_manifest VALUES (?, ?, ?, ?, ?)", rows)
    return con.sql("select count(*) as rows from bls_raw_manifest").df()["rows"].iloc[0]


def build_bls_parquet(con, force: bool = False) -> tuple[int, int]:
    written, skipped = 0, 0

    rows = con.execute("""
        SELECT cbsa_code, year, quarter, src_csv
        FROM bls_raw_manifest
        ORDER BY cbsa_code, year, quarter
    """).fetchall()

    for cbsa_code, year, quarter, src_csv in rows:
        out_dir = BLS_LAKE_ROOT / f"cbsa_code={cbsa_code}" / f"year={year}" / f"quarter={quarter}"
        out_path = out_dir / "data.parquet"

        if out_path.exists() and not force:
            skipped += 1
            continue

        out_dir.mkdir(parents=True, exist_ok=True)

        con.execute(f"""
            COPY (
                SELECT *
                FROM read_csv_auto('{src_csv.replace("'", "''")}')
            )
            TO '{str(out_path).replace("'", "''")}'
            (FORMAT PARQUET);
        """)
        written += 1

    return written, skipped


# -----------------------
# PERMITS 
# -----------------------

CENSUS_CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "census" / "csv"
CENSUS_LAKE_ROOT = PROJECT_ROOT / "data" / "lake" / "census_permits"

def build_census_permits_parquet(con, force: bool = False, partition_cbsa: bool = False) -> int:
    """
    Convert monthly Census permits CSVs (CBSA_YYYY_MM.csv) into a Parquet lake.
    Default partitioning: year/month. Optional: cbsa_code/year/month.
    """
    CENSUS_LAKE_ROOT.mkdir(parents=True, exist_ok=True)

    # If you want "force", easiest is delete the lake folder, or write to a temp folder then swap.
    # Keeping it simple:
    if force and CENSUS_LAKE_ROOT.exists():
        # careful: this deletes your permits lake
        import shutil
        shutil.rmtree(CENSUS_LAKE_ROOT)
        CENSUS_LAKE_ROOT.mkdir(parents=True, exist_ok=True)

    # Parse year/month from filename
    # DuckDB gives full path in "filename" column when filename=true
    part_cols = "cbsa_code, year, month" if partition_cbsa else "year, month"

    con.execute(f"""
        COPY (
          WITH raw AS (
            SELECT
              filename,
              *
            FROM read_csv_auto('{str(CENSUS_CACHE_DIR / "*.csv").replace("'", "''")}',
                              union_by_name=true,
                              filename=true)
          ),
          tagged AS (
            SELECT
              CAST(regexp_extract(filename, 'CBSA_(\\d{{4}})_(\\d{{2}})\\.csv$', 1) AS INTEGER) AS year,
              CAST(regexp_extract(filename, 'CBSA_(\\d{{4}})_(\\d{{2}})\\.csv$', 2) AS INTEGER) AS month,
              CAST("CBSA" AS BIGINT) AS cbsa_code,

              -- Keep whatever you need downstream; examples:
              CAST("Total" AS BIGINT) AS total_permits,
              CAST("1 Unit" AS BIGINT) AS permits_1_unit,
              CAST("2 Unit" AS BIGINT) AS permits_2_unit,
              CAST("3 and 4 Units" AS BIGINT) AS permits_3_4_units,
              CAST("5 Units or More" AS BIGINT) AS permits_5_plus,

              "Name" AS area_name,
              CAST("Metro /Micro Code" AS INTEGER) AS metro_micro_code

            FROM raw
            WHERE regexp_matches(filename, 'CBSA_\\d{{4}}_\\d{{2}}\\.csv$')
          )
          SELECT * FROM tagged
        )
        TO '{str(CENSUS_LAKE_ROOT).replace("'", "''")}'
        (FORMAT PARQUET, PARTITION_BY ({part_cols}), OVERWRITE true);
    """)

    # DuckDB COPY doesn't directly return "files written", so return rowcount as a sanity stat
    n = con.execute(f"""
        SELECT count(*) FROM read_parquet('{str(CENSUS_LAKE_ROOT).replace("'", "''")}/**/*.parquet',
                                         hive_partitioning=1)
    """).fetchone()[0]
    return n


# -----------------------
# CLI entrypoint
# -----------------------
def main() -> int:
    t0 = perf_counter()
    print("[build-parquet-lake] starting...")

    with get_analysis_db_connection() as con:
        # BLS
        bls_n = build_bls_manifest(con)
        print(f"[build-parquet-lake] bls manifest rows: {bls_n} in {perf_counter() - t0:.2f}s")
        if bls_n:
            w, s = build_bls_parquet(con)
            print(f"[build-parquet-lake] bls parquet written: {w}, skipped: {s}")
        else:
            print("[build-parquet-lake] bls: no source files found")

        # Permits
    
        n = build_census_permits_parquet(con)
        print(f"[build-parquet-lake] permits parquet written: {n}")
    
    print(f"[build-parquet-lake] done in {perf_counter() - t0:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())