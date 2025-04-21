"""
mcap_parser.py – Parse the first 60 seconds of an MCAP file
and infer DatasetTags without any ROS dependency.

Relies solely on the PyPI package `mcap`.
"""

from __future__ import annotations

from pathlib import Path

from mcap.reader import make_reader
from mcap.records import Message, Schema

from .dataset_tags import DatasetTags


class McapTaggerError(RuntimeError):
    """Raised when parsing fails or the file is unreadable."""


class McapParser:
    def __init__(self, mcap_path: str | Path) -> None:
        self.path = Path(mcap_path).expanduser().resolve()
        if not self.path.exists():
            raise McapTaggerError(f"File not found: {self.path}")

    def infer_tags(self) -> DatasetTags:
        """
        Very naive tag inference:

        - If any "/radar/<id>/object" topic exists  -> traffic_volume = heavy
        - If frame_id contains "night"              -> time_of_day = night
        - If schema name contains "Weather"         -> weather = rainy
        *Replace this logic with your own rules.*
        """
        ds = DatasetTags()

        with self.path.open("rb") as fh:
            reader = make_reader(fh)
            start_time: float | None = None

            for msg in reader.iter_messages():
                msg_time_sec = msg.log_time / 1e9  # nanosec -> sec

                # record first timestamp
                if start_time is None:
                    start_time = msg_time_sec

                # stop after 60 sec window
                if msg_time_sec - start_time > self.SLICE_SEC:
                    break

                self._apply_rules(msg, ds, reader.schemas)

        # fallback defaults (optional)
        if not ds.to_dict()["weather"]:
            ds.set("weather", ["unknown"])

        return ds

    def _apply_rules(
        self, msg: Message, ds: DatasetTags, schemas: dict[int, Schema]
    ) -> None:
        """Inspect each message and mutate DatasetTags in‑place."""
        topic = msg.channel.topic

        # simplistic traffic volume heuristic
        if "/object" in topic:
            ds.set("traffic_volume", ["heavy_traffic"])

        # time of day from frame_id (dummy rule)
        if b"night" in msg.data:
            ds.set("time_of_day", ["night"])

        # schema‑based weather hint
        schema_name = schemas[msg.channel.schema_id].name.lower()
        if "weather" in schema_name:
            ds.set("weather", ["rainy"])
