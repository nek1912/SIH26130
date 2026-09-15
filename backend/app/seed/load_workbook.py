"""One-time workbook parser.

Parses the frozen Excel workbook and outputs Python data structures
that can be copied into workbook_data.py / scenario.py / approvals.py.

Usage:
    python -m app.seed.load_workbook --workbook path/to/workbook.xlsx

This script is NOT imported at runtime. It is a development tool
for regenerating seed data if the workbook is updated.
"""
from __future__ import annotations

import argparse
import json
import sys

try:
    import openpyxl
except ImportError:
    print("openpyxl required: pip install openpyxl", file=sys.stderr)
    sys.exit(1)


def parse_sheet(ws, header_row: int = 3) -> list[dict]:
    """Parse a worksheet into a list of dicts, skipping title/empty rows."""
    rows = list(ws.iter_rows(min_row=header_row, values_only=True))
    if not rows:
        return []
    headers = [
        str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])
    ]
    result = []
    for row in rows[1:]:
        if all(c is None for c in row):
            continue
        record = {}
        for h, v in zip(headers, row):
            if h.startswith("col_"):
                continue
            record[h] = v
        result.append(record)
    return result


def main():
    parser = argparse.ArgumentParser(description="Parse Gujarat workbook")
    parser.add_argument(
        "--workbook", required=True, help="Path to .xlsx file"
    )
    args = parser.parse_args()

    wb = openpyxl.load_workbook(args.workbook, read_only=True)

    sheets_to_parse = [
        "Scenario_Profile",
        "Approval_Register",
        "Rule_Register",
        "Document_Register",
        "Sources",
        "Expected_Test_Results",
        "Chemical_Inventory",
        "Jurisdiction",
        "Consistency_Fields",
        "Verification_Log",
        "Research_Gaps",
    ]

    for name in sheets_to_parse:
        if name in wb.sheetnames:
            ws = wb[name]
            data = parse_sheet(ws)
            print(f"\n# === {name} ({len(data)} rows) ===")
            print(f"# Headers: {list(data[0].keys()) if data else []}")
            print(json.dumps(data[:3], indent=2, default=str))
            if len(data) > 3:
                print(f"# ... {len(data) - 3} more rows")
        else:
            print(f"# Sheet {name} not found")

    wb.close()


if __name__ == "__main__":
    main()
