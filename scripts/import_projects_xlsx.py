"""One-time import of the "ESRsWithLeads.xlsx" ServiceNow export (RITMs for
all Federal Leads, with the Federal Lead column manually added in Excel since
ServiceNow doesn't expose that catalog variable as a list column/filter) into
the projects DynamoDB table. Re-running this will add duplicate entries; it
does not currently check for existing records by number.

Usage:
    python3 scripts/import_projects_xlsx.py /path/to/ESRsWithLeads.xlsx
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db  # noqa: E402  (path must be adjusted before this import)
from importers import MissingColumnsError, parse_projects_xlsx  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    xlsx_path = sys.argv[1]
    db.ensure_table_exists(db.PROJECTS_TABLE_NAME)

    with open(xlsx_path, "rb") as f:
        try:
            result = parse_projects_xlsx(f)
        except MissingColumnsError as e:
            print(f"Error: {e}")
            sys.exit(1)

    for fields in result.records:
        db.create_project(**fields)

    print(f"Imported {len(result.records)} projects into {db.PROJECTS_TABLE_NAME}")
    if result.skipped:
        print(f"Skipped {result.skipped} row(s) missing a Number")


if __name__ == "__main__":
    main()

