import math
import os
from typing import Any, Dict

import pyarrow as pa
from dotenv import load_dotenv
from influxdb_client_3 import InfluxDBClient3, Point
from loguru import logger

load_dotenv()

INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")

DATABASE_RTSYS = "rtsys"
MEASUREMENT_WAN = "wan"

# Placeholder values sent by the router when a value is unavailable
_EMPTY_VALUES = {"", "none"}
NULL_VALUE = "null"


class InfluxDBWriter:

    def __init__(self, url: str = INFLUX_URL, token: str = INFLUX_TOKEN, database: str = DATABASE_RTSYS):
        self.url = url
        self.token = token
        self.database = database
        self._client: InfluxDBClient3 | None = None

    def _get_client(self) -> InfluxDBClient3:
        if self._client is None:
            if not self.token:
                raise RuntimeError("INFLUX_TOKEN is not set; export it before starting the server")
            self._client = InfluxDBClient3(host=self.url, token=self.token, database=self.database)
        return self._client

    def write_wan(self, data: Dict[str, Any]) -> None:
        """Store a WAN status message in database 'rtsys', measurement 'wan'."""
        identity = str(data.get("identity", "unknown"))
        fields = _to_fields(_flatten(data, exclude={"identity", "time", "date"}))

        if not fields:
            logger.warning(f"WAN message from {identity} has no storable fields")
            return

        point = Point(MEASUREMENT_WAN).tag("identity", identity)
        for name, value in fields.items():
            point = point.field(name, value)

        self._get_client().write(record=point)

    def query(self, sql: str) -> pa.Table:
        """Run an SQL query against the rtsys database and return the result as a pyarrow Table."""
        return self._get_client().query(query=sql, language="sql", mode="all")

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None


def _flatten(data: Dict[str, Any], prefix: str = "", exclude: set = frozenset()) -> Dict[str, Any]:
    """Flatten nested dicts into 'parent_child' keys, skipping excluded top-level keys."""
    flat = {}
    for key, value in data.items():
        if not prefix and key in exclude:
            continue
        name = f"{prefix}_{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten(value, name))
        else:
            flat[name] = value
    return flat


def _to_fields(flat: Dict[str, Any]) -> Dict[str, Any]:
    """Convert values to InfluxDB-compatible field types; unavailable values are stored as 'null'."""
    fields = {}
    for name, value in flat.items():
        if value is None:
            fields[name] = NULL_VALUE
            continue
        if isinstance(value, str):
            if value.strip().lower() in _EMPTY_VALUES:
                fields[name] = NULL_VALUE
                continue
            try:
                number = float(value)
                if math.isfinite(number):
                    fields[name] = number
                    continue
            except ValueError:
                pass
            fields[name] = value
        elif isinstance(value, bool):
            fields[name] = value
        elif isinstance(value, (int, float)):
            fields[name] = float(value)
        else:
            # Lists (e.g. carrier aggregation bands) are stored as their string form
            fields[name] = str(value)
    return fields


influx_writer = InfluxDBWriter()
