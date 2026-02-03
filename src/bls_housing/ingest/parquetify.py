# bls_housing/ingest/parquetify.py

from __future__ import annotations

from pathlib import Path
import re
from time import perf_counter

from bls_housing.ingest.duck import get_analysis_db_connection


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

    
    print(f"[build-parquet-lake] done in {perf_counter() - t0:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())