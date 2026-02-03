
# src/bls_housing/pipeline/ensure_lake.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import duckdb
import pandas as pd

from bls_housing.pipeline.duck import get_analysis_db_connection
from bls_housing.qcew_cache import fetch_area_csv
from bls_housing.census_cache import fetch_cbsa_csv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LAKE_BLS = PROJECT_ROOT / "data" / "lake" / "bls"
LAKE_PERMITS = PROJECT_ROOT / "data" / "lake" / "census_permits"

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
    cbsa_codes = _metros_to_cbsa_codes(metros)
    years = [int(y) for y in years]
    quarters = [int(q) for q in quarters]

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
    return EnsureLakeStatus(
        requested=len(requested_keys),
        present=present,
        missing=len(missing),
        fetched=fetched,
        parquet_written=parquet_written,
        parquet_skipped=parquet_skipped,
        missing_keys=missing,
    )


def ensure_permits_lake(
    years: Iterable[int],
    months: Iterable[int] = range(1, 13),
    *,
    force_download: bool = False,
    force_parquet: bool = False,
) -> EnsureLakeStatus:
    years = [int(y) for y in years]
    months = [int(m) for m in months]
    requested_keys: list[tuple[int, int]] = [(y, m) for y in years for m in months]

    # Partition directory convention (use integer month, no zero pad)
    def part_dir(y: int, m: int) -> Path:
        return LAKE_PERMITS / f"year={y}" / f"month={m}"

    def partition_has_parquet(y: int, m: int) -> bool:
        d = part_dir(y, m)
        return d.exists() and any(d.glob("*.parquet"))

    missing = [
        (y, m) for (y, m) in requested_keys
        if force_parquet or not partition_has_parquet(y, m)
    ]

    fetched = 0
    parquet_written = 0
    parquet_skipped = 0

    with get_analysis_db_connection() as con:
        # 1) fetch/convert missing monthly CSVs into cache
        for y, m in missing:
            fetch_cbsa_csv(
                year=str(y),
                mon=f"{m:02d}",
                csv_cache_dir=CACHE_CENSUS_CSV,
                force_download=force_download,
            )
            fetched += 1

        # 2) canonical parquet writer ONLY
        # Option 1 (recommended): write partitions for just the requested (y,m)
        # by filtering filenames and projecting a canonical schema.
        #
        # This avoids "rebuild whole lake" and avoids a second schema.
        #
        if missing:
            # You can either:
            # - write each (y,m) partition individually (OVERWRITE true for that partition)
            # - OR run one COPY that filters to only missing months and partitions by year/month
            #
            # This is the "one writer" SQL pattern, but targeted to only missing months.

            for y, m in missing:
                src = CACHE_CENSUS_CSV / f"CBSA_{y}_{m:02d}.csv"
                if not src.exists():
                    continue

                out_dir = part_dir(y, m)
                out_dir.mkdir(parents=True, exist_ok=True)

                # If already present and not forcing, skip
                if partition_has_parquet(y, m) and not force_parquet:
                    parquet_skipped += 1
                    continue

                con.execute(f"""
                    COPY (
                        SELECT
                            CAST({y} AS INTEGER) AS year,
                            CAST({m} AS INTEGER) AS month,
                            CAST("CBSA" AS BIGINT) AS cbsa_code,

                            CAST("Total" AS BIGINT) AS total_permits,
                            CAST("1 Unit" AS BIGINT) AS permits_1_unit,
                            CAST("2 Unit" AS BIGINT) AS permits_2_unit,
                            CAST("3 and 4 Units" AS BIGINT) AS permits_3_4_units,
                            CAST("5 Units or More" AS BIGINT) AS permits_5_plus,

                            "Name" AS area_name,
                            CAST("Metro /Micro Code" AS INTEGER) AS metro_micro_code
                        FROM read_csv_auto('{str(src).replace("'", "''")}', union_by_name=true)
                    )
                    TO '{str(out_dir).replace("'", "''")}'
                    (FORMAT PARQUET, OVERWRITE true);
                """)
                parquet_written += 1

    present = len(requested_keys) - len(missing) + parquet_written
    return EnsureLakeStatus(
        requested=len(requested_keys),
        present=present,
        missing=len(missing),
        fetched=fetched,
        parquet_written=parquet_written,
        parquet_skipped=parquet_skipped,
        missing_keys=missing,
    )