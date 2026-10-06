"""One-time import of a ServiceNow sc_req_item CSV export (with the OCIO
Federal Lead catalog variable included as a `variables.<sys_id>` column) into
the projects DynamoDB table. Re-running this will add duplicate entries; it
does not currently check for existing records by number.

Usage:
    python3 scripts/import_projects_csv.py /path/to/ESRsWithLeads.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db  # noqa: E402  (path must be adjusted before this import)
from importers import MissingColumnsError, parse_projects_csv  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    csv_path = sys.argv[1]
    db.ensure_table_exists(db.PROJECTS_TABLE_NAME)

    with open(csv_path, newline="", encoding="cp1252") as f:
        try:
            result = parse_projects_csv(f)
        except MissingColumnsError as e:
            print(f"Error: {e}")
            sys.exit(1)

    for fields in result.records:
        db.create_project(**fields)

    print(f"Imported {len(result.records)} projects into {db.PROJECTS_TABLE_NAME}")
    if result.skipped:
        print(f"Skipped {result.skipped} row(s) missing a number")


if __name__ == "__main__":
    main()
