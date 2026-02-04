# bls_housing/ingest/parquetify.py

from __future__ import annotations

from pathlib import Path
import re
from time import perf_counter

from bls_housing.ingest.duck import get_analysis_db_connection
from bls_housing.logging_config import configure_logging
import logging

logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).parents[3].resolve()

# -----------------------
# BLS (existing)
# -----------------------
bls_dir = PROJECT_ROOT / "data" / "cache" / "bls"
BLS_LAKE_ROOT = PROJECT_ROOT / "data" / "lake" / "bls"


def build_bls_manifest(con) -> int:
    logger.info("build_bls_manifest start: scanning %s", bls_dir)
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

    logger.info("Found %d BLS CSV files to register", len(rows))

    con.execute("""
        CREATE OR REPLACE TABLE bls_raw_manifest(
            qcew_area VARCHAR,
            cbsa_code BIGINT,
            year BIGINT,
            quarter BIGINT,
            src_csv VARCHAR
        )
    """)
    if rows:
        con.executemany("INSERT INTO bls_raw_manifest VALUES (?, ?, ?, ?, ?)", rows)
    count = con.sql("select count(*) as rows from bls_raw_manifest").df()["rows"].iloc[0]
    logger.info("build_bls_manifest done: manifest_rows=%d", int(count))
    return int(count)


def build_bls_parquet(con, force: bool = False) -> tuple[int, int]:
    written, skipped = 0, 0

    rows = con.execute("""
        SELECT cbsa_code, year, quarter, src_csv
        FROM bls_raw_manifest
        ORDER BY cbsa_code, year, quarter
    """).fetchall()

    logger.info("build_bls_parquet start: partitions=%d force=%s", len(rows), force)

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

    logger.info("build_bls_parquet done: written=%d skipped=%d", written, skipped)
    return written, skipped


# -----------------------
# CLI entrypoint
# -----------------------
def main() -> int:
    t0 = perf_counter()
    configure_logging(level="INFO")
    logger.info("[build-parquet-lake] starting...")

    with get_analysis_db_connection() as con:
        # BLS
        bls_n = build_bls_manifest(con)
        logger.info("[build-parquet-lake] bls manifest rows: %d in %.2fs", bls_n, perf_counter() - t0)
        if bls_n:
            w, s = build_bls_parquet(con)
            logger.info("[build-parquet-lake] bls parquet written: %d skipped: %d", w, s)
        else:
            logger.info("[build-parquet-lake] bls: no source files found")

    logger.info("[build-parquet-lake] done in %.2fs", perf_counter() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())