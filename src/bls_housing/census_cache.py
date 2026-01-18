"""Simple census area XLS cache and loader utilities.


The cache stores files under `cache_dir/census/xls` (default: `[project root]/data/cache/census/xls`).
"""

from __future__ import annotations

# import os
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from bls_housing.census_txt_parser import convert_census_txt_to_csv

# Repository root (two levels up from this file: src/bls_housing -> src -> repo root)
REPO_ROOT = Path(__file__).resolve().parents[2]
XLS_DIR = REPO_ROOT / "data" / "cache" / "census" / "xls"
XLS_DIR.mkdir(parents=True, exist_ok=True)
CSV_DIR = REPO_ROOT / "data" / "cache" / "census" / "csv"
CSV_DIR.mkdir(parents=True, exist_ok=True)
RAW_TXT_DIR = REPO_ROOT / "data" / "cache" / "census" / "txt"
RAW_TXT_DIR.mkdir(parents=True, exist_ok=True)
CLEAN_CSV_DIR = REPO_ROOT / "data" / "cache" / "census" / "csv"
CLEAN_CSV_DIR.mkdir(parents=True, exist_ok=True)

def get_census_cbsa_url(year: str, mon: str) -> str:
    """Return the census area XLS download URL for given year, month, and CBSA code
    from late 2019 onwards.

    Example: get_census_cbsa_url("2025", "1")
    """
    if(len(mon) == 1):
        mon = f"0{mon}"


    # txt format from 2009 to Oct 2019
    # https://www.census.gov/construction/bps/txt/tb3u201910.txt
    # format for Nov 2019-2023 
    # https://www.census.gov/construction/bps/xls/msamonthly_202301.xls
    # format from 2024 onwards
    # https://www.census.gov/construction/bps/xls/cbsamonthly_202401.xls

    if(int(year) < 2009):
        raise NotImplementedError("Census CBSA URLs for years before 2009 are not implemented.")
    elif(int(year) < 2019):
        url = "https://www.census.gov/construction/bps/txt/tb3u[YEAR][MON].txt"
    elif (int(year) == 2019):
        if(int(mon) < 11):
            url = "https://www.census.gov/construction/bps/txt/tb3u[YEAR][MON].txt"
        else: #Nov 2019 onwards uses xls format
            url = "https://www.census.gov/construction/bps/xls/msamonthly_[YEAR][MON].xls"  
    elif(int(year) < 2024):
        url = "https://www.census.gov/construction/bps/xls/msamonthly_[YEAR][MON].xls"
    else:
        url = "https://www.census.gov/construction/bps/xls/cbsamonthly_[YEAR][MON].xls"
    url = url.replace("[YEAR]", str(year))
    url = url.replace("[MON]", str(mon).lower())
    return url


def _norm_mon(mon: str) -> str:
    mon = str(mon)
    if len(mon) == 1:
        mon = f"0{mon}"
    return mon


def _xls_filename(year: str, mon: str) -> str:
    mon = _norm_mon(mon)
    return f"cbsamonthly_{year}{mon}.xls"


def _csv_filename(year: str, mon: str) -> str:
    mon = _norm_mon(mon)
    return f"CBSA_{year}_{mon}.csv"


