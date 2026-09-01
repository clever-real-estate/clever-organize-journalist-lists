# clever-organize-journalist-lists

A Claude skill that organizes per-city or per-state journalist CSVs into ranked
folders based on a Clever / Best Interest Financial ranked-list study.

Given a study (URL or HTML file) and a folder of `BUZZSTREAM_<Location>.csv`
files, it parses the study's rankings, creates the four ranked subfolders, moves
each CSV into the right bucket, generates one upload-ready combined CSV per
folder (originals preserved), and reports which locations are still missing a list.

## Contents

| Path | Purpose |
|---|---|
| `SKILL.md` | The skill itself — trigger description and full workflow. |
| `scripts/detect_kind.py` | Decides whether a study/folder is cities or states. |
| `scripts/combine_csvs.py` | Merges per-location CSVs into one upload-ready file. |
| `scripts/fix_number_formatting.py` | Cleans number formatting in the output CSVs. |

## Installing

Clone or download this repo, then drop the `clever-organize-journalist-lists`
folder into your skills directory:

- **Claude Code / Cowork:** `~/.claude/skills/clever-organize-journalist-lists/`
- **Claude app:** upload the folder as a skill in Settings → Capabilities → Skills.

Restart the session and ask something like *"organize my media lists for the
fastest-selling markets study."*

## Note on data

No journalist contact data belongs in this repo. `.gitignore` blocks `*.csv`,
`*.xlsx`, and `BUZZSTREAM_*` so real media lists can't be committed by accident.
