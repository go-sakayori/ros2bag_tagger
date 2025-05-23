from __future__ import annotations

from typing import Dict, List, Tuple


class TagTemplate:
    """Static container for the fixed set of tag categories."""

    # ------------------------------------------------------------------ #
    # Update this tuple whenever the spec evolves
    # ------------------------------------------------------------------ #
    _LABELS: Dict[str, Tuple[str, ...]] = {
        "dynamic_object": (
            "vehicle",
            "two_wheeler",
            "pedestrian",
            "unknown",
        ),
        "ego_vehicle_movement": (
            "lane keep",
            "left turn",
            "right turn",
            "lane change",
            "obstacle avoidance",
            "stopped",
            "parked",
            "pull out",
            "pull over",
        ),
        # No predefined sub-keys yet
        "location": (),
        "road_shape": (),
        "time_of_day": (),
    }

    # ------------------------------------------------------------------ #
    # Public helpers
    # ------------------------------------------------------------------ #

    @classmethod
    def category(cls) -> Tuple[str, ...]:
        """Return all categories name as an immutable tuple."""
        return tuple(cls._LABELS.keys())

    @classmethod
    def subcategory(cls, category: str) -> Tuple[str, ...]:
        """Return the sub-keys defined for *category* (may be empty)."""
        cls._assert_category(category)
        return cls._LABELS[category]

    @classmethod
    def empty(cls) -> Dict[str, Dict[str, List[str]]]:
        """Produce a fresh, fully initialised tag container."""
        return {cat: {sub: [] for sub in cls._LABELS[cat]} for cat in cls.category()}

    @classmethod
    def _assert_category(cls, category: str) -> None:
        if category not in cls._SPEC:
            raise KeyError(f"Unknown category: {category}")

    @classmethod
    def validate(cls, category: str) -> None:
        """
        Raise KeyError if *category* is not part of TagTemplate.

        Always call this before mutating a tag set to catch typos early.
        """
        if category not in cls._CATEGORIES:
            raise KeyError(
                f"Unknown category '{category}'. " f"Known categories: {', '.join(cls._CATEGORIES)}"
            )
