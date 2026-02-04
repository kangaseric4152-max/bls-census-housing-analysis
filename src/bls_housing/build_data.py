from pathlib import Path
import re
import logging
from bls_housing.logging_config import configure_logging
from bls_housing.ingest.duck import get_analysis_db_connection

logger = logging.getLogger(__name__)

INCLUDE_RE = re.compile(r"^\s*--\s*include:\s*(.+?)\s*$")

def expand_sql(sql_path: Path, root: Path) -> str:
    logger.info("Expanding SQL file %s (root=%s)", sql_path, root)
    lines = []
    include_count = 0
    for line in sql_path.read_text(encoding="utf-8").splitlines():
        m = INCLUDE_RE.match(line)
        if m:
            include_count += 1
            rel = m.group(1).strip()
            inc = (root / rel).resolve()
            lines.append(f"-- BEGIN INCLUDE {rel}")
            lines.append(inc.read_text(encoding="utf-8"))
            lines.append(f"-- END INCLUDE {rel}")
        else:
            lines.append(line)
    out = "\n".join(lines) + "\n"
    logger.info("Expanded SQL %s: includes=%d total_lines=%d", sql_path, include_count, len(lines))
    return out

def main():
    configure_logging(level="INFO")

    root = Path(__file__).resolve().parents[2]  # repo root
    rebuild_sql = root / "data" / "rebuild.sql"
    LOG_DIR = root / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Building DuckDB database from %s", rebuild_sql)
    con = get_analysis_db_connection()

    sql = expand_sql(rebuild_sql, root)
    con.execute(sql)

    con.close()
    logger.info("Done building DuckDB database")