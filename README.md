# Kerala Police — Agentic Retrieval-Augmented Assistant

A Agentic Retrieval-Augmented Generation (RAG) project that builds a vector knowledge base from the official Kerala Police website and exposes an AI assistant over a WebSocket API. It uses web-scraped content (stored under `data/`), creates embeddings with NVIDIA embeddings, stores vectors with Chroma, and serves an interactive streaming assistant via a FastAPI WebSocket endpoint.

## Why this project

- Turn the Kerala Police website content into a searchable knowledge base.
- Provide short, factual answers to user queries using retrieved passages (RAG).
- Designed for streaming responses over WebSocket so clients can render partial answers as they arrive.

## Key features

- Web scraping pipeline and JSON/text document output (`webscrape.py`, `runwebsocket.py`).
- Vector store persistence with Chroma (`vector_store/`).
- NVIDIA embeddings and OpenAI-like chat API integration for generation (see `backend/app.py`).
- FastAPI WebSocket server to serve streaming responses on port `8090`.
- Docker-friendly: `backend/Dockerfile` and `docker-compose.yml` provide containerized run options.

## Quick project layout

- `backend/` — FastAPI-based server, Dockerfile, `requirements.txt`, and model/vectorstore integration (`app.py`).
- `data/` — scraped content (many `.txt` files) used to build `dataset.csv` and vector DB.
- `vector_store/` — where the Chroma persistence folder will be saved.
- `webscrape.py` — scraping & LLM-based splitting/structuring script that writes JSON/text files to `data/`.
- `documentmaking.py` — utilities for building/inspecting documents (helper for dataset creation).
- `runwebsocket.py` — interactive scraping/processing helper (may be a work-in-progress).
- `docker-compose.yml` — quick compose setup for frontend + backend.

## Quickstart

Choose either Docker Compose (recommended for quick try) or local Python setup.

### Using Docker Compose

1. Make sure Docker and docker-compose are installed.
2. From project root run:

```bash
docker compose up --build
```

This builds `backend` and `frontend` and exposes the backend on port `8090`.

### Local (Python) setup

1. Create a virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install backend requirements:

```bash
pip install -r backend/requirements.txt
```

3. Create a `.env` file in `backend/` (or export env vars). Required environment variables (examples):

```text
NVIDIA_API_KEY=your_nvidia_api_key_here
# any other keys used by your integration (openai-like endpoints)
```

4. Build the dataset / vector store (summary):

- The backend expects a `dataset.csv` (see `backend/app.py`). If `vector_store/` does not exist, `app.py` will attempt to create it by reading `dataset.csv` in the working directory. The `webscrape.py` and `runwebsocket.py` scripts are helper utilities to produce structured JSON/text documents under `data/` which you can combine into `dataset.csv`.

5. Run the backend server from the `backend/` folder:

```bash
cd backend
python app.py
```

The WebSocket endpoint will listen on `ws://0.0.0.0:8090/`.

## Usage examples

Example: connect via JavaScript WebSocket client

```javascript
const ws = new WebSocket('ws://localhost:8090/');
ws.onopen = () => ws.send('How do I pay a traffic fine?');
ws.onmessage = (evt) => console.log('chunk:', evt.data);
```

Python (simple) example using `websockets`:

```python
import asyncio
import websockets

async def ask(query):
    async with websockets.connect('ws://localhost:8090/') as ws:
        await ws.send(query)
        while True:
            chunk = await ws.recv()
            if chunk == '[END]':
                break
            print(chunk, end='')

asyncio.run(ask('What are the police helpline numbers?'))
```

Note: The server streams answer chunks and sends a final sentinel `[END]` after the complete reply.

## Data and vector store

- Scraped/processed documents live in `data/` as `.txt` (JSON blobs). `backend/app.py` will read `dataset.csv` and build the Chroma collection in `vector_store/` if not already present.
- If you change scraping or documents, remove `vector_store/` to rebuild with updated content.

## Environment & secrets

- Put keys (NVIDIA API keys, other provider keys) into `backend/.env` or export them in your environment before running. `webscrape.py` and `backend/app.py` reference `NVIDIA_API_KEY`.

## Development notes

- `backend/app.py`:
  - Uses `NVIDIAEmbeddings` and an OpenAI-like client to create streaming responses.
  - On first run it will try to read `dataset.csv` and persist a Chroma collection to `vector_store/`.
  - If `vector_store/` exists, it loads it directly.

- `webscrape.py` and `runwebsocket.py` are interactive helpers to produce structured JSON documents (they use an LLM to segment/structure content). Check them before running at scale.

## Where to get help

- Open an issue in this repository for bugs or setup problems.
- See `data/` and `backend/` files for examples of the dataset format. If you add a CONTRIBUTING.md later, link it here: `docs/CONTRIBUTING.md` (recommended).

## Contribution and maintainers

- Maintainer: repository owner listed in Git history (you). Add maintainer/contact info in `MAINTAINERS.md` or `CONTRIBUTING.md` for a public project.
- Contributions: fork, open a PR, or open an issue to discuss large changes.

## Security and privacy

- The project may process personal data present on source pages; follow applicable privacy laws when hosting or sharing the dataset and vector store.
- Keep API keys and secrets out of the repo. Use `.env` and `.gitignore`.

## License

See the repository `LICENSE` file for license details.

---
