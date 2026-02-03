# src/bls_housing/cli/ingest_data.py

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd
import duckdb

from bls_housing.ingest.ensure_lake import ensure_qcew_lake, ensure_permits_csv


def _parse_int_range(s: str) -> list[int]:
    # "2019-2023" -> [2019..2023], "2020" -> [2020]
    if "-" in s:
        a, b = s.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(s)]


def _parse_int_list_or_range(s: str) -> list[int]:
    # "1-4" -> [1..4], "1,3" -> [1,3]
    s = s.strip()
    if not s:
        return []
    if "-" in s:
        a, b = s.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    # normalize column names to lowercase for matching
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def _require_cols(df: pd.DataFrame, required: Iterable[str], *, context: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(
            f"[ingest-data] SQL result missing required columns {missing} for {context}. "
            f"Got columns: {list(df.columns)}"
        )


def _apply_limit(df: pd.DataFrame, limit: int | None) -> pd.DataFrame:
    if limit is None:
        return df
    if limit <= 0:
        raise SystemExit("--limit must be a positive integer")
    return df.head(limit).copy()


def _connect(db_path: Path) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(db_path))


def _apply_sets(con: duckdb.DuckDBPyConnection, sets: list[str]) -> None:
    # --set project_root=/path --set foo=bar
    for item in sets:
        if "=" not in item:
            raise SystemExit(f"--set expects name=value, got: {item!r}")
        name, value = item.split("=", 1)
        name = name.strip()
        value = value.strip()
        if not name:
            raise SystemExit(f"--set expects name=value, got: {item!r}")
        # DuckDB variable values are strings here; user can cast in SQL if needed
        safe_value = value.replace("'", "''")
        con.execute(f"SET VARIABLE {name} = '{safe_value}';")


