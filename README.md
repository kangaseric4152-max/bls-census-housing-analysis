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
**Next steps / suggestions**
- Move static area metadata (e.g., `AREA_CODES`) into a JSON/YAML file under `data/` or into `src/bls_housing/data.py` for reuse.
- Add a minimal test suite (pytest) and include it in `[tool.poetry.dev-dependencies]` if you want `poetry run check`/`pytest` support.
- Add README badges and a short example usage snippet from the notebook for quick reference.
+
If you'd like, I can also:
- Normalize `pyproject.toml` to use either PEP 621 *or* Poetry table consistently.
- Add a tiny `examples/` script that reproduces the notebook analysis end-to-end.
+
---
+
Last updated to match repository contents on 2026-01-05.
# Python Jupyter Notebook BLS Housing Project 

A lightweight, production-ready Python project starter built with:
- Poetry (dependency management)
- mypy (type checking)
- dotenv (for environment config)



# Install dependencies
poetry install

## Project overview
This repository provides utilities and a Jupyter notebook to fetch and analyze QCEW (Quarterly Census of Employment and Wages) area-level data from the BLS. The main notebook is `scripts/housing.ipynb` which demonstrates how to:

- Build a BLS data API URL for an area and quarter using `qcewGetAreaUrl(year, qtr, area)`.
- Load area CSV data into a pandas `DataFrame` via `pd.read_csv(URLPATH)`.
- Filter results by aggregation level (for MSA totals use `agglvl_code == 40`).
- Use the `AREA_CODES` mapping for area metadata (e.g., `C4266` for Seattle-Tacoma-Bellevue).

## Important notes
- Example area codes found in the notebook: `C4266` (Seattle-Tacoma-Bellevue, WA) and `C3890` (Portland-Vancouver-Hillsboro, OR-WA).
- The notebook includes helper code (commented) for alternate HTTP fetching approaches using `urllib.request`.
- When filtering: `agglvl_code == 40` means MSA total covered; `own_code == 0` is total ownership; `industry_code == 10` is all industries; `size_code == 0` is all establishment sizes.

## How to run
1. Ensure dependencies are installed: `poetry install`.
2. Open the notebook `scripts/housing.ipynb` in Jupyter or VS Code and run cells.

## Next steps
- Consider converting `AREA_CODES` to a JSON/YAML data file or a small Python module in `src/bls_housing/` for reuse.
- Add simple functions to fetch and cache area CSVs and to return cleaned DataFrames for downstream analysis.

- Compute Y/Y wage growth for Seattle MSA using total quarterly wages (Q1 vs Q1 prior year), before introducing housing.