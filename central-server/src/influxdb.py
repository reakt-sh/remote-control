import math
import os
import time
from typing import Any, Dict, List
import globals as app_globals

import pyarrow as pa
from dotenv import load_dotenv
from influxdb_client_3 import InfluxDBClient3, Point, WritePrecision
from loguru import logger

load_dotenv()

INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")

DATABASE_RTSYS = "rtsys"
MEASUREMENT_WAN = "wan"
MEASUREMENT_TELEMETRY = "telemetry"
MEASUREMENT_TELEMETRY_LATENCY = "telemetry_latency"
MEASUREMENT_FRAME_LATENCY = "frame_latency"
MEASUREMENT_COMMAND_LATENCY = "command_latency"
MEASUREMENT_CLOCK_TRAIN = "clock_train"
MEASUREMENT_CLOCK_RC = "clock_rc"

FRAME_LATENCY_BATCH_SIZE = 200
TELEMETRY_BATCH_SIZE = 20
TELEMETRY_LATENCY_BATCH_SIZE = 20



class InfluxDBWriter:

    def __init__(self, url: str = INFLUX_URL, token: str = INFLUX_TOKEN, database: str = DATABASE_RTSYS):
        self.url = url
        self.token = token
        self.database = database
        self._client: InfluxDBClient3 | None = None
        self._frame_latency_buffer: List[Point] = []
        self._telemetry_buffer: List[Point] = []
        self._telemetry_latency_buffer: List[Point] = []

    def _get_client(self) -> InfluxDBClient3:
        if self._client is None:
            if not self.token:
                raise RuntimeError("INFLUX_TOKEN is not set; export it before starting the server")
            self._client = InfluxDBClient3(host=self.url, token=self.token, database=self.database)
        return self._client

    def write_wan(self, data: Dict[str, Any]) -> None:
        """Store a WAN status message in database 'rtsys', measurement 'wan'."""
        fields = _to_fields(_flatten(data))

        if not fields:
            logger.warning(f"WAN message from {app_globals.control_session_id} has no storable fields")
            return

        # include control session as a tag so we can filter WAN messages by session in InfluxDB
        point = Point(MEASUREMENT_WAN).tag("session_id", app_globals.control_session_id)

        for name, value in fields.items():
            point = point.field(name, value)

        self._get_client().write(record=point)

    def write_telemetry_latency(self, data: Dict[str, Any]) -> None:
        """Buffer telemetry latency points and write them in batches to limit InfluxDB write calls."""
        point = self._build_latency_point(MEASUREMENT_TELEMETRY_LATENCY, "Telemetry latency", data)
        if point is None:
            return

        # explicit timestamp: we set the timestamp to the remote control recevied it
        self._telemetry_latency_buffer.append(point.time(data['remote_control_timestamp'], WritePrecision.NS))
        if len(self._telemetry_latency_buffer) >= TELEMETRY_LATENCY_BATCH_SIZE:
            self.flush_telemetry_latency()

    def flush_telemetry_latency(self) -> None:
        if not self._telemetry_latency_buffer:
            return

        points = self._telemetry_latency_buffer
        self._telemetry_latency_buffer = []
        self._get_client().write(record=points)

    def write_frame_latency(self, data: Dict[str, Any]) -> None:
        """Buffer frame latency points and write them in batches to limit InfluxDB write calls."""
        point = self._build_latency_point(MEASUREMENT_FRAME_LATENCY, "Frame latency", data)
        if point is None:
            return

        # explicit timestamp: we set the timestamp to the remote control received it
        self._frame_latency_buffer.append(point.time(data['remote_control_timestamp'], WritePrecision.NS))
        if len(self._frame_latency_buffer) >= FRAME_LATENCY_BATCH_SIZE:
            self.flush_frame_latency()

    def flush_frame_latency(self) -> None:
        if not self._frame_latency_buffer:
            return

        points = self._frame_latency_buffer
        self._frame_latency_buffer = []
        self._get_client().write(record=points)

    def write_command_latency(self, data: Dict[str, Any]) -> None:
        self._write_latency(MEASUREMENT_COMMAND_LATENCY, "Command latency", data)

    def _write_latency(self, measurement: str, description: str, data: Dict[str, Any]) -> None:
        point = self._build_latency_point(measurement, description, data)
        if point is not None:
            self._get_client().write(record=point)

    def _build_latency_point(self, measurement: str, description: str, data: Dict[str, Any]) -> Point | None:
        """Build a latency point with latency rounded to integer milliseconds (ties to even)."""
        if not data:
            logger.warning(f"{description} message from {app_globals.control_session_id} has no storable fields")
            return None

        point = Point(measurement).tag("session_id", app_globals.control_session_id)
        for name, value in data.items():
            if name == "latency":
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError("latency must be a finite number in milliseconds")
                if isinstance(value, float) and not math.isfinite(value):
                    raise ValueError("latency must be a finite number in milliseconds")
                value = round(value)
            point = point.field(name, value)

        return point

    def write_clock_train(self, data: Dict[str, Any]) -> None:
        if not data:
            logger.warning(f"Clock offset (train) message from {app_globals.control_session_id} has no storable fields")
            return

        point = Point(MEASUREMENT_CLOCK_TRAIN).tag("session_id", app_globals.control_session_id)
        for name, value in data.items():
            point = point.field(name, value)

        self._get_client().write(record=point)

    def write_clock_rc(self, data: Dict[str, Any]) -> None:
        if not data:
            logger.warning(f"Clock offset (remote control) message from {app_globals.control_session_id} has no storable fields")
            return

        point = Point(MEASUREMENT_CLOCK_RC).tag("session_id", app_globals.control_session_id)
        for name, value in data.items():
            point = point.field(name, value)

        self._get_client().write(record=point)

    def write_telemetry(self, data: Dict[str, Any]) -> None:
        fields = _flatten(data)
        if not fields:
            logger.warning(f"Telemetry message from {app_globals.control_session_id} has no storable fields")
            return

        point = Point(MEASUREMENT_TELEMETRY).tag("session_id", app_globals.control_session_id)
        for name, value in fields.items():
            point = point.field(name, value)

        # explicit timestamp: we set the timestamp when train client send it
        self._telemetry_buffer.append(point.time(data['timestamp'], WritePrecision.NS))
        if len(self._telemetry_buffer) >= TELEMETRY_BATCH_SIZE:
            self.flush_telemetry()

    def flush_telemetry(self) -> None:
        if not self._telemetry_buffer:
            return

        points = self._telemetry_buffer
        self._telemetry_buffer = []
        self._get_client().write(record=points)

    def query(self, sql: str) -> pa.Table:
        """Run an SQL query against the rtsys database and return the result as a pyarrow Table."""
        return self._get_client().query(query=sql, language="sql", mode="all")

    def close(self) -> None:
        try:
            self.flush_frame_latency()
        except Exception as e:
            logger.error(f"Failed to flush buffered frame latency points: {e}")
        try:
            self.flush_telemetry()
        except Exception as e:
            logger.error(f"Failed to flush buffered telemetry points: {e}")
        try:
            self.flush_telemetry_latency()
        except Exception as e:
            logger.error(f"Failed to flush buffered telemetry latency points: {e}")
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
    """Convert values to InfluxDB-compatible field types, skipping unavailable values."""
    fields = {}
    for name, value in flat.items():
        if value is None:
            continue
        if isinstance(value, str):
            if value.strip().lower() in {"", "none", "null"}:
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
