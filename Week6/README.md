# EE 471 – Week 6: Docker & Cog

## Folder structure

```
Week6
├── Task-1-Docker
│   ├── speech-studio        # Week 5 Task 1 (Azure speech website), containerized
│   └── voice-calculator     # Week 5 Task 2 (voice calculator), containerized
└── Task-2-Cog
    ├── docker-compose.yml   # runs the model + website together
    ├── model                # Cog model: ResNet50 cat-kind classifier
    │   ├── cog.yaml
    │   ├── run.py
    │   └── requirements.txt
    └── website              # Flask website that calls the Cog model
        ├── Dockerfile
        ├── app.py
        ├── static/
        └── templates/
```

## Requirements

- Docker Desktop (Windows 11 with the WSL 2 backend)
- WSL 2 with Ubuntu, with Docker Desktop → Settings → Resources → WSL integration → Ubuntu enabled
- [Cog](https://github.com/replicate/cog), installed inside Ubuntu:
  ```bash
  sudo curl -o /usr/local/bin/cog -L "https://github.com/replicate/cog/releases/latest/download/cog_$(uname -s)_$(uname -m)"
  sudo chmod +x /usr/local/bin/cog
  ```
- An Azure Speech key for Task 1. Copy `.env.example` (in the repository root) to `.env` and fill it in.
  The `.env` file is **not** copied into the images (`.dockerignore`), it is passed at run time with `--env-file`.

## Task 1 – Containerized speech apps

Run from the repository root (PowerShell):

```powershell
# Speech Studio  ->  http://localhost:5001
cd Week6\Task-1-Docker\speech-studio
docker build -t speech-studio .
docker run --rm --name speech-studio -p 5001:5000 --env-file ..\..\..\.env speech-studio

# Voice Calculator  ->  http://localhost:5002
cd Week6\Task-1-Docker\voice-calculator
docker build -t voice-calculator .
docker run --rm --name voice-calculator -p 5002:5000 --env-file ..\..\..\.env voice-calculator
```

Both images use `python:3.12-slim`, install the requirements in a cached layer, run as a non-root user
and start the app with gunicorn.

## Task 2 – Cat kind classifier (Cog)

The model is the pre-trained **ResNet50 (ImageNet)** from the Cog getting-started guide.
`run.py` looks at the 5 domestic cat classes of ImageNet (Tabby, Tiger cat, Persian, Siamese, Egyptian Mau)
and returns the most likely kind, the probability that the image is a cat at all, and every prediction is
logged to the terminal and to `/tmp/predictions.log` inside the container.

Run inside Ubuntu (WSL):

```bash
cd Week6/Task-2-Cog/model

# 1. test the model once (also downloads the weights into ./hub)
curl -L https://gist.githubusercontent.com/bfirsh/3c2115692682ae260932a67d93fd94a8/raw/56b19f53f7643bb6c0b822c410c366c3a6244de2/mystery.jpg -o input.jpg
cog run -i image=@input.jpg

# 2. build the model image (the weights are baked into the image)
cog build -t cat-classifier

# 3. start the model + website
cd ..
docker compose up --build
```

- Website: http://localhost:8000 → choose a cat photo → **Classify**
- Cog API: `POST http://localhost:5000/predictions`

### Live prediction logs from inside the container

```bash
docker exec -it cat-model bash
tail -f /tmp/predictions.log
```

### Postman

Cog accepts files as URLs, so a local image is sent as a base64 data URL inside JSON.
Create the request body (PowerShell, in `Week6/Task-2-Cog`, with a photo named `cat.jpg`):

```powershell
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes("$PWD\cat.jpg"))
"{""input"": {""image"": ""data:image/jpeg;base64,$b64""}}" | Set-Content -Encoding ascii postman_body.json
```

In Postman: **POST** `http://localhost:5000/predictions`, header `Content-Type: application/json`,
Body → **binary** → `postman_body.json` → **Send**. The answer contains `"status": "succeeded"` and
`"prediction": "Persian"` (for example).

### Stop everything

```bash
docker compose down
```