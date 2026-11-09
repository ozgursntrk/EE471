"""Neural networks and the training settings (hyperparameters).

The baseline settings are exactly the ones from the PyTorch tutorials:
- Fashion-MNIST: Quickstart tutorial (MLP 512-512, SGD lr=1e-3, batch 64, 5 epochs)
- CIFAR-10: "Training a Classifier" tutorial (LeNet-style CNN, SGD lr=1e-3 momentum 0.9, batch 4, 2 epochs)
"""
from torch import nn

BASELINE = {
    "fashion": {"hidden": 512, "dropout": 0.0, "optimizer": "sgd", "lr": 1e-3,
                "momentum": 0.0, "weight_decay": 0.0, "batch_size": 64, "epochs": 5},
    "cifar": {"channels": 6, "fc": 120, "dropout": 0.0, "optimizer": "sgd", "lr": 1e-3,
              "momentum": 0.9, "weight_decay": 0.0, "batch_size": 4, "epochs": 2},
}


class FashionNet(nn.Module):
    """Fully connected network from the Quickstart tutorial (28x28 grayscale -> 10 classes)."""

    def __init__(self, hidden=512, dropout=0.0):
        super().__init__()
        self.flatten = nn.Flatten()
        self.layers = nn.Sequential(
            nn.Linear(28 * 28, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, 10),
        )

    def forward(self, x):
        return self.layers(self.flatten(x))   # logits (raw scores)


class CifarNet(nn.Module):
    """CNN from the CIFAR-10 tutorial; the widths can be tuned (32x32 RGB -> 10 classes)."""

    def __init__(self, channels=6, fc=120, dropout=0.0):
        super().__init__()
        c1, c2 = channels, channels * 16 // 6          # tutorial: 6 and 16 channels
        self.features = nn.Sequential(
            nn.Conv2d(3, c1, 5), nn.ReLU(), nn.MaxPool2d(2, 2),     # 32 -> 28 -> 14
            nn.Conv2d(c1, c2, 5), nn.ReLU(), nn.MaxPool2d(2, 2),    # 14 -> 10 -> 5
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(c2 * 5 * 5, fc), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(fc, fc * 84 // 120), nn.ReLU(), nn.Dropout(dropout),   # tutorial: 120 -> 84
            nn.Linear(fc * 84 // 120, 10),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


def build_model(name, config):
    if name == "fashion":
        return FashionNet(config["hidden"], config["dropout"])
    return CifarNet(config["channels"], config["fc"], config["dropout"])