"""Streaming deduplicate keeps last row per key without full in-memory rewrite when unique."""
from __future__ import annotations

import csv
from pathlib import Path

from scripts.run_gwo_population_distribution_audit import count_rows, deduplicate


def _write(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["variant", "instance", "seed", "generation", "wolf_index", "value"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_deduplicate_keeps_last_and_skips_rewrite_when_unique(tmp_path: Path) -> None:
    path = tmp_path / "populations.csv"
    _write(
        path,
        [
            {"variant": "a", "instance": "t", "seed": "0", "generation": "0", "wolf_index": "0", "value": "old"},
            {"variant": "a", "instance": "t", "seed": "0", "generation": "0", "wolf_index": "0", "value": "new"},
            {"variant": "a", "instance": "t", "seed": "0", "generation": "0", "wolf_index": "1", "value": "only"},
        ],
    )
    keys = ["variant", "instance", "seed", "generation", "wolf_index"]
    deduplicate(path, keys)
    assert count_rows(path) == 2
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert rows[0]["value"] == "new"
    assert rows[1]["wolf_index"] == "1"

    before = path.read_bytes()
    deduplicate(path, keys)
    assert path.read_bytes() == before
