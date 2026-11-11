import math
import os
from typing import Any, Dict

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from loguru import logger

INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "")
INFLUX_ORG = os.getenv("INFLUX_ORG", "rtsys")

BUCKET_RTSYS = "rtsys"
MEASUREMENT_WAN = "wan"

# Placeholder values sent by the router when a value is unavailable
_EMPTY_VALUES = {"", "none"}


class InfluxDBWriter:

    def __init__(self, url: str = INFLUX_URL, token: str = INFLUX_TOKEN, org: str = INFLUX_ORG):
        self.url = url
        self.token = token
        self.org = org
        self._client: InfluxDBClient | None = None
        self._write_api = None
        self._buckets_ready = set()

    def _get_write_api(self, bucket: str):
        if self._client is None:
            self._client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            self._write_api = self._client.write_api(write_options=SYNCHRONOUS)

        if bucket not in self._buckets_ready:
            buckets_api = self._client.buckets_api()
            if buckets_api.find_bucket_by_name(bucket) is None:
                buckets_api.create_bucket(bucket_name=bucket, org=self.org)
                logger.info(f"Created InfluxDB bucket: {bucket}")
            self._buckets_ready.add(bucket)

        return self._write_api

    def write_wan(self, data: Dict[str, Any]) -> None:
        """Store a WAN status message in bucket 'rtsys', measurement 'wan'."""
        identity = str(data.get("identity", "unknown"))
        fields = _to_fields(_flatten(data, exclude={"identity", "time", "date"}))

        if not fields:
            logger.warning(f"WAN message from {identity} has no storable fields")
            return

        point = Point(MEASUREMENT_WAN).tag("identity", identity)
        for name, value in fields.items():
            point = point.field(name, value)

        write_api = self._get_write_api(BUCKET_RTSYS)
        write_api.write(bucket=BUCKET_RTSYS, org=self.org, record=point)

    def close(self) -> None:
        if self._write_api is not None:
            self._write_api.close()
            self._write_api = None
        if self._client is not None:
            self._client.close()
            self._client = None
        self._buckets_ready.clear()


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
    """Convert values to InfluxDB-compatible field types, dropping unavailable values."""
    fields = {}
    for name, value in flat.items():
        if value is None:
            continue
        if isinstance(value, str):
            if value.strip().lower() in _EMPTY_VALUES:
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
