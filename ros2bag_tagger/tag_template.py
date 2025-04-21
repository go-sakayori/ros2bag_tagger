from __future__ import annotations

from typing import Dict, List, Tuple


class TagTemplate:
    """Static container for the fixed set of tag categories."""

    # ------------------------------------------------------------------ #
    # Update this tuple whenever the spec evolves
    # ------------------------------------------------------------------ #
    _CATEGORIES: Tuple[str, ...] = (
        "dynamic_object",
        "ego_vehicle_movement",
        "location",
        "road_shape",
        "time_of_day",
    )

    # ------------------------------------------------------------------ #
    # Public helpers
    # ------------------------------------------------------------------ #

    @classmethod
    def empty(cls) -> Dict[str, List[str]]:
        """
        Return a fresh dict in which every category key is present and
        mapped to an empty list. This ensures downstream code never needs
        to check for missing keys.
        """
        return {cat: [] for cat in cls._CATEGORIES}

    @classmethod
    def validate(cls, category: str) -> None:
        """
        Raise KeyError if *category* is not part of TagTemplate.

        Always call this before mutating a tag set to catch typos early.
        """
        if category not in cls._CATEGORIES:
            raise KeyError(
                f"Unknown category '{category}'. "
                f"Known categories: {', '.join(cls._CATEGORIES)}"
            )

    @classmethod
    def categories(cls) -> Tuple[str, ...]:
        """Return the tuple of category names (read‑only)."""
        return cls._CATEGORIES
