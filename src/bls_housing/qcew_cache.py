"""Simple QCEW area CSV cache and loader utilities.

Functions:
- `qcew_get_area_url(year, qtr, area)` -> build download URL
- `fetch_area_csv(area, year, qtr, cache_dir, force_download)` -> returns local CSV path (uses cache)
- `load_area_df(area, year, qtr, cache_dir, **pd_read_csv_kwargs)` -> returns a pandas.DataFrame

The cache stores files under `cache_dir` (default: `data/cache`).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pandas as pd
import requests


def qcew_get_area_url(year: str, qtr: str, area: str) -> str:
    """Return the QCEW area CSV download URL for given year, quarter, and area code.

    Example: qcew_get_area_url("2025", "1", "C4266")
    """
    url = "https://data.bls.gov/cew/data/api/[YEAR]/[QTR]/area/[AREA].csv"
    url = url.replace("[YEAR]", str(year))
    url = url.replace("[QTR]", str(qtr).lower())
    url = url.replace("[AREA]", str(area).upper())
    return url


def _cache_filename(area: str, year: str, qtr: str) -> str:
    return f"{area.upper()}_{year}_{qtr.lower()}.csv"


def _ensure_cache_dir(cache_dir: str) -> Path:
    p = Path(cache_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_cached_path(area: str, year: str, qtr: str, cache_dir: str = "data/cache") -> Optional[Path]:
    p = Path(cache_dir) / _cache_filename(area, year, qtr)
    return p if p.exists() else None


def fetch_area_csv(
    area: str,
    year: str,
    qtr: str,
    cache_dir: str = "data/cache",
    force_download: bool = False,
    *,
    timeout: int = 30,
) -> Path:
    """Return a local Path to the area CSV. Use cached file if present unless `force_download`.

    The function will download the CSV and save it into `cache_dir` when needed.
    Raises `requests.HTTPError` for non-200 responses.
    """
    cache_dir_path = _ensure_cache_dir(cache_dir)
    cached = get_cached_path(area, year, qtr, cache_dir)
    if cached and not force_download:
        return cached

    url = qcew_get_area_url(year, qtr, area)
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()

    out_path = cache_dir_path / _cache_filename(area, year, qtr)
    with open(out_path, "wb") as fh:
        fh.write(resp.content)

    return out_path


def load_area_df(
    area: str,
    year: str,
    qtr: str,
    cache_dir: str = "data/cache",
    force_download: bool = False,
    **pd_read_csv_kwargs,
) -> pd.DataFrame:
    """Fetch (or load from cache) and return a pandas DataFrame for the area CSV.

    Any additional keyword args are forwarded to `pandas.read_csv`.
    """
    csv_path = fetch_area_csv(area, year, qtr, cache_dir=cache_dir, force_download=force_download)
    return pd.read_csv(csv_path, **pd_read_csv_kwargs)


__all__ = [
    "qcew_get_area_url",
    "fetch_area_csv",
    "get_cached_path",
    "load_area_df",
]
