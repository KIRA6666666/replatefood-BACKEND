import json
import logging
import logging.config
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(value: str | None) -> None:
    request_id_ctx.set(value)


def get_request_id() -> str | None:
    return request_id_ctx.get()


class JsonFormatter(logging.Formatter):
    _RESERVED = set(logging.makeLogRecord({}).__dict__) | {"taskName"}

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }
        for key, value in record.__dict__.items():
            if key not in self._RESERVED:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    formatter = (
        {"()": JsonFormatter}
        if settings.LOG_JSON
        else {
            "format": "%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
            "datefmt": "%H:%M:%S",
        }
    )

    log_file = Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"default": formatter},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "default",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": str(log_file),
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 5,
                    "encoding": "utf-8",
                    "formatter": "default",
                },
            },
            "root": {
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"],
            },
            "loggers": {
                "uvicorn": {"handlers": ["console", "file"], "level": settings.LOG_LEVEL, "propagate": False},
                "uvicorn.error": {"handlers": ["console", "file"], "level": settings.LOG_LEVEL, "propagate": False},
                "uvicorn.access": {"handlers": [], "level": "WARNING", "propagate": False},
                "sqlalchemy.engine": {"level": "WARNING"},
            },
        }
    )
