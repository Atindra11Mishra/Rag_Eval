# Production RAG Pipeline

Hybrid retrieval (BM25 + vector) · Cross-encoder reranking · RAGAS evaluation · CI quality gates

---

## Quick Start

### Backend (Python / FastAPI)

```bash
cd apps/api

# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and set OPENAI_API_KEY

# 4. Start the API server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### Frontend (Next.js)

```bash
cd apps/web

# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.local.example .env.local
# Edit .env.local if your backend runs on a different port

# 3. Start dev server
npm run dev
```

Frontend available at: http://localhost:3000

---

## Project Structure

```
apps/
  web/          Next.js frontend (TypeScript, Tailwind)
  api/          FastAPI backend (Python)
    app/
      main.py         Entry point
      config.py       Centralised settings (all tunables here)
      api/            Route handlers
      core/
        ingestion/    parse → clean → chunk → embed → index
        retrieval/    vector retriever (BM25 + RRF in Phase 2-3)
        generation/   prompt construction + LLM call
        telemetry/    latency / token / cost logging (Phase 7)
      schemas/        Pydantic request/response models
data/
  raw/          Uploaded documents
  chroma/       ChromaDB persistent index
  eval/         Benchmark datasets (Phase 5)
infra/
  github/workflows/   CI pipeline (Phase 8)
  sql/                Supabase schema (Phase 7)
docs/           Architecture, decisions, eval methodology
```

---

## Build Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Project setup & scaffolding | ✅ Done |
| 1 | Baseline vector RAG (upload → chunk → embed → retrieve → generate) | ✅ Done |
| 2 | BM25 lexical retrieval | ✅ Done |
| 3 | Hybrid retrieval with RRF | ✅ Done |
| 4 | Cross-encoder reranking (BAAI/bge-reranker-base) | ✅ Done |
| 5 | Evaluation dataset + RAGAS benchmark runner | ✅ Done |
| 6 | Tuning loop (experiment config + comparison script) | ✅ Done |
| 7 | Observability (Supabase logging, cost estimation) | ✅ Done |
| 8 | CI-gated evaluation (GitHub Actions) | ✅ Done |
| 9 | UX polish + retrieval inspector + demo readiness | ✅ Done |

---

## Configuration

All tunables live in `apps/api/app/config.py` and are overridden by `.env`.

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model for generation |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `RETRIEVAL_TOP_K` | `10` | Candidates fetched per query |
| `FINAL_TOP_K` | `4` | Chunks sent to generation |
| `CHUNK_SIZE` | `800` | Characters per chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between chunks |
