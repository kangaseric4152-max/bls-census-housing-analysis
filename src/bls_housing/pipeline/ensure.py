# src/bls_housing/pipeline/ensure.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from bls_housing.pipeline.wages import build_annual_wages
from bls_housing.pipeline.permits import build_annual_permits


DERIVED_DIR = Path(__file__).resolve().parents[3] / "data" / "derived"
DERIVED_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class EnsureResult:
    df_tuple: tuple[pd.DataFrame, pd.DataFrame]
    missing_keys: set[tuple[int, int]]  # (Code, Year)


def _read_parquet_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def _expected_keys(metros: pd.DataFrame, years: Iterable[int]) -> set[tuple[int, int]]:
    codes = metros["Code"].astype("int64").tolist()
    return {(int(c), int(y)) for c in codes for y in years}


def _existing_keys(df: pd.DataFrame) -> set[tuple[int, int]]:
    if df.empty:
        return set()
    
    return set(map(tuple, df[["Code", "Year"]].astype("int64").to_numpy()))


def _upsert_parquet(path: Path, df_new: pd.DataFrame, key_cols: list[str]) -> pd.DataFrame:
    """
    Upsert by key into a single parquet file:
      - read old (if exists)
      - concat new
      - drop duplicates on key (keep last)
      - sort and write back
    Returns the full updated dataframe.
    """
    if path.exists():
        df_old = pd.read_parquet(path)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new.copy()

    # normalize key dtypes
    for k in key_cols:
        df_all[k] = df_all[k].astype("int64")

    df_all = df_all.drop_duplicates(subset=key_cols, keep="last")
    df_all = df_all.sort_values(key_cols).reset_index(drop=True)
    df_all.to_parquet(path, index=False)
    return df_all


def ensure_annual_wages(
    metros: pd.DataFrame,
    years: list[int],
    quarters: list[int] = [1, 2, 3, 4],
    parquet_name: str = "annual_wages.parquet",
) -> EnsureResult:
    """
    Ensure derived annual wages data exists for all (Code, Year) keys in metros x years.
    Rebuilds missing keys using build_annual_wages and upserts to parquet.
    """
    path = DERIVED_DIR / parquet_name

    df_existing = _read_parquet_if_exists(path)
    expected = _expected_keys(metros, years)
    existing = _existing_keys(df_existing)
    missing = expected - existing

    (wages_df, df_new) = (pd.DataFrame(), pd.DataFrame())
    missing_codes = sorted({code for code, _ in missing})

    if missing_codes:
        metros_missing = metros[metros["Code"].isin(missing_codes)]
        (wages_df, df_new) = build_annual_wages(metros_missing, years, quarters)

        # sanity: ensure key columns exist
        if not {"Code", "Year"}.issubset(df_new.columns):
            raise ValueError(f"build_annual_wages output missing Code/Year columns: {df_new.columns}")

        df_updated = _upsert_parquet(path, df_new, key_cols=["Code", "Year"])
    else:
        df_updated = df_existing

    # return only the subset needed for the current run
    codes = set(metros["Code"].astype("int64").tolist())
    df_subset = df_updated[
        df_updated["Code"].astype("int64").isin(codes)
        & df_updated["Year"].astype("int64").isin([int(y) for y in years])
    ].copy()

    return EnsureResult((wages_df, df_subset), missing_keys=missing)


def ensure_annual_permits(
    metros: pd.DataFrame,
    years: list[int],
    parquet_name: str = "annual_permits.parquet",
) -> EnsureResult:
    """
    Ensure derived annual permits data exists for all (Code, Year) keys in metros x years.
    Rebuilds missing keys using build_annual_permits and upserts to parquet.
    """
    path = DERIVED_DIR / parquet_name

    df_existing = _read_parquet_if_exists(path)
    expected = _expected_keys(metros, years)
    existing = _existing_keys(df_existing)
    
    (permits_df, df_new) = (pd.DataFrame(), pd.DataFrame())
    missing = expected - existing
    missing_codes = sorted({code for code, _ in missing})
    if missing_codes:
        metros_missing = metros[metros["Code"].isin(missing_codes)]
        (permits_df, df_new) = build_annual_permits(metros_missing, years)
    
        if not {"Code", "Year"}.issubset(df_new.columns):
            raise ValueError(f"build_annual_permits output missing Code/Year columns: {df_new.columns}")

        df_updated = _upsert_parquet(path, df_new, key_cols=["Code", "Year"])
    else:
        df_updated = df_existing

    codes = set(metros["Code"].astype("int64").tolist())
    df_subset = df_updated[
        df_updated["Code"].astype("int64").isin(codes)
        & df_updated["Year"].astype("int64").isin([int(y) for y in years])
    ].copy()

    return EnsureResult((permits_df, df_subset), missing_keys=missing)