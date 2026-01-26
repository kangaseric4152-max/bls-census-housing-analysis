from __future__ import annotations

import logging
import logging.config
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)



    

def configure_logging(
    *,
    level: str = "INFO",
    log_file: str | None = "bls_housing.log",
) -> None:
    """
    Configure root logging once for the whole app.
    Call this from entrypoints only (scripts/CLI/notebook top cell).
    """
    root = logging.getLogger()
    if root.handlers:
        return  # already configured
    
    handlers: dict = {
        "console": {
            "class": "logging.StreamHandler",
            "level": level,
            "formatter": "standard",
        }
    }

    if log_file is not None:
        handlers["file"] = {
            "class": "logging.FileHandler",
            "level": level,
            "formatter": "standard",
            "filename": str(LOG_DIR / log_file),
            "encoding": "utf-8",
        }
        root_handlers = ["console", "file"]
    else:
        root_handlers = ["console"]

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,  # critical for 3rd party libs
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s %(name)s: %(message)s"
                }
            },
            "handlers": handlers,
            "root": {
                "level": level,
                "handlers": root_handlers,
            },
        }
    )
