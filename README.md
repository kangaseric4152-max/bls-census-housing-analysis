## BLS & Census Housing — notebooks and utilities

This repository provides small, reusable utilities and a Jupyter notebook to fetch, cache, and analyze area-level housing and employment data from the U.S. Bureau of Labor Statistics (QCEW) and the U.S. Census (Building Permits Survey — BPS).

The current notebook focuses on aggregating CBSA-level wage and housing permit data and computing year-over-year changes; it does not attempt to model prices, completions, or causality.

Two complementary pressure metrics are used: an annual ratio of growth rates and a cumulative index relative to a base year.

The project is intentionally lightweight and written for learning and reproducible exploration. Current features implemented:

- Helpers to download and cache BLS QCEW area CSVs (quarterly area data).
- Helpers to download Census BPS monthly CBSA XLS files, convert and clean them, and cache cleaned CSVs for fast re-use.
- A Jupyter notebook (`scripts/housing.ipynb`) with example analysis showing how to load cached CSVs and compute simple metrics (e.g., monthly permits, year-to-year change).

Why caching: downloading raw XLS/CSV files on every run is slow and brittle. The project converts raw Census XLS files into cleaned CSVs stored under `data/cache/census/csv/` and reuses them until you force a refresh.

Quick repo layout
- `src/bls_housing/` — core package with cache utilities: `qcew_cache.py` (BLS QCEW), `census_cache.py` (Census BPS XLS→CSV), and a small `main.py`.
- `scripts/housing.ipynb` — notebook demonstrating data fetch, cleaning, and example analyses.
- `data/cache/` — local cache for downloaded and converted files (`census/xls`, `census/csv`, etc.).
- `pyproject.toml` — project and dependency metadata (Poetry).

Data sources 
- BLS QCEW (Quarterly Census of Employment and Wages): area-level employment and wage data in CSVs from the BLS CEW API. These files contain employment and wage data by area and aggregation level (MSA, county, etc.). The project uses `qcew_cache.py` to fetch and cache these CSVs. 

Info here: https://www.bls.gov/cew/additional-resources/open-data/csv-data-slices.htm
This data api goes back to 2014. For previous data there's zip files available.

- U.S. Census Building Permits Survey (BPS) — CBSA monthly releases: published building permits as XLS files (since 2019 path format). Example XLS URL:

  - https://www.census.gov/construction/bps/xls/cbsamonthly_YYYYMM.xls

  The `census_cache.py` module downloads the XLS, detects the header row, normalizes duplicate column names (adds `_year_to_date` suffixes), and writes a cleaned CSV into `data/cache/census/csv/` for downstream analysis.
Census building construction data changed to excel format Nov 2019, before that it was in txt format. 


Notes about the data
- CBSA monthly XLS files include two groups of columns — current month and year-to-date — which the cleaning logic preserves by appending `_year_to_date` to duplicate headings.
- BLS QCEW area CSVs include aggregation codes — e.g. `agglvl_code == 40` identifies MSA totals. The notebook demonstrates filtering by aggregation codes and summing quarterly/annual totals.
- The BPS monthly files are preliminary on release and later revised. The project caches whatever the downloaded file contains; re-run with `force_download=True` in the cache helpers to refresh.

Getting started
1. Install dependencies (Poetry recommended):

### Prerequisite: Poetry

If you don’t already have Poetry installed, you can install it with:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```
follow the instructions to add poetry to your path, and refresh your command line interface 
by typing 
```bash
 'bash' or 'source ~/.bashrc'
```

Make sure you're in the project directory and type
```bash
poetry install
```


2. Run the notebook in VS Code or Jupyter: open `scripts/housing.ipynb` and run cells. The notebook demonstrates using the cache utilities:

```python
from bls_housing.census_cache import fetch_cbsa_csv, load_cbsa_df
csv_path = fetch_cbsa_csv('2025','01')   # download + convert if needed
df = load_cbsa_df('2025','01')          # load cleaned CSV as a DataFrame
```

**Repro run (quick)**

1) Create the environment (Poetry):

Note: if you don't have poetry installed, instructions are in the Getting Started section of this document.

```bash
poetry install
```

2) Run the notebook (interactive) or execute it headless:

- Interactive: open `scripts/housing.ipynb` in VS Code or Jupyter and run cells.
- Headless (execute the notebook end-to-end):

```bash
poetry run jupyter nbconvert --to notebook --execute scripts/housing.ipynb --ExecutePreprocessor.timeout=600
```

3) Quick script alternative (fetch and convert one month):

```bash
poetry run python3 -c "from bls_housing.census_cache import fetch_cbsa_csv; print(fetch_cbsa_csv('2025','01'))"
```

The repro steps have been tested on a clean Linux environment.

Where cache files land

- Census XLS downloads: `data/cache/census/xls/` (raw `.xls` files)
- Cleaned Census CSVs: `data/cache/census/csv/` (files named like `CBSA_YYYY_MM.csv`)
- BLS QCEW area CSV cache: `data/cache/` (files named like `AREA_YYYY_Q.csv`, e.g. `C4266_2025_1.csv`)

What the outputs are

- Cleaned CSV tables (ready for pandas) containing CBSA monthly permit counts and year-to-date columns.
- QCEW area CSVs with employment and wage columns (aggregation codes included; e.g. `agglvl_code == 40` for MSA totals).
- Notebook cells produce small summary tables (e.g., total permits by MSA/month, year-over-year changes) and printed DataFrame heads.

Tips

- To refresh a cached file, pass `force_download=True` to the cache helpers in `src/bls_housing/*_cache.py`.
- Keep large caches out of Git; consider adding `data/cache/` to `.gitignore` or using git-lfs for larger artifacts.

---
Updated: 2026-01-15


