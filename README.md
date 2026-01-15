++**BLS QCEW Housing — Notebook + Utilities**
++
This repository contains a small Python package and a Jupyter notebook for fetching and analyzing BLS QCEW (Quarterly Census of Employment and Wages) area-level data. It is intentionally lightweight and intended for exploration and small reproducible analyses.
++
**Repository Structure**
- `pyproject.toml`: project metadata and dependency declarations (Poetry-style and PEP 621 fields present).
- `README.md`: this file.
- `test_env.py`: a small environment/smoke test script.
- `setup_env.sh`: convenience script to create an environment (optional).
- `scripts/housing.ipynb`: notebook demonstrating data fetch and analysis.
- `data/cache/`: cached CSVs (example: `C4266_2025_1.csv`).
- `src/bls_housing/`: Python package with helper modules (e.g., `main.py`, `qcew_cache.py`).
+
**Requirements**
- Python >= 3.12 (declared in `pyproject.toml`).
- Project dependencies are declared in `pyproject.toml` (use Poetry or install with pip). The package uses `requests` and `pandas`.
+
**Install (recommended: Poetry)**
If you have Poetry installed:

```bash
poetry install
poetry shell        # optional: spawn a shell with the virtualenv
```

Or install with pip into an existing virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```
+
**Run the notebook**
Open `scripts/housing.ipynb` in Jupyter or VS Code and run cells. The notebook demonstrates building BLS CSV URLs, loading them into `pandas.DataFrame`, and simple filters (e.g., `agglvl_code == 40` for MSA totals).
+
**Run the package / CLI**
The project defines a console script entry point in `pyproject.toml` (`project-name` -> `bls_housing.main:main`). With Poetry:

```bash
poetry run project-name
```

Or with an editable pip install:

```bash
python -m bls_housing.main
```
+
**Data cache**
Cached CSVs are stored in `data/cache/` (example file: `data/cache/C4266_2025_1.csv`). The `src/bls_housing/qcew_cache.py` module contains helpers to read/write cache files.
+
**Notes & current inconsistencies**
- `pyproject.toml` contains both PEP 621 `[project]` fields and `[tool.poetry]` sections. This works for metadata but may be cleaned up if you prefer a single format.
- The repository references `mypy`/`ipykernel` for development; ensure your dev environment installs them if you use type checking or run notebooks.
- There is a small smoke test script `test_env.py` but there are no formal pytest tests in the repo yet.
+
**Next steps**
- Move static area metadata (e.g., `AREA_CODES`) into a JSON/YAML file under `data/` or into `src/bls_housing/data.py` for reuse.
- Add a minimal test suite (pytest) and include it in `[tool.poetry.dev-dependencies]` if you want `poetry run check`/`pytest` support.
- Add README badges and a short example usage snippet from the notebook for quick reference.
+

---
+
Last updated to match repository contents on 2026-01-05.
## BLS & Census Housing — notebooks and utilities

This repository provides small, reusable utilities and a Jupyter notebook to fetch, cache, and analyze area-level housing and employment data from the U.S. Bureau of Labor Statistics (QCEW) and the U.S. Census (Building Permits Survey — BPS).

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
- BLS QCEW (Quarterly Census of Employment and Wages): area-level CSVs from the BLS CEW API. These files contain employment and wage data by area and aggregation level (MSA, county, etc.). The project uses `qcew_cache.py` to fetch and cache these CSVs.
- U.S. Census Building Permits Survey (BPS) — CBSA monthly releases: published as XLS files (since 2019 path format). Example XLS URL:

	- https://www.census.gov/construction/bps/xls/cbsamonthly_YYYYMM.xls

	The `census_cache.py` module downloads the XLS, detects the header row, normalizes duplicate column names (adds `_year_to_date` suffixes), and writes a cleaned CSV into `data/cache/census/csv/` for downstream analysis.

Notes about the data
- CBSA monthly XLS files include two groups of columns — current month and year-to-date — which the cleaning logic preserves by appending `_year_to_date` to duplicate headings.
- BLS QCEW area CSVs include aggregation codes — e.g. `agglvl_code == 40` identifies MSA totals. The notebook demonstrates filtering by aggregation codes and summing quarterly/annual totals.
- The BPS monthly files are preliminary on release and later revised. The project caches whatever the downloaded file contains; re-run with `force_download=True` in the cache helpers to refresh.

Getting started
1. Install dependencies (Poetry recommended):

```bash
poetry install
```

2. Run the notebook in VS Code or Jupyter: open `scripts/housing.ipynb` and run cells. The notebook demonstrates using the cache utilities:

```python
from bls_housing.census_cache import fetch_cbsa_csv, load_cbsa_df
csv_path = fetch_cbsa_csv('2025','01')   # download + convert if needed
df = load_cbsa_df('2025','01')          # load cleaned CSV as a DataFrame
```

Development notes & suggestions
- Consider moving static area mappings (`AREA_CODES`, `CBSA_CODES`) into a small JSON under `data/` for reuse across notebooks.
- Add dtype coercion and trimming of textual columns (e.g., `Name`) in `clean_and_convert_xls_to_csv` if you prefer typed CSVs — this is a safe next enhancement.
- Add a minimal test suite (pytest) to validate the cache conversion and header-parsing logic.

---
Updated: 2026-01-15
