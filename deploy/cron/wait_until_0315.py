"""Чекає до наступних 03:15 Europe/Kyiv, потім виходить."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def main() -> None:
    tz = ZoneInfo("Europe/Kyiv")
    now = datetime.now(tz)
    target = now.replace(hour=3, minute=15, second=0, microsecond=0)
    if now >= target:
        target += timedelta(days=1)
    wait = max(0.0, (target - now).total_seconds())
    print(
        f"==> next sync_dntrade at {target.isoformat()} (sleep {int(wait)}s)",
        flush=True,
    )
    time.sleep(wait)


if __name__ == "__main__":
    main()
