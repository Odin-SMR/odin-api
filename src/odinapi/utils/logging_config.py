import json
from typing import Any, Dict

from pythonjsonlogger import jsonlogger


class OdinJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that flattens Gunicorn access JSON into top-level fields.

    Gunicorn access logs are currently formatted as a JSON string via
    ``access_log_format``. That JSON string becomes the logging ``message``.
    This formatter parses that string for the ``gunicorn.access`` logger and
    merges the parsed keys into the log record so CloudWatch sees a single
    flat JSON object per line.
    """

    def process_log_record(self, log_record: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
        # First let the base class apply its normal processing (including
        # field renaming configured via ``rename_fields``).
        log_record = super().process_log_record(log_record)

        logger_name = log_record.get("logger") or log_record.get("name")
        if logger_name == "gunicorn.access":
            message = log_record.get("message")
            if isinstance(message, str):
                try:
                    parsed = json.loads(message)
                except Exception:
                    parsed = None
                if isinstance(parsed, dict):
                    for key, value in parsed.items():
                        # Do not overwrite top-level fields like time, level, etc.
                        if key not in log_record:
                            log_record[key] = value
        return log_record
