from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def _mcap_times(mcap_path: Path) -> tuple[datetime, datetime]:
    from mcap.reader import make_reader  # lazy import

    with mcap_path.open("rb") as fh:
        rdr = make_reader(fh)
        stats = rdr.get_summary().statistics
        if stats:
            start_ns, end_ns = stats.message_start_time, stats.message_end_time
        else:  # rare: no summary chunk
            msgs = rdr.iter_messages()
            first = next(msgs).log_time
            last = first
            for _, _, m in msgs:
                last = m.log_time
            start_ns, end_ns = first, last
    return start_ns / 1e9, end_ns / 1e9


def get_bag_times(path: str | Path) -> tuple[datetime, datetime]:
    p = Path(path)
    if p.suffix == ".mcap":
        return _mcap_times(p)
    raise ValueError(f"Unsupported bag type: {p}")
