#!/usr/bin/env python3
"""Inventory DPFSP_DD ZIP entries without extracting the archive.

Usage:
    python scripts/inventory_dpfsp_zip.py data/instances/DPFSP_DD.zip
    python scripts/inventory_dpfsp_zip.py data/instances/DPFSP_DD.zip --output results/instance_inventory

The default pass reads ZIP metadata and only the first two non-empty text
lines of each candidate instance. It does not load whole instances into memory.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from collections import Counter
from pathlib import PurePosixPath


def first_nonempty_lines(archive: zipfile.ZipFile, member: str, count: int = 3):
    lines = []
    with archive.open(member, "r") as stream:
        for raw in stream:
            line = raw.decode("utf-8-sig", errors="replace").strip()
            if line:
                lines.append(line)
                if len(lines) >= count:
                    break
    return lines


def parse_integer_tokens(line: str):
    return [int(token) for token in re.findall(r"(?<![\\w.])-?\\d+(?![\\w.])", line)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path")
    parser.add_argument("--output", default="results/instance_inventory")
    args = parser.parse_args()

    rows = []
    errors = []
    with zipfile.ZipFile(args.zip_path) as archive:
        members = [info for info in archive.infolist() if not info.is_dir()]
        candidates = [
            info for info in members
            if PurePosixPath(info.filename).suffix.lower() in {".txt", ".dat", ".ins"}
        ]

        for info in candidates:
            row = {
                "path": info.filename,
                "size_bytes": info.file_size,
                "compressed_bytes": info.compress_size,
                "crc32": f"{info.CRC:08x}",
                "jobs": None,
                "machines": None,
                "third_line_integer": None,
                "first_line": None,
                "second_line": None,
                "third_line": None,
                "read_error": None,
            }
            try:
                lines = first_nonempty_lines(archive, info.filename, 3)
                for i, line in enumerate(lines):
                    row[("first_line", "second_line", "third_line")[i]] = line
                if lines:
                    dims = parse_integer_tokens(lines[0])
                    if len(dims) >= 2:
                        row["jobs"], row["machines"] = dims[:2]
                if len(lines) >= 2:
                    third = parse_integer_tokens(lines[1])
                    if len(third) == 1:
                        row["third_line_integer"] = third[0]
            except Exception as exc:
                row["read_error"] = f"{type(exc).__name__}: {exc}"
                errors.append({"path": info.filename, "error": row["read_error"]})
            rows.append(row)

    from pathlib import Path
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    csv_path = output / "instances.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else [
            "path", "size_bytes", "compressed_bytes", "crc32", "jobs",
            "machines", "third_line_integer", "first_line", "second_line",
            "third_line", "read_error"
        ])
        writer.writeheader()
        writer.writerows(rows)

    jobs = Counter(str(row["jobs"]) for row in rows if row["jobs"] is not None)
    machines = Counter(str(row["machines"]) for row in rows if row["machines"] is not None)
    third_values = Counter(
        str(row["third_line_integer"])
        for row in rows if row["third_line_integer"] is not None
    )
    summary = {
        "archive": args.zip_path,
        "archive_bytes": __import__("os").path.getsize(args.zip_path),
        "total_zip_entries": len(members),
        "candidate_instance_files": len(candidates),
        "read_errors": len(errors),
        "jobs_distribution": dict(jobs),
        "machines_distribution": dict(machines),
        "second_line_integer_distribution": dict(third_values),
        "total_uncompressed_candidate_bytes": sum(x.file_size for x in candidates),
        "errors": errors,
        "note": (
            "Only ZIP metadata and the first three non-empty lines of each "
            "candidate file were inspected. No archive entries were extracted."
        ),
    }
    json_path = output / "summary.json"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\\nCSV: {csv_path}\\nJSON: {json_path}")


if __name__ == "__main__":
    main()
