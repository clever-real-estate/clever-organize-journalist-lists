---
name: clever-organize-journalist-lists
description: Use this skill whenever Nicole asks to organize, sort, file, or bucket city or state journalist spreadsheets for a Clever / Best Interest Financial / Real Estate Witch / Clever Offers ranked-list study (e.g. "fastest- and slowest-selling markets," "most expensive cities," "best places to retire"). Trigger on phrases like "organize my media lists," "file these BUZZSTREAM CSVs by rank," "split these into 10 fastest/slowest folders," "combine my city CSVs into one," "make a list of cities I'm missing," or any request that involves taking a folder of per-city or per-state CSV journalist lists and bucketing them by where each city/state ranks in a study. Also trigger if Nicole references a study or ranking page and a folder of CSVs in the same breath, even without naming the steps. The skill prompts her for the rankings source and the folder path, then handles all of it — folder creation, file moves, combined-CSV generation, and a missing-locations report.
---

# Organize Clever Journalist Lists by Study Rank

## What this skill does

Takes a Clever ranked-list study (a webpage or HTML file) plus a local folder of per-city or per-state journalist CSVs (typically named `BUZZSTREAM_<Location>.csv`) and:

1. Parses the study's rankings.
2. Creates four ranked subfolders.
3. Moves each CSV into the folder that matches its rank.
4. Generates one combined upload-ready CSV in each subfolder (originals preserved).
5. Produces a markdown list of locations from the study that don't yet have a CSV.

It works for both **city studies** (typically 100 metros, split into 10 fastest / 10 slowest / Remaining top 50 fastest / Remaining top 50 slowest) and **state studies** (typically 50 states, split into 10 fastest / 10 slowest / Remaining 25 fastest / Remaining 25 slowest). Folder names follow Nicole's existing convention — match her existing folders if any, otherwise use the defaults below.

## Workflow

### Step 1 — Gather inputs (always ask)

Ask Nicole two things up front, ideally in a single AskUserQuestion turn:

1. **Where are the rankings?** A URL to the published study OR a path/upload of the HTML file. Best Interest Financial study pages have a `const CITIES = [...]` and/or `const STATES = [...]` JavaScript array embedded — that's the source of truth. If she pastes a URL, fetch it; if she uploads HTML, read it.
2. **Where are the CSVs?** The local folder path (e.g. `~/Documents/Media Lists/<Study Name>`). Use `request_cowork_directory` if the folder isn't already mounted.

Also confirm scope: *"Are we organizing **cities**, **states**, or **both**?"* — many studies have both. If both, run the workflow twice, once for each.

### Step 2 — Parse the rankings

Best Interest Financial studies embed the data as JS arrays. Each entry looks like:

```
{"n": "Austin, TX", "dom": 110.0, "yoy": 10.0, ...}
```

The `n` field is the location name and there's a primary metric (often `dom` = days on market, but it varies — could be price, score, etc.). Find the metric the study ranks by, then sort.

**Rank direction matters.** Studies usually phrase rank #1 as the "most" of something — slowest-selling, most expensive, etc. The "10 fastest" or "10 cheapest" group is the *opposite end* of the same array. Confirm direction by checking the page's section headings (`#slowest-metros`, `#fastest-metros`, etc.) before assigning ranks. The arrays in BIF studies are sometimes sorted slowest-first (cities) and sometimes fastest-first (states) — don't assume.

If the format isn't a JS array (plain HTML table, PDF, etc.), parse what's there. If you can't, tell Nicole which file/URL you tried and ask her to paste the rankings directly.

**Watch out for non-location rows** like `"National"` averages mixed into the array — exclude them from rank assignment.

### Step 3 — Apply the bucket rules

The buckets are:

| Cities (100 metros) | States (50 states) |
|---|---|
| 10 slowest cities | 10 slowest states |
| 10 fastest cities | 10 fastest states |
| Remaining top 50 slowest cities | Remaining 25 slowest states |
| Remaining top 50 fastest cities | Remaining 25 fastest states |

**Tie rule at the #10 boundary** — this is important. If multiple locations share the same metric value as the 10th-slowest or 10th-fastest, include *all* of them in the "10" bucket, even if it ends up being 12 or 13. Nicole asked for this explicitly: "go up to #10 no matter how many there end up being." Apply it on both ends.

