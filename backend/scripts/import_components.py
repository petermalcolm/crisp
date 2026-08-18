#!/usr/bin/env python3
"""One-time bulk import of reserve components from a prepared staging CSV.

Usage (from backend/, with the venv active):

    .venv/bin/python scripts/import_components.py path/to/staged.csv

The staging CSV should have these columns (any others are ignored):

    name,estimated_cost,initial_year,expected_life_years,category_code,notes

`category_code` and `notes` may be blank or omitted entirely. Do NOT include
an `id` column — this script generates a real UUID for each row; the system
doesn't use spreadsheet row numbers as ids (forecast branches are edited
independently before merging, so ids must never collide across branches).

The data repo must be on a forecast branch (not main) — same rule the app's
own UI enforces. Create one first:

    cd version-controlled-data && git checkout -b import-components

After this script runs, review the diff and either let it ride until you're
ready to merge via the UI's "Merge to main" button, or inspect/commit further
by hand.
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402
from app.core.calc.costs import Component  # noqa: E402
from app.data import csv_store, git_ops  # noqa: E402

REQUIRED_COLUMNS = {
    "name",
    "estimated_cost",
    "initial_year",
    "expected_life_years",
}
OPTIONAL_COLUMNS = {"category_code", "notes"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_path", type=Path, help="Path to the staging CSV")
    parser.add_argument(
        "--data-repo",
        type=Path,
        default=settings.data_repo_path,
        help="Override the data repo path (defaults to the app's configured path)",
    )
    return parser.parse_args()


def load_staging_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        header = {h.strip().lower() for h in (reader.fieldnames or [])}
        missing = REQUIRED_COLUMNS - header
        if missing:
            sys.exit(
                f"Staging CSV is missing required column(s): {', '.join(sorted(missing))}\n"
                f"Found columns: {', '.join(reader.fieldnames or [])}"
            )
        ignored = header - REQUIRED_COLUMNS - OPTIONAL_COLUMNS
        if ignored:
            print(f"Note: ignoring unrecognized column(s): {', '.join(sorted(ignored))}")
        return [
            {k.strip().lower(): (v or "").strip() for k, v in row.items()}
            for row in reader
        ]


def validate_and_build(
    rows: list[dict[str, str]], known_category_codes: set[str]
) -> list[Component]:
    errors: list[str] = []
    components: list[Component] = []

    for i, row in enumerate(rows, start=2):  # +1 header, +1 to be 1-indexed
        name = row.get("name", "")
        if not name:
            errors.append(f"Row {i}: name is blank")
            continue

        try:
            estimated_cost = float(row["estimated_cost"])
            if estimated_cost <= 0:
                errors.append(f"Row {i} ({name}): estimated_cost must be > 0, got {estimated_cost}")
                continue
        except ValueError:
            errors.append(f"Row {i} ({name}): estimated_cost '{row.get('estimated_cost')}' is not a number")
            continue

        try:
            initial_year = int(float(row["initial_year"]))
        except ValueError:
            errors.append(f"Row {i} ({name}): initial_year '{row.get('initial_year')}' is not an integer")
            continue

        try:
            expected_life_years = int(float(row["expected_life_years"]))
            if expected_life_years <= 0:
                errors.append(f"Row {i} ({name}): expected_life_years must be > 0, got {expected_life_years}")
                continue
        except ValueError:
            errors.append(
                f"Row {i} ({name}): expected_life_years '{row.get('expected_life_years')}' is not an integer"
            )
            continue

        category_code = row.get("category_code") or None
        if category_code and category_code not in known_category_codes:
            errors.append(
                f"Row {i} ({name}): unknown category_code '{category_code}' "
                f"(known: {', '.join(sorted(known_category_codes))})"
            )
            continue

        notes = row.get("notes") or None

        components.append(
            Component(
                id=csv_store.new_id(),
                name=name,
                estimated_cost=estimated_cost,
                initial_year=initial_year,
                expected_life_years=expected_life_years,
                category_code=category_code,
                notes=notes,
            )
        )

    if errors:
        print(f"\n{len(errors)} row(s) failed validation — nothing was imported:\n")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    return components


def main() -> None:
    args = parse_args()
    data_repo = args.data_repo

    current_branch = git_ops.current_branch(data_repo)
    if current_branch == "main":
        sys.exit(
            "Refusing to import onto 'main' — it's read-only, same as in the app.\n"
            "Create a forecast branch first:\n\n"
            f"    cd {data_repo} && git checkout -b import-components\n"
        )

    if not args.csv_path.exists():
        sys.exit(f"No such file: {args.csv_path}")

    staging_rows = load_staging_rows(args.csv_path)
    known_categories = csv_store.read_categories(data_repo)
    known_category_codes = {c.code for c in known_categories}

    new_components = validate_and_build(staging_rows, known_category_codes)

    existing = csv_store.read_components(data_repo)
    csv_store.write_components(data_repo, existing + new_components)

    committed = git_ops.commit_all(
        data_repo, f"Import {len(new_components)} components from spreadsheet"
    )

    by_category: dict[str, int] = {}
    for c in new_components:
        key = c.category_code or "(none)"
        by_category[key] = by_category.get(key, 0) + 1

    print(f"\nImported {len(new_components)} components onto branch '{current_branch}'.")
    print("By category:")
    for code, count in sorted(by_category.items()):
        print(f"  {code}: {count}")
    print(
        "\nCommitted."
        if committed
        else "\nNothing to commit (working tree already matched)."
    )
    print(f"Review with: git -C {data_repo} show --stat HEAD")
    print("When ready, merge via the app UI's \"Merge to main\" button.")


if __name__ == "__main__":
    main()
