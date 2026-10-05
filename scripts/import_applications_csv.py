"""One-time import of a ServiceNow CMDB Business Application CSV export into
the applications DynamoDB table. Re-running this will add duplicate entries;
it does not currently check for existing records by name.

Usage:
    python3 scripts/import_applications_csv.py /path/to/cmdb_ci_business_app.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db  # noqa: E402  (path must be adjusted before this import)
from importers import MissingColumnsError, parse_applications_csv  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    csv_path = sys.argv[1]
    db.ensure_table_exists(db.APPLICATIONS_TABLE_NAME)

    with open(csv_path, newline="", encoding="cp1252") as f:
        try:
            result = parse_applications_csv(f)
        except MissingColumnsError as e:
            print(f"Error: {e}")
            sys.exit(1)

    for fields in result.records:
        db.create_application(**fields)

    print(f"Imported {len(result.records)} applications into {db.APPLICATIONS_TABLE_NAME}")
    if result.skipped:
        print(f"Skipped {result.skipped} row(s) missing a name")


if __name__ == "__main__":
    main()
