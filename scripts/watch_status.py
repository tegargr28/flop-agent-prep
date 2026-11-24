#!/usr/bin/env python3
"""Watch the official FLOP pages for status changes.

Runs the same read-only check as check_status.py, but keeps a local
snapshot of the signals it found last time (status-snapshot.json,
next to this script's data folder ~/.flop-agent/). On the next run it
reports only what changed, for example a phase opening or an
enrollment that is no longer unavailable.

Read-only, no keys, no posting. The snapshot is local state, it is
not part of this repository (see .gitignore).
"""
import json
import os
import sys
import urllib.request
import re
from pathlib import Path

PAGES = [
    ("testnet", "https://flop.finance/testnet/"),
    ("official", "https://flop.finance/official/"),
    ("operator", "https://docs.flop.network/"),
]
SIGNALS = [
    "unscored opening",
    "scored phase",
    "devnet is running and earns nothing",
    "public operator enrollment is unavailable",
    "testnet remains planned",
    "no launched or tradable",
    "registration is open",
]


def snapshot_path() -> Path:
    home = Path(os.environ.get("FLOP_AGENT_HOME", Path.home() / ".flop-agent"))
    return home / "status-snapshot.json"


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "flop-agent-prep watch"})
    with urllib.request.urlopen(request, timeout=20) as response:
        html = response.read().decode("utf-8", errors="replace")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).lower()


def current_signals() -> dict:
    found = {}
    for name, url in PAGES:
        text = fetch(url)
        found[name] = sorted(signal for signal in SIGNALS if signal in text)
    return found


def main() -> int:
    path = snapshot_path()
    try:
        now = current_signals()
    except Exception as error:
        print(f"could not read the official pages: {error}")
        return 1
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(now, indent=2), encoding="utf-8")
        print("First run: snapshot saved. Signals found:")
        for name, signals in now.items():
            print(f"  {name}: {', '.join(signals) if signals else '(none)'}")
        print("Run this again later and it will report only changes.")
        return 0
    before = json.loads(path.read_text(encoding="utf-8"))
    changes = []
    for name in now:
        for signal in sorted(set(now[name]) - set(before.get(name, []))):
            changes.append(f"APPEARED on {name}: '{signal}'")
        for signal in sorted(set(before.get(name, [])) - set(now[name])):
            changes.append(f"GONE from {name}: '{signal}'")
    path.write_text(json.dumps(now, indent=2), encoding="utf-8")
    if not changes:
        print("No change in the official status signals since the last run.")
        return 0
    print("CHANGED:")
    for change in changes:
        print(f"  - {change}")
    print("Read the official page yourself before acting on a change.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
