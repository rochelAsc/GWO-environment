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
            if not name.endswith("/") and PurePosixPath(name).suffix.lower() in {".txt", ".dat", ".ins"}
        ]
        for name in candidates:
            try:
                text = archive.read(name).decode("utf-8-sig")
                instance = parse_dpfsp_instance_text(text, source=name)
                parsed.append(name)
                jobs_distribution[str(instance.jobs)] += 1
                machines_distribution[str(instance.machines)] += 1
                factories_distribution[str(instance.factories)] += 1
            except Exception as exc:
                failures.append({
                    "path": name,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                })

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
