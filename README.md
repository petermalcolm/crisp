# CRISP — Capital Reserve Investment/reserve Study Planner

A self-hosted tool for planning and tracking a capital reserve fund: a list of
components that need periodic replacement, a year-by-year cost projection,
adjustable economic assumptions (inflation, interest, contribution growth),
and a Fully Funded Balance (FFB) analysis. The underlying data is itself
git-version-controlled, with a `main` branch for the current state of the
world and named "forecast" branches for what-if scenarios that can be
squash-merged back into `main` when they become real.

## Prerequisites

- Python 3.11+
- Node 18.19+ (or newer — the repo was built and tested against Node 25/npm 11)
- git

## First-time setup

```bash
# Backend
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

The data repo at `version-controlled-data/` is already a separate, initialized
git repository (gitignored by this outer repo — see `.gitignore`). It ships
with empty CSVs on `main`; nothing further to set up.

## Running it

Two processes, both need to be running:

```bash
# Terminal 1 — backend (from backend/)
.venv/bin/uvicorn app.main:app --port 8000 --reload

# Terminal 2 — frontend (from frontend/)
npm run dev
```

Then open http://localhost:5173. The Vite dev server proxies `/api/*` to the
backend on port 8000 (see `frontend/vite.config.ts`).

If you're driving this through the Claude Code browser-preview tooling, both
processes are already registered in `.claude/launch.json` as `frontend` and
`backend`.

## How the data model works

- **`main` is read-only** in the UI — it reflects the current, real state of
  the world. All edits require an active forecast branch.
- **"+ Forecast"** (top right) creates a new branch in the data repo and
  switches to it. Edits there autosave as git commits a few seconds after you
  stop typing (visible via `git log` in `version-controlled-data/`).
- The branch dropdown switches between `main` and any forecast branches.
- **"Merge to main"** squash-merges the current forecast branch into `main`
  as a single commit, making the scenario permanent. On a conflict, the merge
  is aborted cleanly (409 response) — recreate the forecast branch from the
  latest `main` and redo the edits.
- Per-year rate assumptions (inflation, interest, YoY contribution change,
  total annual contribution) are "sticky": set a value once and it carries
  forward (shown light/dashed) until overridden by an explicit later-year
  value (shown solid).
- The Fully Funded Balance view needs a **Current Reserve Balance**, set once
  in the Income/Expenses Parameters table, to compute actual $ and % funded
  against the theoretical FFB target — until one is set, the FFB view shows
  targets only.

## Bulk-importing components from a spreadsheet

For a one-time load of many components (e.g. migrating an existing reserve
study), use `backend/scripts/import_components.py` instead of adding them
one at a time through the UI.

1. Prepare a staging CSV with these columns (any others are ignored, and
   `category_code`/`notes` may be blank or omitted):

   ```
   name,estimated_cost,initial_year,expected_life_years,category_code,notes
   ```

   Don't include an `id` column — the script generates a real UUID per row.
   Valid `category_code` values are whatever's in `version-controlled-data/categories.csv`
   (currently `CH`, `IN`, `OS`, `OB`, `PO` — see that file to add/rename categories).

2. Create a forecast branch to import onto (imports are blocked on `main`,
   same as the UI):

   ```bash
   cd version-controlled-data && git checkout -b import-components
   ```

3. Run the script:

   ```bash
   cd backend
   .venv/bin/python scripts/import_components.py /path/to/staged.csv
   ```

   It validates every row before writing anything — cost/life must be
   positive numbers, category codes must be known — and reports every bad
   row (with its line number) at once rather than stopping at the first.
   On success it commits the import as a single commit on your forecast
   branch.

4. Review (`git -C version-controlled-data show --stat HEAD`), then merge
   permanently via the app's "Merge to main" button.

## Running tests

```bash
cd backend
.venv/bin/pytest
```

## Project layout

```
backend/            FastAPI app, calculation engine, CSV data layer, tests
frontend/            React + TypeScript + Vite + Tailwind UI
version-controlled-data/   Separate git repo holding the actual reserve data (gitignored)
```
