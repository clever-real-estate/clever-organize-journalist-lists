#!/usr/bin/env python3
"""
Detect and (optionally) fix Google Sheets number-formatting artifacts in
BUZZSTREAM CSV exports:

  - Cells like "$8", "$31" → 8, 31          (Currency format leaking into text)
  - Cells like "2.0", "12.0" → 2, 12        (Number-with-decimal format leaking)

These are common when a source Google Sheet has a column formatted as Currency
or Number-with-decimals, and the value gets exported as the DISPLAYED string
rather than the raw number. Fields like "Most Desirable Rank" are integers, so
a value of "$8" or "8.0" is always wrong.

The fix only touches cells that match those two exact patterns, so it never
alters names, outlets, URLs, or any other content.

Usage:
    python3 fix_number_formatting.py <file-or-folder> [<file-or-folder> ...] [--check-only]

--check-only  Report affected cells without modifying files (exit 1 if any found).

By default the script modifies files in place and reports per-file counts.
"""

import argparse
import csv
import glob
import os
import re
import sys

DOLLAR = re.compile(r"^\$(\d+(?:\.\d+)?)$")
TRAILING_ZERO = re.compile(r"^(\d+)\.0+$")


def clean(val: str) -> tuple[str, bool]:
    """Return (cleaned_value, was_changed)."""
    s = val.strip()
    m = DOLLAR.match(s)
    if m:
        v = m.group(1)
        m2 = TRAILING_ZERO.match(v)
        cleaned = m2.group(1) if m2 else v
        return cleaned, cleaned != val
    m = TRAILING_ZERO.match(s)
    if m:
        return m.group(1), True
    return val, False


def expand(target: str) -> list[str]:
    if os.path.isdir(target):
        return sorted(glob.glob(os.path.join(target, "**", "BUZZSTREAM_*.csv"), recursive=True))
    return [target]


def process_file(path: str, check_only: bool) -> int:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return 0

    header, body = rows[0], rows[1:]
    changes = 0
    for row in body:
        for i, cell in enumerate(row):
            new, changed = clean(cell)
            if changed:
                row[i] = new
                changes += 1

    if changes and not check_only:
        with open(path, "w", encoding="utf-8", newline="") as out:
            writer = csv.writer(out)
            writer.writerow(header)
            writer.writerows(body)
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Files or folders to scan")
    parser.add_argument("--check-only", action="store_true", help="Report only; don't modify files")
    args = parser.parse_args()

    total_files = touched = total_cells = 0
    for target in args.paths:
        for fp in expand(target):
            if "Combined_" in os.path.basename(fp):
                continue
            total_files += 1
            n = process_file(fp, args.check_only)
            if n:
                touched += 1
                total_cells += n
                verb = "would fix" if args.check_only else "fixed"
                print(f"  {verb} {n} cell(s): {fp}")

    verb = "Would fix" if args.check_only else "Fixed"
    print(f"\nScanned {total_files} files. {verb} {total_cells} cell(s) in {touched} file(s).")

    if args.check_only and total_cells > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
