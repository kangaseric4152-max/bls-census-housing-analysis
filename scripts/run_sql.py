# scripts/run_sql.py
import argparse
from pathlib import Path
import logging
import duckdb
from bls_housing.logging_config import configure_logging

logger = logging.getLogger(__name__)

def main():
    configure_logging(level="INFO")
    ap = argparse.ArgumentParser(description="Run a .sql file against a DuckDB database")
    ap.add_argument("db", help="DuckDB database file (e.g., data/analysis.duckdb)")
    ap.add_argument("sql", help=".sql file to execute (e.g., data/ingest/ingest_dim_metro_full.sql)")
    args = ap.parse_args()

    db_path = Path(args.db)
    sql_path = Path(args.sql)

    sql_text = sql_path.read_text(encoding="utf-8")

    logger.info("Running SQL file %s against DB %s", sql_path, db_path)
    con = duckdb.connect(str(db_path))
    con.execute(sql_text)
    con.close()
    logger.info("Successfully executed %s", sql_path)

if __name__ == "__main__":
    main()