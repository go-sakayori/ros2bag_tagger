"""MCAP parser module.

Parse MCAP file and infer without any ROS runtime dependency.
The implementation relies solely on the PyPIpackage mcap.
"""

from __future__ import annotations

from pathlib import Path

from mcap.reader import make_reader
from mcap_ros2.decoder import DecoderFactory

from .dataset_tags import DatasetTags


class McapTaggerError(RuntimeError):
    """Raised when parsing fails or the file is unreadable."""


class McapParser:
    """Infer :class:DatasetTags from a slice of an MCAP recording."""

    def __init__(self, mcap_path: str | Path, template: dict | None = None) -> None:
        """Instantiate a parser for *mcap_path*.

        Parameters
        ----------
        mcap_path
        """
        self.path = Path(mcap_path).expanduser().resolve()
        self.template = template
        self.velocity = [None, None]
        if not self.path.exists():
            raise McapTaggerError(f"File not found: {self.path}")

    def infer_tags(self) -> DatasetTags:
        """
        Very naive tag inference.

        *Replace this logic.*
        """
        ds = DatasetTags()
        if self.template:
            ds._tags.update(self.template)
        factory = DecoderFactory()

        with self.path.open("rb") as fh:
            rdr = make_reader(fh, decoder_factories=[factory])
            for _, channel, _, ros_msg in rdr.iter_decoded_messages(
                topics=["/perception/object_recognition/objects", "/localization/kinematic_state"],
                log_time_order=False,
            ):
                self._apply_rules(channel.topic, ros_msg, ds)

        ds.add("velocity", ",".join(map(str, self.velocity)))
        return ds

    def _apply_rules(self, topic: str, ros_msg, ds: DatasetTags) -> None:
        """Inspect each message and mutate DatasetTags in-place."""

        if topic == "/perception/object_recognition/objects":
            self._update_dynamic_object_tags(ros_msg, ds)

        if topic == "/localization/kinematic_state":
            self._update_velocity(ros_msg, self.velocity)

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

    @staticmethod
    def _update_velocity(ros_msg, velocity):
        current_vel = ros_msg.twist.twist.linear.x

        if velocity[0] is None or current_vel < velocity[0]:
            velocity[0] = current_vel
        if velocity[1] is None or current_vel > velocity[1]:
            velocity[1] = current_vel
