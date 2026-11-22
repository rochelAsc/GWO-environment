#!/usr/bin/env python3
"""Validate the DPFSP-DD parser against every text instance inside the ZIP.

Usage:
    python scripts/validate_dpfsp_parser.py data/instances/DPFSP_DD.zip
    python scripts/validate_dpfsp_parser.py data/instances/DPFSP_DD.zip --output results/parser_validation/summary.json

The script reads entries directly from the ZIP; it does not extract or modify it.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

from dpfsp_dd import parse_dpfsp_instance_text


CANDIDATE_SUFFIXES = {".txt", ".dat", ".ins"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path")
    parser.add_argument("--output", default="results/parser_validation/summary.json")
    args = parser.parse_args()

    parsed = []
    failures = []
    jobs_distribution = Counter()
    machines_distribution = Counter()
    factories_distribution = Counter()

    with zipfile.ZipFile(args.zip_path) as archive:
        candidates = [
            name for name in archive.namelist()
            if not name.endswith("/")
            and PurePosixPath(name).suffix.lower() in CANDIDATE_SUFFIXES
        ]
        if not candidates:
            raise ValueError(
                f"No candidate instance files found in {args.zip_path!r}; "
                f"expected files with extensions: {', '.join(sorted(CANDIDATE_SUFFIXES))}"
            )

        for name in candidates:
            try:
                instance_text = archive.read(name).decode("utf-8-sig")
            except UnicodeDecodeError as exc:
                failures.append({
                    "path": name,
                    "error_type": type(exc).__name__,
                    "message": f"file is not valid UTF-8: {exc}",
                })
                continue

            try:
                instance = parse_dpfsp_instance_text(instance_text, source=name)
            except ValueError as exc:
                # ValueError is the parser's documented signal for malformed instance data.
                failures.append({
                    "path": name,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                })
                continue

            parsed.append(name)
            jobs_distribution[str(instance.jobs)] += 1
            machines_distribution[str(instance.machines)] += 1
            factories_distribution[str(instance.factories)] += 1

    summary = {
        "archive": args.zip_path,
        "candidate_files": len(candidates),
        "parsed_successfully": len(parsed),
        "failed": len(failures),
        "jobs_distribution": dict(sorted(jobs_distribution.items(), key=lambda item: int(item[0]))),
        "machines_distribution": dict(sorted(machines_distribution.items(), key=lambda item: int(item[0]))),
        "factories_distribution": dict(sorted(factories_distribution.items(), key=lambda item: int(item[0]))),
        "failures": failures,
        "note": "All entries were parsed directly from the ZIP; no extraction or archive modification occurred.",
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