def _load_keys_from_sql(
    *,
    dataset: str,
    sql_file: Path,
    db_path: Path,
    sets: list[str],
    limit: int | None,
) -> tuple[pd.DataFrame | None, list[int], list[int], list[int] | None]:
    """
    Returns:
      - metros_df (for qcew) or None (for permits)
      - years
      - months (permits) OR quarters (qcew)
      - quarters (qcew) OR None (permits)

    Note: for qcew, returns (metros_df, years, quarters, None)
          for permits, returns (None, years, months, None)
    """
    if not sql_file.exists():
        raise SystemExit(f"--sql-file not found: {sql_file}")

    sql = sql_file.read_text(encoding="utf-8")

    with _connect(db_path) as con:
        _apply_sets(con, sets)
        df = con.execute(sql).df()

    df = _normalize_cols(df)
    df = _apply_limit(df, limit)

    if df.empty:
        raise SystemExit("[ingest-data] SQL query returned 0 rows; nothing to ingest.")

    if dataset == "qcew":
        # allow code or cbsa_code
        if "cbsa_code" not in df.columns and "code" in df.columns:
            df = df.rename(columns={"code": "cbsa_code"})
        _require_cols(df, ["cbsa_code", "year", "quarter"], context="dataset=qcew")

        # coerce to ints and dedupe
        df = df[["cbsa_code", "year", "quarter"]].copy()
        df["cbsa_code"] = df["cbsa_code"].astype("int64")
        df["year"] = df["year"].astype("int64")
        df["quarter"] = df["quarter"].astype("int64")
        df = df.drop_duplicates().sort_values(["cbsa_code", "year", "quarter"])

        metros = pd.DataFrame({"Code": sorted(df["cbsa_code"].unique().tolist())})
        years = sorted(df["year"].unique().tolist())
        quarters = sorted(df["quarter"].unique().tolist())

        return metros, years, quarters, None

    else:
        _require_cols(df, ["year", "month"], context="dataset=permits")

        df = df[["year", "month"]].copy()
        df["year"] = df["year"].astype("int64")
        df["month"] = df["month"].astype("int64")
        df = df.drop_duplicates().sort_values(["year", "month"])

        years = sorted(df["year"].unique().tolist())
        months = sorted(df["month"].unique().tolist())
        return None, years, months, None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", choices=["qcew", "permits"], required=True)

    # New: drive ingestion from SQL results
    p.add_argument("--sql-file", default="", help="SQL file that returns ingestion keys (see README)")
    p.add_argument("--db", default="data/analysis.duckdb", help="DuckDB path for running --sql-file")
    p.add_argument(
        "--set",
        action="append",
        default=[],
        help="Set a DuckDB variable for --sql-file, e.g. --set project_root=/path/to/repo",
    )
    p.add_argument("--dry-run", action="store_true", help="Print what would be ingested and exit")
    p.add_argument("--limit", type=int, default=None, help="Limit SQL key rows (safety)")

    # Existing parameter mode (kept)
    p.add_argument("--years", default="", help="e.g. 2019-2023 or 2022 (ignored if --sql-file)")
    p.add_argument("--quarters", default="1-4", help="qcew only: e.g. 1-4 or 1,3 (ignored if --sql-file)")
    p.add_argument("--months", default="1-12", help="permits only: e.g. 1-12 or 1,2,3 (ignored if --sql-file)")
    p.add_argument("--cbsa", default="", help="qcew only: comma-separated CBSA codes (ignored if --sql-file)")

    p.add_argument("--force-download", action="store_true")
    p.add_argument("--force-parquet", action="store_true")

    args = p.parse_args()

    sql_file = Path(args.sql_file).expanduser() if args.sql_file else None
    db_path = Path(args.db).expanduser()

    if sql_file:
        metros, years, third, _ = _load_keys_from_sql(
            dataset=args.dataset,
            sql_file=sql_file,
            db_path=db_path,
            sets=args.set,
            limit=args.limit,
        )

        if args.dataset == "qcew":
            quarters = third
            assert metros is not None
            assert quarters is not None

            if args.dry_run:
                print("[ingest-data] mode=sql dataset=qcew")
                print(f"[ingest-data] metros={len(metros)} years={years} quarters={quarters}")
                print(metros.head(10).to_string(index=False))
                return 0

            st = ensure_qcew_lake(
                metros,
                years,
                quarters,
                force_download=args.force_download,
                force_parquet=args.force_parquet,
            )

        else:
            months = third

            if args.dry_run:
                print("[ingest-data] mode=sql dataset=permits")
                print(f"[ingest-data] years={years} months={months}")
                return 0

            st = ensure_permits_csv(
                years,
                months,
                force_download=args.force_download,
            )

    else:
        # legacy param mode
        if not args.years.strip():
            raise SystemExit("--years is required unless --sql-file is provided")

        years = _parse_int_range(args.years)

        if args.dataset == "qcew":
            if not args.cbsa.strip():
                raise SystemExit("--cbsa is required for dataset=qcew (e.g. --cbsa 17460,18140)")

            cbsa_codes = [int(x.strip()) for x in args.cbsa.split(",") if x.strip()]
            quarters = _parse_int_list_or_range(args.quarters)
            if not quarters:
                raise SystemExit("--quarters must not be empty for dataset=qcew")

            metros = pd.DataFrame({"Code": cbsa_codes})

            if args.dry_run:
                print("[ingest-data] mode=params dataset=qcew")
                print(f"[ingest-data] metros={cbsa_codes} years={years} quarters={quarters}")
                return 0

            st = ensure_qcew_lake(
                metros,
                years,
                quarters,
                force_download=args.force_download,
                force_parquet=args.force_parquet,
            )

        else:
            months = _parse_int_list_or_range(args.months)
            if not months:
                raise SystemExit("--months must not be empty for dataset=permits")

            if args.dry_run:
                print("[ingest-data] mode=params dataset=permits")
                print(f"[ingest-data] years={years} months={months}")
                return 0

            st = ensure_permits_csv(
                years,
                months,
                force_download=args.force_download,
            )

    print(
        f"[ingest-data] requested={st.requested} missing={st.missing} "
        f"fetched={st.fetched} parquet_written={st.parquet_written} skipped={st.parquet_skipped}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())