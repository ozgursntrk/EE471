"""Datasets, transforms and data loaders for Fashion-MNIST and CIFAR-10."""
from functools import lru_cache

import torch
from PIL import Image, ImageOps
from torch.utils.data import DataLoader, TensorDataset, random_split
from torchvision import datasets, transforms

DATA_DIR = "data"
SEED = 42

FASHION_CLASSES = [
    "T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
    "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot",
]
CIFAR_CLASSES = [
    "airplane", "automobile", "bird", "cat", "deer",
    "dog", "frog", "horse", "ship", "truck",
]

# Transforms: PIL image -> normalized tensor (the same ones are used for training and inference)
FASHION_TRANSFORM = transforms.ToTensor()                       # 1 x 28 x 28, values 0..1
CIFAR_TRANSFORM = transforms.Compose([
    transforms.ToTensor(),                                      # 3 x 32 x 32, values 0..1
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),     # values -1..1
])

DATASETS = {
    "fashion": {"cls": datasets.FashionMNIST, "classes": FASHION_CLASSES,
                "transform": FASHION_TRANSFORM, "val_size": 10000},
    "cifar": {"cls": datasets.CIFAR10, "classes": CIFAR_CLASSES,
              "transform": CIFAR_TRANSFORM, "val_size": 5000},
}


@lru_cache(maxsize=None)  # load each split only once, even across many HPO trials
def load_split(name, train):
    """Download the dataset once and return all images and labels as tensors.

    The transform is applied once here (not every epoch), which makes training much faster.
    """
    info = DATASETS[name]
    dataset = info["cls"](root=DATA_DIR, train=train, download=True, transform=info["transform"])
    loader = DataLoader(dataset, batch_size=1000)
    images, labels = zip(*loader)
    return TensorDataset(torch.cat(images), torch.cat(labels))


def get_loaders(name, batch_size, validation=False):
    """Return (train_loader, eval_loader).

    validation=False: train on the full training set, evaluate on the test set.
    validation=True:  split the training set into train/validation (used by the
                      hyperparameter search, so the test set stays unseen).
    """
    train_set = load_split(name, train=True)
    if validation:
        val_size = DATASETS[name]["val_size"]
        generator = torch.Generator().manual_seed(SEED)
        train_set, eval_set = random_split(
            train_set, [len(train_set) - val_size, val_size], generator=generator
        )
    else:
        eval_set = load_split(name, train=False)

    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
    eval_loader = DataLoader(eval_set, batch_size=1000)
    return train_loader, eval_loader


# ---------- Inference: turn an uploaded photo into the format the model was trained on ----------
def square(img, fill):
    """Pad the image to a square so resizing does not stretch it."""
    side = max(img.size)
    canvas = Image.new(img.mode, (side, side), fill)
    canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    return canvas


def preprocess(name, img):
    """PIL image -> 1 x C x H x W tensor."""
    if name == "fashion":
        img = img.convert("L")
        # Fashion-MNIST garments are light on a black background.
        # Most photos have a light background, so invert them.
        border = [img.getpixel((x, y)) for x in (0, img.width - 1) for y in (0, img.height - 1)]
        if sum(border) / len(border) > 127:
            img = ImageOps.invert(img)
        img = ImageOps.autocontrast(img)                              # use the full 0..255 range
        box = img.point(lambda p: 255 if p > 40 else 0).getbbox()    # find the garment
        if box:
            img = img.crop(box)                                       # cut away the empty background
        img = square(img, 0).resize((28, 28), Image.LANCZOS)
        return FASHION_TRANSFORM(img).unsqueeze(0)

    img = img.convert("RGB")
    img = ImageOps.fit(img, (32, 32), Image.BILINEAR)  # center crop to a square, then resize
    return CIFAR_TRANSFORM(img).unsqueeze(0)