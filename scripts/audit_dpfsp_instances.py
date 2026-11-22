#!/usr/bin/env python3
"""Audit every DPFSP_DD instance in a ZIP without extracting archive entries.

Usage:
    python scripts/audit_dpfsp_instances.py data/instances/DPFSP_DD.zip
    python scripts/audit_dpfsp_instances.py data/instances/DPFSP_DD.zip \
        --output results/instance_audit

The audit reads each candidate instance completely in memory (the current
archive is small), validates its structure, and writes per-file, per-family,
and aggregate reports. The ZIP itself is never extracted or modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath


CANDIDATE_SUFFIXES = {".txt", ".dat", ".ins"}
EXPECTED_VARIANTS = {"Small": set(range(1, 6)), "Large": set(range(2, 8))}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def integer_tokens(line: str):
    """Return integer tokens, or None if any token is not an integer."""
    try:
        return [int(token) for token in line.split()]
    except ValueError:
        return None


def add_issue(issues, code, severity, detail):
    issues.append({"code": code, "severity": severity, "detail": detail})


def parse_instance(member: str, raw: bytes):
    """Parse and validate the observed two-header / processing / due-date format."""
    issues = []
    row = {
        "path": member,
        "size_bytes": len(raw),
        "sha256": sha256(raw),
        "jobs": None,
        "machines": None,
        "second_line_integer": None,
        "processing_rows_found": 0,
        "processing_rows_expected": None,
        "processing_values_found": 0,
        "processing_time_min": None,
        "processing_time_max": None,
        "due_dates_found": 0,
        "due_dates_expected": None,
        "due_date_min": None,
        "due_date_max": None,
        "processing_sha256": None,
        "due_dates_sha256": None,
        "family": None,
        "variant": None,
        "folder": PurePosixPath(member).parent.name,
        "status": "invalid",
        "issue_codes": "",
        "issue_details": "",
    }

    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        add_issue(issues, "INVALID_UTF8", "error", str(exc))
        row["issue_codes"] = "INVALID_UTF8"
        row["issue_details"] = str(exc)
        return row, issues

    nonempty = [
        (line_no, line.strip())
        for line_no, line in enumerate(decoded.splitlines(), start=1)
        if line.strip()
    ]
    if len(nonempty) < 2:
        add_issue(issues, "HEADER_LINES_MISSING", "error",
                  f"Expected two non-empty header lines; found {len(nonempty)}")
        row["issue_codes"] = ";".join(x["code"] for x in issues)
        row["issue_details"] = " | ".join(x["detail"] for x in issues)
        return row, issues

    header = integer_tokens(nonempty[0][1])
    if header is None or len(header) != 2 or min(header) <= 0:
        add_issue(issues, "INVALID_DIMENSION_HEADER", "error",
                  f"Line {nonempty[0][0]} must contain exactly two positive integers")
    else:
        row["jobs"], row["machines"] = header
        row["processing_rows_expected"] = header[0]
        row["due_dates_expected"] = header[0]

    second = integer_tokens(nonempty[1][1])
    if second is None or len(second) != 1 or second[0] <= 0:
        add_issue(issues, "INVALID_SECOND_HEADER", "error",
                  f"Line {nonempty[1][0]} must contain exactly one positive integer")
    else:
        row["second_line_integer"] = second[0]

    marker_positions = [
        i for i, (_, value) in enumerate(nonempty[2:], start=2)
        if value.casefold() == "duedate"
    ]
    if not marker_positions:
        add_issue(issues, "DUEDATE_MARKER_MISSING", "error",
                  "No Duedate marker found after the two header lines")
        processing_lines = nonempty[2:]
        due_lines = []
    else:
        marker = marker_positions[0]
        processing_lines = nonempty[2:marker]
        due_lines = nonempty[marker + 1:]
        if len(marker_positions) > 1:
            add_issue(issues, "MULTIPLE_DUEDATE_MARKERS", "error",
                      f"Found {len(marker_positions)} Duedate markers")

    row["processing_rows_found"] = len(processing_lines)
    row["due_dates_found"] = len(due_lines)

    if row["jobs"] is not None and len(processing_lines) != row["jobs"]:
        add_issue(issues, "PROCESSING_ROW_COUNT_MISMATCH", "error",
                  f"Expected {row['jobs']} job rows; found {len(processing_lines)}")

    processing_matrix = []
    processing_values = []
    if row["machines"] is not None:
        expected_machine_ids = list(range(row["machines"]))
        for line_no, line in processing_lines:
            values = integer_tokens(line)
            if values is None:
                add_issue(issues, "NON_INTEGER_PROCESSING_ROW", "error",
                          f"Line {line_no} contains a non-integer token")
                continue
            if len(values) != 2 * row["machines"]:
                add_issue(issues, "PROCESSING_TOKEN_COUNT_MISMATCH", "error",
                          f"Line {line_no}: expected {2 * row['machines']} integers; found {len(values)}")
                continue
            pairs = list(zip(values[0::2], values[1::2]))
            machine_ids = [pair[0] for pair in pairs]
            times = [pair[1] for pair in pairs]
            if sorted(machine_ids) != expected_machine_ids:
                add_issue(issues, "MACHINE_INDEX_SET_MISMATCH", "error",
                          f"Line {line_no}: machine indices must be exactly {expected_machine_ids}; found {machine_ids}")
            if any(value <= 0 for value in times):
                add_issue(issues, "NON_POSITIVE_PROCESSING_TIME", "error",
                          f"Line {line_no}: processing times must be positive")
            processing_matrix.append(pairs)
            processing_values.extend(times)

    row["processing_values_found"] = len(processing_values)
    if processing_values:
        row["processing_time_min"] = min(processing_values)
        row["processing_time_max"] = max(processing_values)
    if processing_matrix:
        row["processing_sha256"] = sha256(
            json.dumps(processing_matrix, separators=(",", ":")).encode("utf-8")
        )

    due_dates = []
    for line_no, line in due_lines:
        values = integer_tokens(line)
        if values is None or len(values) != 1:
            add_issue(issues, "INVALID_DUE_DATE_LINE", "error",
                      f"Line {line_no}: expected exactly one integer due date")
            continue
        if values[0] < 0:
            add_issue(issues, "NEGATIVE_DUE_DATE", "error",
                      f"Line {line_no}: due date must be non-negative")
        due_dates.append(values[0])

    if row["jobs"] is not None and len(due_lines) != row["jobs"]:
        add_issue(issues, "DUE_DATE_COUNT_MISMATCH", "error",
                  f"Expected {row['jobs']} due-date lines; found {len(due_lines)}")
    if row["jobs"] is not None and len(due_dates) != row["jobs"]:
        # The line-level issue above may explain this; this count records parsed values.
        add_issue(issues, "PARSED_DUE_DATE_COUNT_MISMATCH", "error",
                  f"Expected {row['jobs']} parsed due dates; found {len(due_dates)}")
    if due_dates:
        row["due_date_min"] = min(due_dates)
        row["due_date_max"] = max(due_dates)
        row["due_dates_sha256"] = sha256(
            json.dumps(due_dates, separators=(",", ":")).encode("utf-8")
        )

    # Filename checks are deliberately metadata checks; they do not assign
    # a semantic name to the second header field.
    stem = PurePosixPath(member).stem
    if row["folder"] == "Small":
        match = re.fullmatch(r"I_(\d+)_(\d+)_(\d+)_(\d+)", stem)
        if not match:
            add_issue(issues, "UNRECOGNIZED_SMALL_FILENAME", "warning",
                      f"Filename {stem!r} does not match I_<field>_<jobs>_<machines>_<replicate>")
        else:
            name_field, name_jobs, name_machines, replicate = map(int, match.groups())
            row["family"] = "_".join(stem.split("_")[:-1])
            row["variant"] = replicate
            for label, actual, expected in (
                ("second header", row["second_line_integer"], name_field),
                ("jobs", row["jobs"], name_jobs),
                ("machines", row["machines"], name_machines),
            ):
                if actual is not None and actual != expected:
                    add_issue(issues, "FILENAME_HEADER_MISMATCH", "warning",
                              f"Filename {label}={expected}, file header={actual}")
            if replicate not in EXPECTED_VARIANTS["Small"]:
                add_issue(issues, "UNEXPECTED_FILENAME_VARIANT", "warning",
                          f"Small replicate suffix {replicate} is outside 1..5")
    elif row["folder"] == "Large":
        match = re.fullmatch(r"(Ta\d+)_(\d+)", stem)
        if not match:
            add_issue(issues, "UNRECOGNIZED_LARGE_FILENAME", "warning",
                      f"Filename {stem!r} does not match Ta<id>_<variant>")
        else:
            family, variant = match.groups()
            row["family"] = family
            row["variant"] = int(variant)
            if row["second_line_integer"] is not None and row["second_line_integer"] != row["variant"]:
                add_issue(issues, "FILENAME_HEADER_MISMATCH", "warning",
                          f"Filename variant={row['variant']}, second header={row['second_line_integer']}")
            if row["variant"] not in EXPECTED_VARIANTS["Large"]:
                add_issue(issues, "UNEXPECTED_FILENAME_VARIANT", "warning",
                          f"Large variant {row['variant']} is outside 2..7")
    else:
        add_issue(issues, "UNEXPECTED_DIRECTORY", "warning",
                  f"Instance is under directory {row['folder']!r}, not Small or Large")

    errors = [x for x in issues if x["severity"] == "error"]
    warnings = [x for x in issues if x["severity"] == "warning"]
    row["status"] = "invalid" if errors else ("valid_with_warnings" if warnings else "valid")
    row["issue_codes"] = ";".join(x["code"] for x in issues)
    row["issue_details"] = " | ".join(x["detail"] for x in issues)
    return row, issues


def family_reports(rows):
    grouped = defaultdict(list)
    for row in rows:
        if row["family"]:
            grouped[(row["folder"], row["family"])].append(row)

    reports = []
    family_issues = []
    for (folder, family), members in sorted(grouped.items()):
        expected = EXPECTED_VARIANTS.get(folder, set())
        variants = [int(x["variant"]) for x in members if x["variant"] not in (None, "")]
        counts = Counter(variants)
        present = set(variants)
        missing = sorted(expected - present)
        unexpected = sorted(present - expected)
        duplicates = sorted(value for value, count in counts.items() if count > 1)
        jobs = sorted({int(x["jobs"]) for x in members if x["jobs"] not in (None, "")})
        machines = sorted({int(x["machines"]) for x in members if x["machines"] not in (None, "")})
        second_fields = sorted({
            int(x["second_line_integer"]) for x in members
            if x["second_line_integer"] not in (None, "")
        })
        processing_hashes = sorted({x["processing_sha256"] for x in members if x["processing_sha256"]})
        due_hashes = sorted({x["due_dates_sha256"] for x in members if x["due_dates_sha256"]})
        problems = []
        if missing:
            problems.append("missing variants: " + ",".join(map(str, missing)))
        if unexpected:
            problems.append("unexpected variants: " + ",".join(map(str, unexpected)))
        if duplicates:
            problems.append("duplicate variants: " + ",".join(map(str, duplicates)))
        if len(jobs) > 1 or len(machines) > 1:
            problems.append("inconsistent dimensions within family")
        # The second header is a per-variant field for Large families, not a
        # family-constant field. parse_instance() already checks that it matches
        # the filename suffix for each Large member; do not flag its variation.
        reports.append({
            "folder": folder,
            "family": family,
            "files_found": len(members),
            "expected_variants": ",".join(map(str, sorted(expected))),
            "present_variants": ",".join(map(str, sorted(present))),
            "missing_variants": ",".join(map(str, missing)),
            "unexpected_variants": ",".join(map(str, unexpected)),
            "duplicate_variants": ",".join(map(str, duplicates)),
            "jobs_values": ",".join(map(str, jobs)),
            "machines_values": ",".join(map(str, machines)),
            "second_line_values": ",".join(map(str, second_fields)),
            "distinct_processing_matrices": len(processing_hashes),
            "distinct_due_date_vectors": len(due_hashes),
            "family_status": "warning" if problems else "complete",
            "notes": " | ".join(problems),
        })
        if problems:
            family_issues.append({
                "code": "FAMILY_INCONSISTENCY",
                "severity": "warning",
                "detail": f"{folder}/{family}: " + " | ".join(problems),
            })
    return reports, family_issues


def write_csv(path: Path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", help="Path to DPFSP_DD.zip")
    parser.add_argument("--output", default="results/instance_audit",
                        help="Output directory (default: results/instance_audit)")
    args = parser.parse_args()

    zip_path = Path(args.zip_path)
    if not zip_path.is_file():
        raise SystemExit(f"ZIP file not found: {zip_path}")

    archive_digest = hashlib.sha256()
    with zip_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            archive_digest.update(chunk)

    rows = []
    all_issues = []
    with zipfile.ZipFile(zip_path) as archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        candidates = [
            item for item in members
            if PurePosixPath(item.filename).suffix.lower() in CANDIDATE_SUFFIXES
        ]
        for item in candidates:
            try:
                raw = archive.read(item)
                row, issues = parse_instance(item.filename, raw)
            except Exception as exc:
                row = {
                    "path": item.filename, "size_bytes": item.file_size,
                    "sha256": "", "jobs": None, "machines": None,
                    "second_line_integer": None, "processing_rows_found": 0,
                    "processing_rows_expected": None, "processing_values_found": 0,
                    "processing_time_min": None, "processing_time_max": None,
                    "due_dates_found": 0, "due_dates_expected": None,
                    "due_date_min": None, "due_date_max": None,
                    "processing_sha256": None, "due_dates_sha256": None,
                    "family": None, "variant": None,
                    "folder": PurePosixPath(item.filename).parent.name,
                    "status": "invalid", "issue_codes": "ARCHIVE_READ_ERROR",
                    "issue_details": f"{type(exc).__name__}: {exc}",
                }
                issues = [{
                    "code": "ARCHIVE_READ_ERROR", "severity": "error",
                    "detail": f"{item.filename}: {type(exc).__name__}: {exc}",
                }]
            rows.append(row)
            for issue in issues:
                all_issues.append({
                    "path": item.filename,
                    "code": issue["code"],
                    "severity": issue["severity"],
                    "detail": issue["detail"],
                })

    families, family_issues = family_reports(rows)
    all_issues.extend({
        "path": "",
        "code": issue["code"],
        "severity": issue["severity"],
        "detail": issue["detail"],
    } for issue in family_issues)

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "instances_audit.csv", rows)
    write_csv(output / "families.csv", families)
    write_csv(output / "issues.csv", all_issues)

    issue_counts = Counter(x["code"] for x in all_issues)
    severity_counts = Counter(x["severity"] for x in all_issues)
    by_folder = {}
    for folder in sorted({x["folder"] for x in rows}):
        subset = [x for x in rows if x["folder"] == folder]
        by_folder[folder] = {
            "files": len(subset),
            "valid": sum(x["status"] == "valid" for x in subset),
            "valid_with_warnings": sum(x["status"] == "valid_with_warnings" for x in subset),
            "invalid": sum(x["status"] == "invalid" for x in subset),
            "jobs_distribution": dict(Counter(str(x["jobs"]) for x in subset if x["jobs"] is not None)),
            "machines_distribution": dict(Counter(str(x["machines"]) for x in subset if x["machines"] is not None)),
            "second_line_integer_distribution": dict(Counter(
                str(x["second_line_integer"]) for x in subset if x["second_line_integer"] is not None
            )),
        }

    exact_duplicates = defaultdict(list)
    for row in rows:
        if row["sha256"]:
            exact_duplicates[row["sha256"]].append(row["path"])
    duplicate_groups = [
        paths for paths in exact_duplicates.values() if len(paths) > 1
    ]

    summary = {
        "archive": str(zip_path),
        "archive_bytes": zip_path.stat().st_size,
        "archive_sha256": archive_digest.hexdigest(),
        "total_zip_entries": len(members),
        "candidate_instance_files": len(candidates),
        "files_valid": sum(x["status"] == "valid" for x in rows),
        "files_valid_with_warnings": sum(x["status"] == "valid_with_warnings" for x in rows),
        "files_invalid": sum(x["status"] == "invalid" for x in rows),
        "exact_duplicate_content_groups": len(duplicate_groups),
        "duplicate_content_examples": duplicate_groups[:20],
        "families": {
            "total": len(families),
            "complete": sum(x["family_status"] == "complete" for x in families),
            "with_warnings": sum(x["family_status"] == "warning" for x in families),
            "by_folder": dict(Counter(x["folder"] for x in families)),
        },
        "by_folder": by_folder,
        "issue_counts": dict(issue_counts),
        "issue_severity_counts": dict(severity_counts),
        "issues_total": len(all_issues),
        "outputs": {
            "instances": str(output / "instances_audit.csv"),
            "families": str(output / "families.csv"),
            "issues": str(output / "issues.csv"),
        },
        "validation_rules": [
            "UTF-8 text with two non-empty header lines",
            "first header: exactly two positive integers (jobs, machines)",
            "second header: exactly one positive integer representing the number of factories (F)",
            "exactly one Duedate marker",
            "exactly jobs processing rows before Duedate",
            "each processing row: one machine-index/time pair per machine",
            "machine indices in each row must be exactly 0..machines-1",
            "processing times must be positive integers",
            "exactly jobs due-date lines after Duedate, one non-negative integer per line",
            "filename metadata and family variants checked separately from structural validity",
        ],
        "note": (
            "Every candidate file was read and checked in memory. No ZIP entries "
            "were extracted, modified, or written back to the archive. The second "
            "header integer is interpreted as the number of factories (F), as documented for this benchmark."
        ),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nReports written to: {output}")


if __name__ == "__main__":
    main()