**Rank-50 / rank-25 boundary** — flag ties to Nicole but don't auto-expand; the "remaining" buckets are sized to fill out the study's top 50 (cities) or top 25 (states) on each end.

**Worked example, cities:**
Slowest array starts: Austin 110, San Antonio 109, Miami 105, … Charlotte 90 (rank 10), Tucson 89 (rank 11). No tie at 90 → 10 Slowest = exactly 10 cities.
Fastest end: San Jose 12, San Francisco 14, Rochester 15, Lancaster 17, Seattle 26, Grand Rapids 27, Allentown 28, Buffalo 29, Harrisburg 31, Albany 35, **but** San Diego 35 and Modesto 35 are also at 35. → 10 Fastest = 12 cities (the cutoff value rules).

**Worked example, states:**
States with 12 cities in 10 fastest because Missouri/Pennsylvania/New York all tied at 54 days; 10 slowest had no tie at the boundary so it stayed at 10. Remaining 25 fastest = 13 states (25 minus 12 in the top bucket); Remaining 25 slowest = 15 states.

### Step 4 — Audit for Google Sheets number-format artifacts (ALWAYS)

Before moving or combining anything, scan every source CSV for two recurring formatting bugs from the BuzzStream / Google Sheets export pipeline:

- Cells like `$8` in integer columns (a Currency format leaking through as text)
- Cells like `2.0` in integer columns (a Number-with-decimals format leaking through)

Rank fields, category counts, days-on-market, and similar integer columns should never carry a `$` prefix or a `.0` suffix. When they do, downstream tooling that expects numbers breaks silently, and Nicole ends up with wrong ranks in her outreach.

Run the bundled auditor on the whole folder before doing anything else:

```
python3 scripts/fix_number_formatting.py <path-to-source-folder>
```

By default it fixes in place and reports counts. Use `--check-only` if you want to preview first. Only cells that match the exact patterns `^\$\d+(\.\d+)?$` or `^\d+\.0+$` are touched — names, outlets, URLs, and free-text fields are never modified.

Do this every time you organize a batch of BUZZSTREAM CSVs or set up new customization spreadsheets, without waiting to be asked. Nicole has flagged this as a standing check.

### Step 5 — Detect city vs. state files by reading the header (don't trust filenames)

This is critical because some location names overlap — `BUZZSTREAM_NewYork.csv` could be the NYC metro list or the New York state list, and `BUZZSTREAM_Washington.csv` could be Washington, DC or Washington state. The filename is identical; the folder location can be wrong if files were dropped in by mistake.

**The reliable signal is the CSV header.** BuzzStream exports tag rows with study-specific columns:

- **City file** — header contains `CITY SLOWEST RANK`, `CITY FASTEST RANK`, or `City - V2`.
- **State file** — header contains `STATE SLOWEST RANK`, `STATE FASTEST RANK`, or `State1`.

Use the bundled `scripts/detect_kind.py` to classify any file or folder before you move it:

```
python3 scripts/detect_kind.py <path-to-folder>
```

It prints one line per file (`CITY` / `STATE` / `BOTH` / `UNKNOWN`) and exits non-zero if anything is ambiguous. Run it on the source folder *before* doing any moves, and again on each destination folder *after* moving, as a final audit.

If detection returns `BOTH` or `UNKNOWN`, ask Nicole — don't guess. Filename + folder location alone are not enough.

### Step 6 — Create folders and move files

Folder names — match Nicole's existing convention if folders already exist (case and pluralization vary: "10 fastest cities" vs "10 Fastest Cities"). Otherwise create:

- `10 fastest cities` / `10 slowest cities` / `Remaining top 50 fastest cities` / `Remaining top 50 slowest cities`
- `10 fastest states` / `10 slowest states` / `Remaining 25 fastest states` / `Remaining 25 slowest states`

If Nicole has a `Cities` and `States` parent folder structure, respect it. Check first. Route each file by its detected kind (Step 4), then by its rank.

CSV filename convention is `BUZZSTREAM_<LocationName>.csv` with no spaces or punctuation:
- `Austin` → Austin, TX
- `SanAntonio` → San Antonio, TX
- `NewYork` → New York (city *or* state — distinguished by header, see Step 4)
- `SaltLakeCity`, `OklahomaCity`, `RhodeIsland`, `WestVirginia`, `NorthDakota`, `NewMexico`, `NewHampshire`, `NewJersey`, etc.

