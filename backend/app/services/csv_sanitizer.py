import csv
import logging
from io import StringIO
from typing import Any

_module_logger = logging.getLogger(__name__)
_module_logger.debug("module.loaded module=%s", __name__)
FORMULA_PREFIXES = ("=", "+", "-", "@")


def sanitize_csv_value(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, list):
        text = "; ".join(str(item) for item in value)
    else:
        text = str(value)

    if text.startswith(FORMULA_PREFIXES):
        return f"'{text}"
    return text


def write_csv(headers: list[str], rows: list[dict[str, Any]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({header: sanitize_csv_value(row.get(header)) for header in headers})
    return output.getvalue()
