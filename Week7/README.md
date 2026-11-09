# EE 471 – Week 7: Fashion-MNIST & CIFAR-10 Classifiers (PyTorch + Optuna + Cog)

| Dataset | Baseline (tutorial settings) | Optimized (Optuna) |
|---|---|---|
| Fashion-MNIST | 65.04 % | **88.94 %** |
| CIFAR-10 | 56.71 % | **74.23 %** |

One-page report: [Week7_Report.pdf](Week7_Report.pdf)

## Folder structure

```
Week7
├── classifier/                  # training + Cog model
│   ├── data.py                  # datasets, transforms, data loaders, preprocessing for uploads
│   ├── models.py                # FashionNet (Quickstart MLP), CifarNet (tutorial CNN), baseline settings
│   ├── train.py                 # training loop, test accuracy, saves weights/ and results/
│   ├── hpo.py                   # Optuna hyperparameter search, then trains the optimized model
│   ├── export_samples.py        # saves test images to samples/ (for the website and Postman)
│   ├── run.py, cog.yaml         # Cog runner (DATASET and VARIANT environment variables)
│   ├── weights/                 # 4 trained models (.pt)
│   ├── results/                 # accuracies, per-class accuracies, HPO trials (.json)
│   └── samples/                 # 20 test images per dataset
├── website/                     # Flask website: side-by-side comparison of both models
├── docker-compose.fashion.yml   # garment classifier: 2 Cog models + website
└── docker-compose.cifar.yml     # CIFAR-10 classifier: 2 Cog models + website
```

## 1. Training (optional, the trained weights are in the repo)

Windows, NVIDIA GPU (tested on an RTX 5070 Ti, CUDA 13.2):

```powershell
python -m venv C:\venvs\week7
C:\venvs\week7\Scripts\Activate.ps1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu132
pip install optuna

cd Week7\classifier
python train.py fashion                 # baseline, tutorial hyperparameters
python train.py cifar
python hpo.py fashion --trials 20       # search + optimized model
python hpo.py cifar --trials 20
python export_samples.py                # test images for the demo
```

## 2. Running with Cog and Docker

Requirements: Docker Desktop and Cog (inside WSL 2 Ubuntu on Windows).

```bash
cd Week7/classifier
cog build -t week7-classifier            # one image with all four models
cd ..

docker compose -f docker-compose.fashion.yml up --build    # garment classifier
# or
docker compose -f docker-compose.cifar.yml up --build      # CIFAR-10 classifier
```

- Website: http://localhost:8000 (upload an image, both models answer side by side)
- Cog API of the baseline model: `POST http://localhost:5001/predictions`
- Cog API of the optimized model: `POST http://localhost:5002/predictions`

The same Cog image runs twice; the environment variables `DATASET` (`fashion` / `cifar`) and
`VARIANT` (`baseline` / `optimized`) choose which weights are loaded.

### Live prediction logs inside a container

```bash
docker exec -it garment-optimized bash      # or cifar-optimized
tail -f /tmp/predictions.log
```

### Postman

Cog accepts files as URLs, so the image is sent as a base64 data URL (PowerShell, in `Week7`):

```powershell
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$PWD\classifier\samples\fashion\Ankle-boot-0.png"))
"{""input"": {""image"": ""data:image/png;base64,$b64""}}" | Set-Content -Encoding ascii postman_body.json
```

Postman: `POST http://localhost:5002/predictions`, header `Content-Type: application/json`,
Body → binary → `postman_body.json` → Send. The response contains `"prediction": "Ankle boot"`.

### Stop

```bash
docker compose -f docker-compose.fashion.yml down
```