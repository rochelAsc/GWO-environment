"""Tune Week 3 PFSP GWO with Optuna under a fixed evaluation budget."""
from __future__ import annotations
import argparse, hashlib, json, platform, sys, time
from pathlib import Path
import numpy as np
import optuna
from optuna.samplers import TPESampler
from scripts.gwo_pfs import gwo_pfs
from scripts.pfs_taillard import load_taillard_instance

BUDGET = 15030
WOLF_CHOICES = [9, 10, 15, 18, 30, 45]
DEFAULT_INSTANCES = [Path("data/benchmarks/taillard/ta001.txt"), Path("data/benchmarks/taillard/ta011.txt")]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--training-seeds", nargs="+", type=int, default=[100, 101, 102])
    parser.add_argument("--instances", nargs="+", type=Path, default=DEFAULT_INSTANCES)
    parser.add_argument("--output", type=Path, default=Path("results/week3_optuna_v1"))
    parser.add_argument("--sampler-seed", type=int, default=20261123)
    args = parser.parse_args()
    if args.trials < 2 or not args.training_seeds:
        parser.error("--trials must be >= 2 and training seeds cannot be empty")
    args.output.mkdir(parents=True, exist_ok=True)
    instances = [load_taillard_instance(p) for p in args.instances]
    for instance in instances:
        if not instance.upper_bound or instance.upper_bound <= 0:
            parser.error(f"{instance.name} needs a positive published upper bound")

    db_path = (args.output / "study.db").resolve()
    study = optuna.create_study(
        study_name="week3_pfsp_makespan_tpe_v1",
        storage=f"sqlite:///{db_path.as_posix()}",
        direction="minimize",
        sampler=TPESampler(seed=args.sampler_seed),
        load_if_exists=False,
    )

    def objective(trial):
        wolves = trial.suggest_categorical("n_wolves", WOLF_CHOICES)
        iterations = BUDGET // wolves - 1
        if wolves * (iterations + 1) != BUDGET:
            raise RuntimeError("population does not divide the fixed budget")
        a_start = trial.suggest_float("a_start", 1.5, 2.5)
        a_end = trial.suggest_float("a_end", 0.0, 0.5)
        exponent = trial.suggest_float("a_exponent", 0.5, 2.0)
        per_instance, total_time, total_evals = {}, 0.0, 0
        for instance in instances:
            ratios = []
            for seed in args.training_seeds:
                start = time.perf_counter()
                result = gwo_pfs(
                    instance.processing_times, n_wolves=wolves, iterations=iterations,
                    seed=seed, a_start=a_start, a_end=a_end, a_exponent=exponent,
                )
                total_time += time.perf_counter() - start
                total_evals += result.evaluations
                if result.evaluations != BUDGET:
                    raise RuntimeError("unexpected objective evaluation count")
                ratios.append(result.best_fitness / instance.upper_bound)
            per_instance[instance.name] = float(np.mean(ratios))
        trial.set_user_attr("instance_normalized_scores", per_instance)
        trial.set_user_attr("runtime_seconds", total_time)
        trial.set_user_attr("total_evaluations", total_evals)
        return float(np.mean(list(per_instance.values())))

    started = time.perf_counter()
    study.optimize(objective, n_trials=args.trials, gc_after_trial=True)
    tuning_time = time.perf_counter() - started
    study.trials_dataframe(attrs=("number", "value", "params", "state", "duration", "user_attrs")).to_csv(
        args.output / "trials.csv", index=False
    )
    best = study.best_trial
    params = dict(best.params)
    best_wolves = int(params["n_wolves"])
    metadata = {
        "protocol": "week3_pfsp_optuna_tpe_v1",
        "objective": "mean across instances of mean(best_makespan / published_upper_bound)",
        "direction": "minimize", "sampler": "TPESampler", "sampler_seed": args.sampler_seed,
        "n_trials": args.trials, "training_seeds": args.training_seeds,
        "evaluation_seeds_reserved": list(range(30)), "evaluation_budget_per_run": BUDGET,
        "wolf_choices": WOLF_CHOICES, "best_params": params, "best_value": best.value,
        "best_iterations_derived": BUDGET // best_wolves - 1,
        "best_trial_instance_scores": best.user_attrs.get("instance_normalized_scores", {}),
        "best_trial_runtime_seconds": best.user_attrs.get("runtime_seconds"),
        "best_trial_total_evaluations": best.user_attrs.get("total_evaluations"),
        "total_tuning_runtime_seconds": tuning_time,
        "total_tuning_evaluations": args.trials * len(instances) * len(args.training_seeds) * BUDGET,
        "python": sys.version, "platform": platform.platform(),
        "numpy": np.__version__, "optuna": optuna.__version__,
        "instances": [
            {"name": item.name, "jobs": item.n_jobs, "machines": item.n_machines,
             "published_upper_bound": item.upper_bound, "sha256": sha256(path), "path": str(path)}
            for path, item in zip(args.instances, instances)
        ],
    }
    (args.output / "best_params.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from optuna.visualization.matplotlib import plot_optimization_history, plot_param_importances
    ax = plot_optimization_history(study)
    ax.figure.tight_layout()
    ax.figure.savefig(args.output / "optimization_history.png", dpi=160)
    plt.close(ax.figure)
    try:
        ax = plot_param_importances(study)
        ax.figure.tight_layout()
        ax.figure.savefig(args.output / "param_importances.png", dpi=160)
        plt.close(ax.figure)
    except (ValueError, RuntimeError) as exc:
        (args.output / "importance_plot_unavailable.txt").write_text(str(exc) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
