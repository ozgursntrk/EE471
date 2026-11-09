"""Hyperparameter optimization with Optuna, then train the best model.

    python hpo.py fashion --trials 20
    python hpo.py cifar --trials 20

Every trial trains on 50k (Fashion) / 45k (CIFAR) images and is scored on a
validation split, so the test set is only used once, for the final model.
"""
import argparse
import json
import os

import optuna

from data import DATASETS
from train import fit, run


def suggest(trial, name):
    """The search space: which values Optuna may try."""
    config = {
        "optimizer": trial.suggest_categorical("optimizer", ["sgd", "adam"]),
        "lr": trial.suggest_float("lr", 1e-4, 1e-1, log=True),
        "weight_decay": trial.suggest_categorical("weight_decay", [0.0, 1e-5, 1e-4]),
        "dropout": trial.suggest_float("dropout", 0.0, 0.5, step=0.1),
    }
    config["momentum"] = (trial.suggest_float("momentum", 0.0, 0.95)
                          if config["optimizer"] == "sgd" else 0.0)
    if name == "fashion":
        config["hidden"] = trial.suggest_categorical("hidden", [128, 256, 512, 1024])
        config["batch_size"] = trial.suggest_categorical("batch_size", [32, 64, 128, 256])
        config["epochs"] = trial.suggest_categorical("epochs", [5, 10, 15])
    else:
        config["channels"] = trial.suggest_categorical("channels", [6, 16, 32, 48])
        config["fc"] = trial.suggest_categorical("fc", [120, 256, 512])
        config["batch_size"] = trial.suggest_categorical("batch_size", [16, 32, 64, 128])
        config["epochs"] = trial.suggest_categorical("epochs", [5, 10, 15, 20])
    return config


def objective(trial, name):
    config = suggest(trial, name)
    print(f"\nTrial {trial.number}: {config}")

    def on_epoch(epoch, accuracy):
        trial.report(accuracy, epoch)
        if trial.should_prune():            # clearly worse than earlier trials -> stop early
            raise optuna.TrialPruned()

    _, history, _ = fit(name, config, validation=True, on_epoch=on_epoch)
    trial.set_user_attr("config", config)
    return history[-1]["accuracy"]          # validation accuracy, Optuna maximizes it


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", choices=DATASETS)
    parser.add_argument("--trials", type=int, default=20)
    args = parser.parse_args()

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=42),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=2),
    )
    study.optimize(lambda trial: objective(trial, args.dataset), n_trials=args.trials)

    best = study.best_trial
    best_config = best.user_attrs["config"]
    print(f"\nBest validation accuracy: {best.value:.2%} (trial {best.number})")
    print(f"Best hyperparameters: {best_config}")

    os.makedirs("results", exist_ok=True)
    trials = [{"number": t.number, "state": t.state.name,
               "value": None if t.value is None else round(t.value, 4), "params": t.params}
              for t in study.trials]
    with open(f"results/{args.dataset}-hpo.json", "w") as f:
        json.dump({"best_validation_accuracy": round(best.value, 4),
                   "best_config": best_config, "trials": trials}, f, indent=2)
    with open(f"results/{args.dataset}-best-params.json", "w") as f:
        json.dump(best_config, f, indent=2)

    # Final model: best hyperparameters, full training set, evaluated on the test set
    run(args.dataset, best_config, "optimized")