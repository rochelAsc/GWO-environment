"""Plot mean best-so-far makespan with ±1 sample standard deviation."""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


def plot(convergence_csv: Path, output_dir: Path) -> None:
    grouped = defaultdict(list)
    with convergence_csv.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            grouped[row["instance"]].append((
                int(row["generation"]),
                float(row["mean_best_makespan"]),
                float(row["std_best_makespan"]),
            ))

    output_dir.mkdir(parents=True, exist_ok=True)
    for instance, rows in sorted(grouped.items()):
        rows.sort(key=lambda item: item[0])
        x = [r[0] for r in rows]
        mean = [r[1] for r in rows]
        std = [r[2] for r in rows]
        lower = [m - s for m, s in zip(mean, std)]
        upper = [m + s for m, s in zip(mean, std)]

        fig, ax = plt.subplots(figsize=(9, 5))
        ax.plot(x, mean, label="Média do melhor makespan")
        ax.fill_between(x, lower, upper, alpha=0.2, label="±1 desvio padrão")
        ax.set_title(f"Convergência GWO — {instance}")
        ax.set_xlabel("Geração")
        ax.set_ylabel("Melhor makespan (Cmax)")
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(output_dir / f"{instance}_convergence.png", dpi=180)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("results/week2_baseline_v2/convergence.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/week2_baseline_v2/figures"),
    )
    args = parser.parse_args()
    plot(args.input, args.output)


if __name__ == "__main__":
    main()
