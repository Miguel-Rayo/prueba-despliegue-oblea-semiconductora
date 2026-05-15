# ============================================================
# LOGGING ESTRUCTURADO — Robusto para Docker / Render
# ============================================================

import logging
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

# Handler para consola (siempre disponible)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Handler para archivo (mejor esfuerzo; en entornos efímeros puede fallar)
_file_handler: logging.Handler | None = None
try:
    _fh = logging.FileHandler(LOG_DIR / "backend.log", encoding="utf-8")
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(formatter)
    _file_handler = _fh
except Exception as e:
    # Si no podemos escribir en disco (ej. filesystem read-only), solo usamos consola
    _fallback = logging.StreamHandler(sys.stderr)
    _fallback.setLevel(logging.WARNING)
    _fallback.setFormatter(formatter)
    _fallback.handle(
        logging.LogRecord(
            "logging", logging.WARNING, "", 0,
            f"No se pudo crear file handler en {LOG_DIR}: {e}", (), None
        )
    )

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        logger.addHandler(console_handler)
        if _file_handler is not None:
            logger.addHandler(_file_handler)
    return logger
