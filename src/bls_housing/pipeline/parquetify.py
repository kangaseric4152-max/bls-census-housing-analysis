# bls_housing/pipeline/parquetify.py

from pathlib import Path
from bls_housing.pipeline.duck import get_analysis_db_connection
import re
from time import perf_counter


PROJECT_ROOT = Path(__file__).parents[3].resolve()  # adjust to your layout
bls_dir = PROJECT_ROOT / "data" / "cache" / "bls"

def build_bls_manifest(con):

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
        str(p.resolve())
    ))

    con.execute("""
    CREATE OR REPLACE TABLE bls_raw_manifest(
        qcew_area VARCHAR,
        cbsa_code BIGINT,
        year BIGINT,
        quarter BIGINT,
        src_csv VARCHAR )
    """)
    con.executemany("INSERT INTO bls_raw_manifest VALUES (?, ?, ?, ?, ?)", rows)
    df = con.sql("select count(*) as rows from bls_raw_manifest").df()
    return df['rows'].iloc[0]


LAKE_ROOT = PROJECT_ROOT / "data" / "lake" / "bls"

def build_bls_parquet(con, force: bool = False) -> tuple[int,int]:
    (written, skipped) = (0,0)
  

    rows = con.execute("""
        SELECT cbsa_code, year, quarter, src_csv
        FROM bls_raw_manifest
        ORDER BY cbsa_code, year, quarter
    """).fetchall()

    for cbsa_code, year, quarter, src_csv in rows:
        out_dir = LAKE_ROOT / f"cbsa_code={cbsa_code}" / f"year={year}" / f"quarter={quarter}"
        out_path = out_dir / "data.parquet"

        if out_path.exists() and not force:
            skipped+=1
            continue

        out_dir.mkdir(parents=True, exist_ok=True)

        # Read the one CSV and write one Parquet
        con.execute(f"""
            COPY (
                SELECT *
                FROM read_csv_auto('{src_csv.replace("'", "''")}')
            )
            TO '{str(out_path).replace("'", "''")}'
            (FORMAT PARQUET);
        """)
        written+=1
    return (written, skipped)


def main() -> int:
    t0 = perf_counter()
    print("[build-parquet-lake] starting...")

    with get_analysis_db_connection() as con:
        manifest_count = build_bls_manifest(con)  # return int
        print(f"[build-parquet-lake] manifest rows: {manifest_count} in {perf_counter() - t0:.2f}s")

        if manifest_count == 0:
            print("[build-parquet-lake] no source files found; nothing to do.")
            print(f"[build-parquet-lake] done in {perf_counter() - t0:.2f}s")
            return 0

        written, skipped = build_bls_parquet(con)  # return (int, int)
        print(f"[build-parquet-lake] parquet written: {written}, skipped: {skipped}")

    print(f"[build-parquet-lake] done in {perf_counter() - t0:.2f}s")
    return 0


if __name__ == "__main__":
    main()