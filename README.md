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

