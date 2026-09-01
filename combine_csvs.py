#!/usr/bin/env python3
"""
Combine all BUZZSTREAM_*.csv files in a folder into a single CSV.

Usage:
    python3 combine_csvs.py <folder-path> [--output <filename>]

Behavior:
- Reads every BUZZSTREAM_*.csv in the folder (non-recursive).
- Skips any existing Combined_*.csv (so re-running is safe).
- Computes the union of headers across files, preserving first-seen order.
- Writes Combined_<FolderName>.csv inside the folder, with all rows.
- Skips empty rows. Originals are not modified.
"""

import argparse
import csv
import glob
import os
import re
import sys


def slug(s: str) -> str:
    """Turn a folder name into a snake_case-ish slug suitable for a filename."""
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s or "Combined"


def combine(folder: str, output: str | None = None) -> str:
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        raise SystemExit(f"Not a directory: {folder}")

    pattern = os.path.join(folder, "BUZZSTREAM_*.csv")
    files = sorted(
        f for f in glob.glob(pattern)
        if not os.path.basename(f).startswith("Combined_")
    )
    if not files:
        raise SystemExit(f"No BUZZSTREAM_*.csv files found in {folder}")

    if output:
        out_path = os.path.join(folder, output) if not os.path.isabs(output) else output
    else:
        out_path = os.path.join(folder, f"Combined_{slug(os.path.basename(folder))}.csv")

    # Pass 1: collect union of headers, preserving first-seen order across files.
    headers: list[str] = []
    seen: set[str] = set()
    for fp in files:
        with open(fp, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            try:
                row = next(reader)
            except StopIteration:
                continue
            for h in row:
                if h not in seen:
                    seen.add(h)
                    headers.append(h)

    # Pass 2: write combined output.
    total = 0
    per_file: list[tuple[str, int]] = []
    with open(out_path, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=headers)
        writer.writeheader()
        for fp in files:
            with open(fp, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    if any((v or "").strip() for v in row.values()):
                        writer.writerow({k: row.get(k, "") for k in headers})
                        count += 1
            per_file.append((os.path.basename(fp), count))
            total += count

    for name, n in per_file:
        print(f"  {name}: {n} rows")
    print(f"\nCombined {len(files)} files, {total} rows -> {out_path}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Combine BUZZSTREAM_*.csv files in a folder.")
    parser.add_argument("folder", help="Folder containing BUZZSTREAM_*.csv files")
    parser.add_argument("--output", "-o", help="Output filename (default: Combined_<FolderName>.csv)")
    args = parser.parse_args()
    combine(args.folder, args.output)


if __name__ == "__main__":
    main()
