"""Train a classifier and save it to weights/<dataset>-<name>.pt

    python train.py fashion                      # baseline (tutorial settings)
    python train.py cifar
    python train.py fashion --params results/fashion-best-params.json --name optimized
"""
import argparse
import json
import os
import time

import torch
from torch import nn

from data import DATASETS, SEED, get_loaders
from models import BASELINE, build_model

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def make_optimizer(model, config):
    if config["optimizer"] == "adam":
        return torch.optim.Adam(model.parameters(), lr=config["lr"],
                                weight_decay=config["weight_decay"])
    return torch.optim.SGD(model.parameters(), lr=config["lr"], momentum=config["momentum"],
                           weight_decay=config["weight_decay"])


def train_one_epoch(model, loader, loss_fn, optimizer):
    model.train()
    for images, labels in loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        loss = loss_fn(model(images), labels)   # 1) forward pass + loss
        optimizer.zero_grad()                   # 2) reset old gradients
        loss.backward()                         # 3) backpropagation
        optimizer.step()                        # 4) update the weights


def evaluate(model, loader, loss_fn):
    """Return (average loss, accuracy, per-class accuracy list)."""
    model.eval()
    total_loss, correct, count = 0.0, 0, 0
    class_correct, class_count = torch.zeros(10), torch.zeros(10)
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(DEVICE), labels.to(DEVICE)
            logits = model(images)
            total_loss += loss_fn(logits, labels).item() * len(labels)
            hits = (logits.argmax(1) == labels).cpu()
            correct += hits.sum().item()
            count += len(labels)
            for c in range(10):
                mask = labels.cpu() == c
                class_correct[c] += hits[mask].sum()
                class_count[c] += mask.sum()
    per_class = (class_correct / class_count).tolist()
    return total_loss / count, correct / count, per_class


def fit(name, config, validation=False, on_epoch=None):
    """Train with the given hyperparameters. on_epoch(epoch, accuracy) is called after each epoch."""
    torch.manual_seed(SEED)
    train_loader, eval_loader = get_loaders(name, config["batch_size"], validation)
    model = build_model(name, config).to(DEVICE)
    loss_fn = nn.CrossEntropyLoss()
    optimizer = make_optimizer(model, config)

    history = []
    for epoch in range(1, config["epochs"] + 1):
        train_one_epoch(model, train_loader, loss_fn, optimizer)
        loss, accuracy, per_class = evaluate(model, eval_loader, loss_fn)
        history.append({"epoch": epoch, "loss": round(loss, 4), "accuracy": round(accuracy, 4)})
        print(f"  epoch {epoch:2d}/{config['epochs']}  loss {loss:.4f}  accuracy {accuracy:.2%}")
        if on_epoch:
            on_epoch(epoch, accuracy)
    return model, history, per_class


def run(name, config, model_name):
    """Train on the full training set, test on the test set, save weights and results."""
    print(f"Training {name}-{model_name} on {DEVICE} with {config}")
    start = time.time()
    model, history, per_class = fit(name, config)
    seconds = time.time() - start

    result = {
        "dataset": name,
        "model": model_name,
        "config": config,
        "test_accuracy": history[-1]["accuracy"],
        "per_class_accuracy": {c: round(a, 4) for c, a in zip(DATASETS[name]["classes"], per_class)},
        "history": history,
        "train_seconds": round(seconds, 1),
        "parameters": sum(p.numel() for p in model.parameters()),
    }
    os.makedirs("weights", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    torch.save({"state_dict": model.cpu().state_dict(), "config": config,
                "test_accuracy": result["test_accuracy"]},
               f"weights/{name}-{model_name}.pt")
    with open(f"results/{name}-{model_name}.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"Test accuracy: {result['test_accuracy']:.2%}  ({seconds:.0f} s)")
    print(f"Saved weights/{name}-{model_name}.pt and results/{name}-{model_name}.json")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", choices=DATASETS)
    parser.add_argument("--params", help="JSON file with hyperparameters (default: tutorial baseline)")
    parser.add_argument("--name", default="baseline")
    args = parser.parse_args()

    config = BASELINE[args.dataset]
    if args.params:
        with open(args.params) as f:
            config = json.load(f)
    run(args.dataset, config, args.name)