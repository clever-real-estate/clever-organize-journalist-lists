#!/usr/bin/env python3
"""
Detect whether a BUZZSTREAM CSV is a city list or a state list by reading its header.

BuzzStream exports for Clever studies tag rows with study-specific columns. The header
fingerprints are:
  - City file:  contains 'CITY SLOWEST RANK', 'CITY FASTEST RANK', or 'City - V2'
  - State file: contains 'STATE SLOWEST RANK', 'STATE FASTEST RANK', or 'State1'

This is the only reliable way to tell BUZZSTREAM_NewYork.csv (NYC metro) from
BUZZSTREAM_NewYork.csv (NY state), or Washington (DC) from Washington (state).
The filename and folder location are *not* sufficient.

Usage:
    python3 detect_kind.py <file-or-folder> [<file-or-folder> ...]

Outputs one line per file: <kind>\t<path>
where <kind> is one of: CITY, STATE, BOTH, UNKNOWN.

Exit code: 0 if all files are CITY or STATE; 1 if any are BOTH or UNKNOWN.
"""

import csv
import glob
import os
import sys

CITY_MARKERS = {"CITY SLOWEST RANK", "CITY FASTEST RANK", "City - V2"}
STATE_MARKERS = {"STATE SLOWEST RANK", "STATE FASTEST RANK", "State1"}


def detect(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            header = next(csv.reader(f), [])
    except (OSError, StopIteration):
        return "UNKNOWN"
    s = set(header)
    has_city = bool(s & CITY_MARKERS)
    has_state = bool(s & STATE_MARKERS)
    if has_city and not has_state:
        return "CITY"
    if has_state and not has_city:
        return "STATE"
    if has_city and has_state:
        return "BOTH"
    return "UNKNOWN"


def expand(target: str) -> list[str]:
    if os.path.isdir(target):
        return sorted(glob.glob(os.path.join(target, "**", "BUZZSTREAM_*.csv"), recursive=True))
    return [target]


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: detect_kind.py <file-or-folder> [...]", file=sys.stderr)
        return 2

    bad = 0
    for target in sys.argv[1:]:
        for fp in expand(target):
            if "Combined_" in os.path.basename(fp):
                continue
            kind = detect(fp)
            print(f"{kind}\t{fp}")
            if kind in ("BOTH", "UNKNOWN"):
                bad += 1
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
