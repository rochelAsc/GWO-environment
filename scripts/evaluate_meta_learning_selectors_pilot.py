"""Exploratory leave-one-instance-out evaluation of meta selectors on pilot freeze."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import LeaveOneGroupOut

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FREEZE = ROOT / "experiments/meta_learning/data/metabasis_pilot_v1"
DEFAULT_OUT = ROOT / "results/meta_learning_metabasis_pilot_v1/selector_eval_exploratory_v1"
VARIANTS = ("baseline", "optuna", "fuzzy", "surrogate")
METADATA_COLS = ("instance", "sha256", "feature_version")


def _regret(y_row: dict[str, float], choice: str) -> float:
    best = min(y_row[v] for v in VARIANTS)
    return float(y_row[choice] - best)


def _bootstrap_mean_ci(values: np.ndarray, rng: np.random.Generator, n_boot: int = 2000):
    if len(values) == 0:
        return {"mean": None, "ci95": [None, None]}
    means = []
    n = len(values)
    for _ in range(n_boot):
        sample = values[rng.integers(0, n, size=n)]
        means.append(float(np.mean(sample)))
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {"mean": float(np.mean(values)), "median": float(np.median(values)), "ci95": [float(lo), float(hi)]}


def _paired_wins(a: np.ndarray, b: np.ndarray) -> dict[str, int]:
    return {
        "a_better": int(np.sum(a < b)),
        "b_better": int(np.sum(b < a)),
        "ties": int(np.sum(a == b)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-dir", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--random-repeats", type=int, default=100)
    args = parser.parse_args()

    freeze_dir = args.freeze_dir.resolve()
    features = pd.read_csv(freeze_dir / "instance_features.csv")
    targets = pd.read_csv(freeze_dir / "per_instance_targets.csv")
    merged = features.merge(targets, on="instance", how="inner", validate="one_to_one")
    if len(merged) != len(features) or len(merged) != len(targets):
        raise SystemExit("features/targets instance mismatch after merge")

    predictor_cols = [c for c in features.columns if c not in METADATA_COLS]
    X = merged[predictor_cols].to_numpy(dtype=float)
    y_class = merged["winner"].to_numpy()
    y_reg = merged[[f"y_{v}" for v in VARIANTS]].to_numpy(dtype=float)
    groups = merged["instance"].to_numpy()
    y_lookup = {
        row.instance: {v: float(getattr(row, f"y_{v}")) for v in VARIANTS}
        for row in merged.itertuples(index=False)
    }

    logo = LeaveOneGroupOut()
    rng = np.random.default_rng(args.seed)

    records: list[dict[str, object]] = []
    for fold, (train_idx, test_idx) in enumerate(logo.split(X, y_class, groups)):
        assert len(test_idx) == 1
        i = int(test_idx[0])
        inst = str(groups[i])
        y_true = y_lookup[inst]

        train_winners = y_class[train_idx]
        counts = {v: int(np.sum(train_winners == v)) for v in VARIANTS}
        best_global = max(VARIANTS, key=lambda v: (counts[v], -VARIANTS.index(v)))

        clf = RandomForestClassifier(
            n_estimators=200,
            random_state=args.seed,
            class_weight="balanced",
        )
        clf.fit(X[train_idx], y_class[train_idx])
        clf_choice = str(clf.predict(X[test_idx])[0])

        reg = RandomForestRegressor(n_estimators=200, random_state=args.seed)
        reg.fit(X[train_idx], y_reg[train_idx])
        pred = reg.predict(X[test_idx])[0]
        reg_choice = VARIANTS[int(np.argmin(pred))]

        random_choices = [VARIANTS[int(rng.integers(0, len(VARIANTS)))] for _ in range(args.random_repeats)]
        random_regrets = [_regret(y_true, c) for c in random_choices]

        row = {
            "fold": fold,
            "instance": inst,
            "jobs": int(merged.iloc[i]["jobs"]),
            "machines": int(merged.iloc[i]["machines"]),
            "true_winner": str(y_class[i]),
            "low_confidence": int(merged.iloc[i]["low_confidence"]),
            "margin_y": float(merged.iloc[i]["margin_y"]),
            "choice_rf_classifier": clf_choice,
            "choice_rf_regressor": reg_choice,
            "choice_best_global_train": best_global,
            "regret_rf_classifier": _regret(y_true, clf_choice),
            "regret_rf_regressor": _regret(y_true, reg_choice),
            "regret_best_global_train": _regret(y_true, best_global),
            "regret_random_mean": float(np.mean(random_regrets)),
            "hit_rf_classifier": int(clf_choice == y_class[i]),
            "hit_rf_regressor": int(reg_choice == y_class[i]),
        }
        for v in VARIANTS:
            row[f"regret_always_{v}"] = _regret(y_true, v)
            row[f"choice_always_{v}"] = v
        records.append(row)

    frame = pd.DataFrame.from_records(records)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out / "per_instance_predictions.csv", index=False)

    selectors = {
        "rf_classifier": frame["regret_rf_classifier"].to_numpy(),
        "rf_regressor": frame["regret_rf_regressor"].to_numpy(),
        "best_global_train": frame["regret_best_global_train"].to_numpy(),
        "random_mean": frame["regret_random_mean"].to_numpy(),
        **{f"always_{v}": frame[f"regret_always_{v}"].to_numpy() for v in VARIANTS},
    }
    fuzzy = selectors["always_fuzzy"]
    summary = {
        "protocol": "leave_one_instance_out",
        "n_instances": int(len(frame)),
        "feature_version": str(features["feature_version"].iloc[0]),
        "seed": args.seed,
        "random_repeats": args.random_repeats,
        "exploratory": True,
        "primary_metric": "per_instance_regret_vs_oracle",
        "selector_regret": {
            name: _bootstrap_mean_ci(vals, np.random.default_rng(args.seed + 1))
            for name, vals in selectors.items()
        },
        "accuracy": {
            "rf_classifier": float(frame["hit_rf_classifier"].mean()),
            "rf_regressor": float(frame["hit_rf_regressor"].mean()),
        },
        "paired_vs_always_fuzzy": {
            name: _paired_wins(vals, fuzzy)
            for name, vals in selectors.items()
            if name != "always_fuzzy"
        },
        "notes": [
            "Pilot exploratory evaluation only; n=36, many low-margin labels.",
            "Do not claim confirmatory generalization.",
            "Operational comparator: always_fuzzy.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("N_INST", summary["n_instances"])
    print("ACCURACY", summary["accuracy"])
    for name, stats in summary["selector_regret"].items():
        print(
            "REGRET",
            name,
            "mean=",
            round(stats["mean"], 6),
            "median=",
            round(stats["median"], 6),
            "ci95=",
            [round(x, 6) for x in stats["ci95"]],
        )
    print("PAIRED_VS_FUZZY", summary["paired_vs_always_fuzzy"])
    print("WROTE", out)


if __name__ == "__main__":
    main()
