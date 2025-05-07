"""MCAP parser module.

Parse MCAP file and infer without any ROS runtime dependency.
The implementation relies solely on the PyPIpackage mcap.
"""

from __future__ import annotations

from pathlib import Path

from mcap_ros2.reader import read_ros2_messages

from .dataset_tags import DatasetTags


class McapTaggerError(RuntimeError):
    """Raised when parsing fails or the file is unreadable."""


class McapParser:
    """Infer :class:DatasetTags from a slice of an MCAP recording."""

    def __init__(self, mcap_path: str | Path) -> None:
        """Instantiate a parser for *mcap_path*.

        Parameters
        ----------
        mcap_path
        """
        self.path = Path(mcap_path).expanduser().resolve()
        self.turn_signal = 1
        if not self.path.exists():
            raise McapTaggerError(f"File not found: {self.path}")

    def infer_tags(self) -> DatasetTags:
        """
        Very naive tag inference.

        *Replace this logic.*
        """
        ds = DatasetTags()
        start_time: float | None = None

        for view in read_ros2_messages(
            str(self.path),
            topics=[
                "/perception/object_recognition/objects",
                "/localization/kinematic_state",
                "/pacmod/turn_rpt",
            ],
        ):
            # record first timestamp
            if start_time is None:
                start_time = view.log_time_ns

            self._apply_rules(view.channel.topic, view.ros_msg, ds)

        return ds

    def _apply_rules(self, topic: str, ros_msg, ds: DatasetTags) -> None:
        """Inspect each message and mutate DatasetTags in-place."""

        if topic == "/perception/object_recognition/objects":
            self._update_dynamic_object_tags(ros_msg, ds)
        if topic == "/localization/kinematic_state":
            self._update_road_shape(ros_msg, ds)
        if topic == "/pacmod/turn_rpt":
            self.turn_signal = 1

    @staticmethod
    def _update_dynamic_object_tags(ros_msg, ds: DatasetTags) -> None:
        """Add tags to dynamic_object."""
        for obj in ros_msg.objects:
            label = obj.classification[0].label

            match label:
                case 0:
                    ds.add_dynamic_object("unknown", "unknown")
                case 1:
                    ds.add_dynamic_object("vehicle", "car")
                case 2:
                    ds.add_dynamic_object("vehicle", "truck")
                case 3:
                    ds.add_dynamic_object("vehicle", "bus")
                case 4:
                    ds.add_dynamic_object("vehicle", "trailer")
                case 5:
                    ds.add_dynamic_object("two_wheeler", "motorcycle")
                case 6:
                    ds.add_dynamic_object("two_wheeler", "bicycle")
                case 7:
                    ds.add_dynamic_object("pedestrian", "pedestrian")
                case 8:
                    ds.add_dynamic_object("pedestrian", "animal")
                case 9:
                    ds.add_dynamic_object("unknown", "hazard")
                case 10:
                    ds.add_dynamic_object("unknown", "over_drivable")
                case 11:
                    ds.add_dynamic_object("unknown", "under_drivable")