Move files using `mv`. If `mv` fails with "Operation not permitted," call `mcp__cowork__allow_cowork_file_delete` on any path in the folder once — it enables the whole folder.

**Within-domain ambiguity (same kind, different location):**
- `BUZZSTREAM_Portland.csv` (CITY) is most often Portland, OR (rank 59) but the study may include Portland, ME (rank 74) too. Ask which one if both are in scope.

### Step 7 — Generate combined CSVs

Run `scripts/combine_csvs.py` against each ranked subfolder. It writes `Combined_<Folder_Name>.csv` alongside the originals, taking the union of headers across all source CSVs (in case columns drift between files). Originals are preserved.

```
python3 scripts/combine_csvs.py "<path-to-folder>"
```

Repeat for each of the four subfolders.

If Nicole later adds a new CSV to a folder and asks to "update the combined CSV," re-run the script on just that folder — it overwrites the existing combined file.

**Combined CSVs are downstream of the source files — always regenerate them after ANY change to the sources.** This includes:

- Adding new files
- Removing files
- Editing cell values (formatting cleanup, find/replace, deduplication, verification passes, stripping columns, etc.)
- Renaming files

If Nicole asks you to "fix formatting in all the files," "clean up values," "strip $ signs," "remove customized fields," or anything that touches cell contents inside the per-location CSVs, treat that as also implying "then update the combined CSVs." Don't wait to be reminded — check the folder for any `Combined_*.csv` and regenerate it as the final step of the task. The combined file is stale the moment you change a source, and Nicole uploads from the combined file, so a stale combined = wrong data going out.

Same rule applies to the deduplication/verification pipeline: when `.valids.csv` files or `Verified_*.csv` / `Valid_*.csv` files change, any combined CSV that includes them needs regenerating.

### Step 8 — Produce the missing-locations report

Cross-reference the study's full list against the CSVs you found. Write a markdown file at the root of the study folder:

- Cities: `Missing Media Lists.md`
- States: `Missing State Media Lists.md`

Structure:

```markdown
# Missing Media Lists — <Study Title>

N of the M locations in the study still need media lists.

## 10 Slowest Cities (X missing)

- #6 Knoxville, TN — 93 days
- ...

## 10 Fastest Cities (X missing)

*Optional note about ties expanding the bucket.*

- ...

## Remaining Top 50 Slowest Cities (X missing)
...

## Remaining Top 50 Fastest Cities (X missing)
...

## Notes

- Any disambiguation calls (e.g. "Portland.csv covers Portland, OR — Portland, ME is missing").
- Any rank-boundary ties worth flagging.
```

Always show the rank and the ranking metric value (days on market, price, etc.) — Nicole uses this to prioritize outreach.

### Step 9 — Wrap up

Summarize concisely:
- Counts per bucket (e.g. "10 slowest states: 8 of 10 → 321 rows combined").
- A computer:// link to the missing-locations markdown.
- Don't re-explain the bucket rules unless something nontrivial happened (a tie expanded a group, a file was ambiguous, etc.).

## Why these defaults

- **Tie-inclusive #10** — Nicole's outreach is ranked-cohort-driven; if Modesto sells in the same number of days as San Jose, leaving it out misrepresents the cohort. Better to over-include than under-include at the #10 line.
- **Originals preserved** — combined CSVs are an *upload convenience*; originals stay because Nicole verifies and re-cleans on a per-city basis.
- **Union of headers when combining** — different cities sometimes have slight column drift (added rank columns, status columns). Union avoids silent data loss.
- **Markdown for the missing report** — easy to skim, easy to copy individual rows into outreach planning, renders inline in finder/preview.

## When NOT to use this skill

- If Nicole has a single CSV with all journalists already and just wants to filter/sort it — that's a spreadsheet task, not a folder-organization task.
- If the study only ranks one dimension (e.g. just a "top 10" with no extended top-50) — ask whether she still wants the four-bucket structure or something simpler.
- If the user isn't Nicole and the BUZZSTREAM/Clever convention doesn't apply — adapt or skip.
