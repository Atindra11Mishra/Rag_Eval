# Production RAG Pipeline

Hybrid retrieval (BM25 + vector), cross-encoder reranking, RAGAS evaluation, and CI quality gates.

## Quick Start

### Backend (Python / FastAPI)

Use Python 3.13 for the backend. The dependency set is pinned to modern
LangChain, Chroma, and RAGAS releases that allow NumPy 2.x wheels on Windows.

```bash
cd apps/api

# 1. Create and activate a virtual environment
py -3.13 -m venv .venv
.venv\Scripts\activate

# Confirm this prints Python 3.13.x
python --version

# 2. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env and set LLM_API_KEY

# 4. Start the API server
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend (Next.js)

```bash
cd apps/web
npm install
copy .env.local.example .env.local
npm run dev
```

Frontend: http://localhost:3000

## Deployment

### Backend on Render

This repo includes [apps/api/Dockerfile](apps/api/Dockerfile) and [render.yaml](render.yaml).

Required Render environment variables:

| Variable | Value |
| --- | --- |
| `LLM_API_KEY` | Groq, NVIDIA NIM, or other OpenAI-compatible API key |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` for Groq or `https://integrate.api.nvidia.com/v1` for NVIDIA NIM |
| `LLM_MODEL` | Provider model name, for example `openai/gpt-oss-120b` |
| `ALLOWED_ORIGINS` | `*` for the temporary demo setup |
| `RERANKER_ENABLED` | `false` for smaller demo instances, `true` for full reranking |

Render should expose `/health` as the health check endpoint.

### Frontend on Vercel

Deploy `apps/web` as the Vercel project root and set:

```bash
NEXT_PUBLIC_API_URL=https://your-render-backend-url
```

## Project Structure

```text
apps/
  web/          Next.js frontend (TypeScript, Tailwind)
  api/          FastAPI backend (Python)
    app/
      main.py         Entry point
      config.py       Centralized settings
      api/            Route handlers
      core/
        ingestion/    parse -> clean -> chunk -> embed -> index
        retrieval/    vector, BM25, and hybrid retrieval
        generation/   prompt construction and LLM calls
        telemetry/    latency, token, and cost logging
      schemas/        Pydantic request/response models
data/
  raw/          Uploaded documents
  chroma/       ChromaDB persistent index
  eval/         Benchmark datasets
infra/
  sql/          Supabase schema
docs/           Architecture, decisions, eval methodology
```

## Build Phases

| Phase | Description | Status |
| --- | --- | --- |
| 0 | Project setup and scaffolding | Done |
| 1 | Baseline vector RAG: upload -> chunk -> embed -> retrieve -> generate | Done |
| 2 | BM25 lexical retrieval | Done |
| 3 | Hybrid retrieval with RRF | Done |
| 4 | Cross-encoder reranking | Done |
| 5 | Evaluation dataset and RAGAS benchmark runner | Done |
| 6 | Tuning loop and comparison script | Done |
| 7 | Observability with Supabase logging and cost estimation | Done |
| 8 | CI-gated evaluation | Done |
| 9 | UX polish and retrieval inspector | Done |

## Configuration

All tunables live in `apps/api/app/config.py` and can be overridden by `.env`.

| Variable | Default | Description |
| --- | --- | --- |
| `LLM_API_KEY` | empty | API key for Groq, NVIDIA NIM, OpenAI, or another OpenAI-compatible chat provider |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Chat completion provider base URL |
| `ALLOWED_ORIGINS` | `*` | Temporary permissive CORS setting for demo deployment |
| `LLM_MODEL` | `gpt-4o-mini` | Chat model for generation |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Local/free embedding model |
| `RETRIEVAL_MODE` | `hybrid` | `vector`, `bm25`, or `hybrid` |
| `RETRIEVAL_TOP_K` | `10` | Candidates fetched per query |
| `FINAL_TOP_K` | `4` | Chunks sent to generation |
| `RERANKER_ENABLED` | `true` | Enables cross-encoder reranking |
| `CHUNK_SIZE` | `800` | Characters per chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between chunks |
