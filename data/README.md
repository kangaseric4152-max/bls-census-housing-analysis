data/README.md

# Data Directory

This directory contains source data, ingestion scripts, and derived artifacts used for the
BLS / Census housing & zoning pressure analysis.

The project is designed to be **reproducible**: raw inputs + SQL ingestion scripts
can fully rebuild the DuckDB database locally.

---

## Directory Structure
```
data/ 
  ├── cache/              # Cache files from govt sources (BLS, Census)
  │                       # (ignored by git)
  ├── raw/                # Source-of-truth input data
  │    │                 # (CSV, sampled govt files) 
  │    ├── metros.csv 
  │    └── README.md (optional) 
  │ 
  ├── ingest/             # SQL ingestion / transformation scripts 
  │    ├── ingest_dim_metro_full.sql 
  │    └── ... 
  │ 
  ├── dumps/              # Generated query outputs (ignored by git) 
  │ 
  ├── rebuild.sql         # file to populate database
  ├── analysis.duckdb     # Local DuckDB database (ignored by git) 
  └── README.md
```
---

## Raw Data (`data/raw/`)

This directory contains **small, curated source files** used to populate dimension
tables and seed analysis.

Examples:
- `metros.csv` — cleaned CBSA metro code → area mapping (derived from BLS/Census documentation)
- Sample government data files used for schema validation and development

---

## Ingestion Scripts (`data/ingest/`)

SQL scripts in this directory create or replace tables inside DuckDB using
repo-relative paths.

Example:
```sql
CREATE OR REPLACE TABLE dim_metro_full AS
SELECT
    CAST(Code AS INTEGER) AS Code,
    Area,
    Title
FROM read_csv_auto('data/raw/metros.csv', header=true);

All ingestion scripts are designed to be run from the repository root.


---

Rebuilding the Database

To rebuild the local DuckDB database from scratch:

poetry run duckdb data/analysis.duckdb < data/ingest/ingest_dim_metro_full.sql

Additional ingestion scripts can be chained or added to a rebuild.sql entrypoint.


---

Ignored Artifacts

The following are intentionally not committed:

*.duckdb database files

JSON/CSV query outputs

temporary analysis dumps


These artifacts can be regenerated at any time from raw data + SQL scripts.


---

Notes

DuckDB is used for local analytics, prototyping, and reproducible querying

Data is primarily annual and quarterly BLS/Census data (2014–2024)

Future extensions may include Parquet-based caching for larger datasets