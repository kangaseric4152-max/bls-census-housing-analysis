
# src/bls_housing/ingest/ensure_lake.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import logging

from bls_housing.ingest.duck import get_analysis_db_connection
from bls_housing.qcew_cache import fetch_area_csv
from bls_housing.census_cache import fetch_cbsa_csv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LAKE_BLS = PROJECT_ROOT / "data" / "lake" / "bls"

CACHE_BLS = PROJECT_ROOT / "data" / "cache" / "bls"
CACHE_CENSUS_CSV = PROJECT_ROOT / "data" / "cache" / "census" / "csv"

@dataclass(frozen=True)
class EnsureLakeStatus:
    requested: int
    present: int
    missing: int
    fetched: int
    parquet_written: int
    parquet_skipped: int
    missing_keys: list[tuple]  # concrete keys for debugging


def _metros_to_cbsa_codes(metros: pd.DataFrame) -> list[int]:
    # supports either Code or code column
    col = "Code" if "Code" in metros.columns else "code"
    return [int(x) for x in metros[col].astype("int64").tolist()]


def ensure_qcew_lake(
    metros: pd.DataFrame,
    years: Iterable[int],
    quarters: Iterable[int] = (1, 2, 3, 4),
    *,
    force_download: bool = False,
    force_parquet: bool = False,
    timeout: int = 30,
) -> EnsureLakeStatus:
    logger = logging.getLogger(__name__)
    cbsa_codes = _metros_to_cbsa_codes(metros)
    years = [int(y) for y in years]
    quarters = [int(q) for q in quarters]

    logger.info("ensure_qcew_lake start: metros=%d years=%s quarters=%s force_download=%s force_parquet=%s",
                len(cbsa_codes), years, quarters, force_download, force_parquet)

    requested_keys: list[tuple[int, int, int]] = [
        (cbsa, y, q) for cbsa in cbsa_codes for y in years for q in quarters
    ]

    # lake file path convention from your existing parquetify:
    # data/lake/bls/cbsa_code=<cbsa>/year=<year>/quarter=<q>/data.parquet
    def lake_path(cbsa: int, y: int, q: int) -> Path:
        return LAKE_BLS / f"cbsa_code={cbsa}" / f"year={y}" / f"quarter={q}" / "data.parquet"

    missing = [(cbsa, y, q) for (cbsa, y, q) in requested_keys if (not lake_path(cbsa, y, q).exists() or force_parquet)]

    fetched = 0
    parquet_written = 0
    parquet_skipped = 0

    with get_analysis_db_connection() as con:
        # 1) fetch missing CSVs into cache (uses your existing function)
        for cbsa, y, q in missing:
            area = f"C{cbsa // 10:04d}"  # 17460 -> C1746
            fetch_area_csv(
                area=area,
                year=str(y),
                qtr=str(q),
                cache_dir=CACHE_BLS,
                force_download=force_download,
                timeout=timeout,
            )
            fetched += 1

        # 2) parquetify only missing partitions
        for cbsa, y, q in missing:
            out = lake_path(cbsa, y, q)
            out.parent.mkdir(parents=True, exist_ok=True)

            # cached CSV naming pattern: C####_YYYY_Q.csv (per your manifest logic)
            src_csv = CACHE_BLS / f"C{cbsa // 10:04d}_{y}_{q}.csv"
            if not src_csv.exists():
                # leave it missing; this is useful when BLS returns 404 (like Cleveland 2024)
                continue

            if out.exists() and not force_parquet:
                parquet_skipped += 1
                continue

            con.execute(f"""
                COPY (
                    SELECT *
                    FROM read_csv_auto('{str(src_csv).replace("'", "''")}')
                )
                TO '{str(out).replace("'", "''")}'
                (FORMAT PARQUET);
            """)
            parquet_written += 1

    present = len(requested_keys) - len(missing) + parquet_written  # “best effort”; not perfect if 404s
    logger.info("ensure_qcew_lake done: requested=%d present=%d missing=%d fetched=%d parquet_written=%d parquet_skipped=%d",
                len(requested_keys), present, len(missing), fetched, parquet_written, parquet_skipped)
    return EnsureLakeStatus(
        requested=len(requested_keys),
        present=present,
        missing=len(missing),
        fetched=fetched,
        parquet_written=parquet_written,
        parquet_skipped=parquet_skipped,
        missing_keys=missing,
    )


def ensure_permits_csv(
    years: Iterable[int],
    months: Iterable[int] = range(1, 13),
    *,
    force_download: bool = False,

) -> EnsureLakeStatus:
    logger = logging.getLogger(__name__)
    years = [int(y) for y in years]
    months = [int(m) for m in months]
    requested_keys: list[tuple[int, int]] = [(y, m) for y in years for m in months]

    #missing = [
    #    (y, m) for (y, m) in requested_keys
    #]
    df = pd.DataFrame()

    with get_analysis_db_connection() as con:
        # check for missing census cache files.
        df = con.execute("""
            WITH date_range AS (
            SELECT year, mon
            FROM (SELECT UNNEST(?) AS year) y
            CROSS JOIN (SELECT UNNEST(?) AS mon) m
            ),
            files AS (
            SELECT file
            FROM glob(project_path('/data/cache/census/csv/CBSA_*.csv'))
            ),
            present AS (
            SELECT
                TRY_CAST(regexp_extract(file, 'CBSA_(\\d{4})_(\\d{2})\\.csv$', 1) AS INT) AS year,
                TRY_CAST(regexp_extract(file, 'CBSA_(\\d{4})_(\\d{2})\\.csv$', 2) AS INT) AS mon
            FROM files
            WHERE regexp_matches(file, 'CBSA_\\d{4}_\\d{2}\\.csv$')
            ),
            missing AS (
            SELECT d.year, d.mon
            FROM date_range d
            LEFT JOIN present p
                ON d.year = p.year AND d.mon = p.mon
            WHERE p.year IS NULL
            )
            SELECT year, mon
            FROM missing
            ORDER BY year, mon;
        """, [years, months]).df()

    missing: list[tuple[int, int]] = list(df.itertuples(index=False, name=None))
    assert all(1 <= m <= 12 for _, m in missing)
    logger.info("ensure_permits_csv start: years=%s months=%s force_download=%s",
                years, months, force_download)
    fetched = 0

    
    # 1) fetch/convert missing monthly CSVs into cache
    for y, m in missing:
        fetch_cbsa_csv(
            year=str(y),
            mon=f"{m:02d}",
            csv_cache_dir=CACHE_CENSUS_CSV,
            force_download=force_download,
        )
        fetched += 1

    present = len(requested_keys) - len(missing)
    logger.info("ensure_permits_csv done: requested=%d present=%d missing=%d fetched=%d",
                len(requested_keys), present, len(missing), fetched)

    return EnsureLakeStatus(
        requested=len(requested_keys),
        present=present,
        missing=len(missing),
        fetched=fetched,
        parquet_written=0,
        parquet_skipped=0,
        missing_keys=missing,
    )