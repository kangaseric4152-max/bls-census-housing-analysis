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
  pipeline/        data build logic (wages, permits, cumulative metrics)
  duck.py          DuckDB helpers and database writes
  logging_config.py
  helpers.py       shared constants and utilities

scripts/
  housing.ipynb    main analysis notebook

data/
  cache/           raw public data (BLS, Census)
  derived/         parquet outputs
  rebuild.sql      schema initialization
  TODO          known data caveats & anomalies

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
---

## Outputs

- DuckDB analytical tables
- Parquet files under data/derived
- Line charts illustrating annual and cumulative housing pressure

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

Last updated: 2026-01-27
