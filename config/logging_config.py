"""Configuração de logging para toda a aplicação."""
import logging
import logging.config
from pathlib import Path

from config.settings import settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """Configura handlers de console e arquivo."""
    log_dir: Path = settings.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    level = logging.DEBUG if settings.debug else logging.INFO

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {"format": _LOG_FORMAT, "datefmt": _DATE_FORMAT},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": level,
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": str(log_dir / "news_automation.log"),
                    "maxBytes": 10_485_760,  # 10 MB
                    "backupCount": 5,
                    "formatter": "standard",
                    "level": level,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "handlers": ["console", "file"],
                "level": level,
            },
        }
    )