def _ensure_cache_dir(cache_dir: str | Path = XLS_DIR) -> Path:
    p = Path(cache_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_cached_xls_path(year: str, mon: str, cache_dir: str | Path = XLS_DIR) -> Optional[Path]:
    p = Path(cache_dir) / _xls_filename(year, mon)
    return p if p.exists() else None


def get_cached_csv_path(year: str, mon: str, cache_dir: str | Path = CSV_DIR) -> Optional[Path]:
    p = Path(cache_dir) / _csv_filename(year, mon)
    return p if p.exists() else None

def get_cached_txt_path(year: str, mon: str, cache_dir: str | Path = RAW_TXT_DIR) -> Optional[Path]:
    p = Path(cache_dir) / f"tb3u{year}{_norm_mon(mon)}.txt"
    return p if p.exists() else None


def fetch_census_txt(
    year: str,
    mon: str,
    cache_dir: str | Path = RAW_TXT_DIR,
    force_download: bool = False,
    *,
    timeout: int = 30,
) -> Path:
    """Return a local Path to the census TXT. Use cached file if present unless `force_download`."""
    cache_dir_path = _ensure_cache_dir(cache_dir)
    cached = get_cached_txt_path(year, mon, cache_dir_path)
    if cached and not force_download:
        return cached       
    url = get_census_cbsa_url(year, mon)
    try:
        resp = requests.get(url, timeout=timeout)
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download {url}: {e}") from e
    if resp.status_code >= 400:
        raise RuntimeError(f"Failed to download {url}: HTTP {resp.status_code}")        
    out_path = cache_dir_path / f"tb3u{year}{_norm_mon(mon)}.txt"
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    with open(tmp_path, "wb") as fh:
        fh.write(resp.content)
    tmp_path.replace(out_path)
    return out_path


def fetch_cbsa_xls(
    year: str,
    mon: str,
    cache_dir: str | Path = XLS_DIR,
    force_download: bool = False,
    *,
    timeout: int = 30,
) -> Path:
    """Return a local Path to the CBSA XLS. Use cached file if present unless `force_download`."""
    cache_dir_path = _ensure_cache_dir(cache_dir)
    cached = get_cached_xls_path(year, mon, cache_dir_path)
    if cached and not force_download:
        return cached

    url = get_census_cbsa_url(year, mon)
    try:
        resp = requests.get(url, timeout=timeout)
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download {url}: {e}") from e
    if resp.status_code >= 400:
        raise RuntimeError(f"Failed to download {url}: HTTP {resp.status_code}")

    out_path = cache_dir_path / _xls_filename(year, mon)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    with open(tmp_path, "wb") as fh:
        fh.write(resp.content)
    tmp_path.replace(out_path)

    return out_path


def clean_and_convert_xls_to_csv(xls_path: Path, csv_path: Path) -> None:
    """Convert the census CBSA XLS to a cleaned CSV file."""
    import pandas as pd
    df = pd.read_excel(xls_path, header=None)

    # Find the header row by looking for the 'CSA' or 'CBSA' label (robust to shifted rows)
    header_idx = None
    for idx, row in df.iterrows():
        try:
            vals = row.astype(str).str.strip().str.upper()
            if (vals == "CSA").any() or (vals == "CBSA").any():
                header_idx = idx
                break
        except Exception:
            continue

    if header_idx is None:
        # Fallback to previous approach (skip first 6 rows)
        header_idx = 6

    df = df.iloc[header_idx:]
    new_header = df.iloc[0]
    df = df[1:]

    # Build clean column names and make them unique.
    new_cols: list[str] = []
    seen: dict[str, int] = {}
    for col in new_header:
        key = col if isinstance(col, str) else str(col)
        key = key.strip() if isinstance(key, str) else key
        # represent empty-like values consistently
        if key == "" or key.lower() == "nan":
            key = "nan"

        count = seen.get(key, 0)
        if count == 0:
            new_name = key
        else:
            # first duplicate becomes _year_to_date, subsequent get numbered suffixes
            if count == 1:
                new_name = f"{key}_year_to_date"
            else:
                new_name = f"{key}_year_to_date_{count}"
        new_cols.append(new_name)
        seen[key] = count + 1

    df.columns = new_cols

    # Basic validation: ensure a few expected columns are present
    expected = ["CBSA", "Name", "Total"]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing expected columns in cleaned CSV: {missing}. "
            f"Source XLS: {xls_path}, detected header row starting at index {header_idx}"
        )

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)


def fetch_cbsa_csv(
    year: str,
    mon: str,
    csv_cache_dir: str | Path = CSV_DIR,
    xls_cache_dir: str | Path = XLS_DIR,
    force_download: bool = False,
) -> Path:
    """Return a local Path to the cleaned CBSA CSV, converting from XLS or TXT if necessary."""
    csv_cache_dir = _ensure_cache_dir(csv_cache_dir)
    cached = get_cached_csv_path(year, mon, csv_cache_dir)
    if cached and not force_download:
        return cached

    # if before Nov 2019, use txt format
    if(int(year) < 2019 or (int(year) == 2019 and int(mon) < 11)):
        # Ensure TXT is downloaded
        txt_path = fetch_census_txt(year, mon, cache_dir=RAW_TXT_DIR, force_download=force_download)
        out_csv = Path(csv_cache_dir) / _csv_filename(year, mon)
        convert_census_txt_to_csv(txt_path, out_csv)
        return out_csv


    # Ensure XLS is downloaded
    xls_path = fetch_cbsa_xls(year, mon, cache_dir=xls_cache_dir, force_download=force_download)

    out_csv = Path(csv_cache_dir) / _csv_filename(year, mon)
    clean_and_convert_xls_to_csv(xls_path, out_csv)
    return out_csv


# Load area CSV into pandas DataFrame, with caching
# If before Nov 2019, use old txt format parser instead of xls, 
# branch into alternate loading path

def load_cbsa_df(
    year: str,
    mon: str,
    csv_cache_dir: str | Path = CSV_DIR,
    xls_cache_dir: str | Path = XLS_DIR,
    force_download: bool = False,
    **pd_read_csv_kwargs,
) -> pd.DataFrame:
    """Fetch (or load from cache) and return a pandas DataFrame for the CBSA CSV.

    Any additional keyword args are forwarded to `pandas.read_csv`.
    """
    csv_path = fetch_cbsa_csv(year, mon, csv_cache_dir=csv_cache_dir, xls_cache_dir=xls_cache_dir, force_download=force_download)
    df = pd.read_csv(csv_path, **pd_read_csv_kwargs)

    # Basic validation for expected Census CBSA columns
    expected = ["CBSA", "Name", "Total"]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing expected Census CBSA columns: {missing}. Source CSV: {csv_path}"
        )

    return df



__all__ = [
    "get_census_cbsa_url",
    "fetch_cbsa_xls",
    "fetch_cbsa_csv",
    "get_cached_xls_path",
    "get_cached_csv_path",
    "clean_and_convert_xls_to_csv",
    "load_cbsa_df",
]
