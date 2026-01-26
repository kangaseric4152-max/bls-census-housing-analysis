from pathlib import Path
import duckdb
import re
from bls_housing.logging_config import configure_logging


INCLUDE_RE = re.compile(r"^\s*--\s*include:\s*(.+?)\s*$")

def expand_sql(sql_path: Path, root: Path) -> str:
    lines = []
    for line in sql_path.read_text(encoding="utf-8").splitlines():
        m = INCLUDE_RE.match(line)
        if m:
            rel = m.group(1).strip()
            inc = (root / rel).resolve()
            lines.append(f"-- BEGIN INCLUDE {rel}")
            lines.append(inc.read_text(encoding="utf-8"))
            lines.append(f"-- END INCLUDE {rel}")
        else:
            lines.append(line)
    return "\n".join(lines) + "\n"

def main():
    configure_logging(level="INFO")
    
    root = Path(__file__).resolve().parents[2]  # repo root
    db_path = root / "data" / "analysis.duckdb"
    rebuild_sql = root / "data" / "rebuild.sql"
    LOG_DIR = root / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    print("Building DuckDB database...")
    con = duckdb.connect(str(db_path))

    sql = expand_sql(rebuild_sql, root)
    con.execute(sql)

    con.close()
    print("Done.")