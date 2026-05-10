# Tuning Experiment Log

Record each experiment as you tune retrieval parameters. One row per run.

## Tunable Parameters

| Parameter | Config Key | Default | Notes |
|-----------|-----------|---------|-------|
| Chunk size | `CHUNK_SIZE` | 800 | Characters per chunk |
| Chunk overlap | `CHUNK_OVERLAP` | 150 | Overlap between chunks |
| Vector top-k | `RETRIEVAL_TOP_K` | 10 | Candidates from vector search |
| RRF constant | `RRF_K` | 60 | Fusion constant |
| Reranker depth | `RERANKER_CANDIDATE_DEPTH` | 20 | Candidates sent to reranker |
| Final top-n | `RERANKER_TOP_N` | 4 | Chunks in generation prompt |
| Retrieval mode | `RETRIEVAL_MODE` | hybrid | vector / bm25 / hybrid |

---

## Experiment Log

| Run Name | Mode | Chunk | Top-K | RRF-K | Rerank-N | Faithfulness | Ctx Precision | Ctx Recall | Ans Relevance | Notes |
|----------|------|-------|-------|-------|----------|-------------|--------------|-----------|--------------|-------|
| baseline_v1 | vector | 800 | 10 | — | off | TBD | TBD | TBD | TBD | Initial baseline |
| hybrid_v1 | hybrid | 800 | 10 | 60 | off | TBD | TBD | TBD | TBD | Add hybrid retrieval |
| reranked_v1 | hybrid | 800 | 10 | 60 | 4 | TBD | TBD | TBD | TBD | Add reranker |

---

## How to Run a Comparison

```bash
cd apps/api
python scripts/run_eval.py --dataset ../../data/eval/benchmark_v1.json --run-name baseline_v1
# change .env config, re-ingest if chunk size changed
python scripts/run_eval.py --dataset ../../data/eval/benchmark_v1.json --run-name hybrid_v1
python scripts/benchmark_compare.py ../../data/eval/baseline_v1.json ../../data/eval/hybrid_v1.json
```

---

## What to Change One Variable at a Time

1. Change only one config value
2. Re-ingest documents if chunk size/overlap changed
3. Run benchmark
4. Record result above
5. Understand *why* the metric moved before changing another variable
