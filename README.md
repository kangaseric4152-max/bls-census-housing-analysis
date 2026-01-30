# BLS & Census Housing Analysis
_Reproducible data pipeline and exploratory analysis using U.S. public datasets_

---

## Overview

This repository provides a lightweight, reproducible pipeline for ingesting, caching, and analyzing
area-level housing permits and wage data from U.S. public sources:

- Bureau of Labor Statistics (BLS) — Quarterly Census of Employment and Wages (QCEW)
- U.S. Census Bureau — Building Permits Survey (BPS)

The project focuses on CBSA-level (metro area) trends and demonstrates how to:

- Ingest heterogeneous public datasets
- Normalize and cache raw files for repeatable analysis
- Build derived analytical tables in DuckDB
- Compute simple, interpretable housing pressure metrics
- Explore results interactively in a Jupyter notebook

This is not a predictive model. The goal is transparency, reproducibility, and method clarity.

---

## Why This Project Exists

This project began as an exploration of how publicly available labor (BLS) and housing (permit) data can be combined to understand structural housing pressure and inform zoning and policy discussions at the metro level.

---

## What This Project Computes

Two complementary metrics are used to explore housing supply pressure relative to labor growth:

1. Annual Zoning Pressure Index  
   Ratio of year-over-year wage growth to year-over-year permit growth.

2. Cumulative Housing Deficit Index  
   Relative change in wages vs. permits indexed to a base year.

These metrics are designed to surface structural imbalances, not to explain causality or pricing.

---

## Repository Layout
```bash
src/bls_housing/
  pipeline/        data build logic (wages, permits, cumulative metrics, parquet lake)
  duck.py          DuckDB helpers and database writes
  logging_config.py
  helpers.py       shared constants and utilities

scripts/
  housing.ipynb    main analysis notebook

data/
  cache/           raw public data (BLS, Census)
  derived/         parquet outputs
  lake/            parquet lake files in hive folder structure
  rebuild.sql      schema initialization
  TODO             known data caveats & anomalies

pyproject.toml
```
---

## Data Sources

BLS — QCEW (Quarterly Census of Employment and Wages)

- Area-level employment and wage data
- Accessed via the BLS CEW open CSV API
- Aggregation level agglvl_code == 40 is used for metro totals

Census — Building Permits Survey (BPS)

- Monthly CBSA-level building permits
- Published as Excel since November 2019
- Earlier data used fixed-width text formats

Notes about the data:
- This project analyzes Metropolitan Statistical Areas (MSAs) only.
While QCEW provides data for both MSAs and Micropolitan Statistical Areas (MicroSAs), MicroSAs are excluded to focus analysis on large urban labor and housing markets.
- Queryable data currently is derived from a pdf in the docs folder, but it's not exhaustive. A more comprehensive list of MSAs is in area-titles-csv.csv from https://www.bls.gov/cew/classifications/areas/qcew-area-titles.htm, but that needs to be matched with census reporting data.
- Replaced earlier PDF-based CBSA reference with QCEW area CSV to ensure current MSA/MicroSA classification accuracy.
- Area Classification Notes:
Metropolitan area definitions are sourced from the BLS QCEW area reference CSV.
During validation, three areas originally included via an older PDF reference were removed after confirmation that they were reclassified from Metropolitan Statistical Areas (MSAs) to Micropolitan Statistical Areas following the 2020 Census:
Carbondale–Marion, IL
Pine Bluff, AR
East Stroudsburg, PA.
These reclassifications were announced by the Office of Management and Budget (OMB) in July 2023 and implemented in 2025. The dimension table reflects current MSA classifications only.
---

## Why Caching Exists

Public data downloads are slow, brittle, and occasionally unavailable.

This project downloads raw files once, converts them to normalized CSV or Parquet, and reuses cached
data unless explicitly refreshed.

---

## Getting Started

Prerequisites:
- Python 3.10+
- Poetry

Build the data:
```bash
poetry install
poetry run build-data
```
Open housing.ipynb and run the cells to generate analysis tables and charts.

After running the notebook, you can process the raw csv to a parquet data lake form:
```bash
poetry run build-parquet-lake
```

---

## Outputs

- DuckDB analytical tables
- Parquet files under data/derived
- Line charts illustrating annual and cumulative housing pressure
- Parquet lake under data/lake

Optional: Object Storage (S3-compatible)
The Parquet lake can be published to S3-compatible object storage (e.g. MinIO or AWS S3) and queried directly from DuckDB using Hive-style partitioning.

From there you can query S3:
```sql
SELECT
  cbsa_code,
  year,
  quarter,
  COUNT(*) AS rows
FROM read_parquet(
  's3://housing-lake/bls/**/**/*.parquet',
  hive_partitioning=1
)
GROUP BY cbsa_code, year, quarter;
100% ▕██████████████████████████████████████▏ (00:00:04.45 elapsed)
┌───────────┬───────┬─────────┬───────┐
│ cbsa_code │ year  │ quarter │ rows  │
│   int64   │ int64 │  int64  │ int64 │
├───────────┼───────┼─────────┼───────┤
│     48660 │  2024 │       4 │  1274 │
│     48660 │  2024 │       3 │  1274 │
│     48660 │  2024 │       2 │  1274 │
│       ·   │    ·  │       · │    ·  │
│       ·   │    ·  │       · │    ·  │
│       ·   │    ·  │       · │    ·  │
├───────────┴───────┴─────────┴───────┤
│ 4046 rows (40 shown)      4 columns │
└─────────────────────────────────────┘
```

---

## Notes & Caveats

- Some metros lack complete permit or wage coverage
- Small base-year permit counts can produce unstable ratios
- Known anomalies are documented in data/TODO

---

## Changelog / Rationale

- Reorganized README into a clear narrative
- Removed exploratory or tutorial-style language
- Clarified scope and limitations
- Added parquet lake and poetry run script

Last updated: 2026-01-28
