from pathlib import Path

import lanelet2.io
from autoware_lanelet2_extension_python.projection import MGRSProjector


class MapMarker:
    def __init__(self, mcap_path: str | Path, map_path: str | Path) -> None:
        self.mcap_path = Path(mcap_path).expanduser().resolve()
        if not self.mcap_path.exists():
            print(f"File not found: {self.mcap_path}")

        self.map_path = Path(map_path).expanduser().resolve()
        if not self.map_path.exists():
            print(f"File not found: {self.map_path}")

        self.map = lanelet2.io.load(self.map_path, MGRSProjecter(lanelet2.io.Origin(0.0, 0.0)))


if __name__ == "__main__":
    mapmarker = MapMarker(
        mcap_path=None,
        map_path="/home/npc2301030/autoware_map/shinagawa_odaiba_stable/lanelet2_map.osm",
    )
