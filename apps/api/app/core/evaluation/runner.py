"""
Evaluation runner: runs benchmark questions through the full pipeline
and computes RAGAS metrics.

Usage:
    python -m app.core.evaluation.runner --dataset data/eval/benchmark_v1.json
"""
import json
import logging
import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path

from app.config import settings
from app.core.retrieval.vector_retriever import retrieve_vector
from app.core.retrieval.bm25_retriever import retrieve_bm25
from app.core.retrieval.hybrid_retriever import retrieve_hybrid
from app.core.reranking.reranker import rerank
from app.core.generation.generator import generate_answer
from app.core.evaluation.dataset import load_dataset, EvalSample

logger = logging.getLogger(__name__)


@dataclass
class SampleResult:
    sample_id: str
    question: str
    generated_answer: str
    retrieved_contexts: list[str]
    reference_answer: str
    faithfulness: float | None = None
    context_precision: float | None = None
    context_recall: float | None = None
    answer_relevance: float | None = None


@dataclass
class EvalRunResult:
    run_name: str
    dataset_version: str
    config_snapshot: dict
    created_at: str
    samples: list[SampleResult] = field(default_factory=list)
    mean_faithfulness: float | None = None
    mean_context_precision: float | None = None
    mean_context_recall: float | None = None
    mean_answer_relevance: float | None = None
    pass_fail: str = "unknown"


def _run_pipeline(question: str) -> tuple[str, list[str]]:
    """Run the full retrieval + rerank + generate pipeline for one question."""
    mode = settings.retrieval_mode
    top_k = settings.retrieval_top_k

    if mode == "vector":
        candidates, _ = retrieve_vector(question, k=top_k)
    elif mode == "bm25":
        candidates, _ = retrieve_bm25(question, k=top_k)
    else:  # hybrid
        candidates, _ = retrieve_hybrid(question, k=top_k, rrf_k=settings.rrf_k)

    if settings.reranker_enabled and candidates:
        pool = candidates[: settings.reranker_candidate_depth]
        final_chunks, _ = rerank(question, pool, top_n=settings.reranker_top_n)
    else:
        final_chunks = candidates[: settings.final_top_k]

    gen = generate_answer(question, final_chunks)
    contexts = [c["text"] for c in final_chunks]
    return gen.answer, contexts


def _compute_ragas(samples: list[SampleResult]) -> list[SampleResult]:
    """Compute RAGAS metrics for all samples."""
    try:
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            context_precision,
            context_recall,
            answer_relevancy,
        )
        from datasets import Dataset

        data = {
            "question": [s.question for s in samples],
            "answer": [s.generated_answer for s in samples],
            "contexts": [s.retrieved_contexts for s in samples],
            "ground_truth": [s.reference_answer for s in samples],
        }
        dataset = Dataset.from_dict(data)
        result = evaluate(
            dataset,
            metrics=[faithfulness, context_precision, context_recall, answer_relevancy],
        )
        df = result.to_pandas()

        for i, sample in enumerate(samples):
            sample.faithfulness = float(df.loc[i, "faithfulness"])
            sample.context_precision = float(df.loc[i, "context_precision"])
            sample.context_recall = float(df.loc[i, "context_recall"])
            sample.answer_relevance = float(df.loc[i, "answer_relevancy"])

    except ImportError:
        logger.warning(
            "RAGAS or datasets not installed. "
            "Run: pip install ragas datasets\n"
            "Skipping metric computation — results saved without scores."
        )

    return samples


THRESHOLDS = {
    "faithfulness": 0.80,
    "context_precision": 0.80,
    "context_recall": 0.75,
    "answer_relevance": 0.78,
}


def run_eval(
    dataset_path: str,
    run_name: str | None = None,
    output_dir: str = "data/eval",
) -> EvalRunResult:
    samples_data = load_dataset(dataset_path)
    run_name = run_name or f"run_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    config_snapshot = {
        "retrieval_mode": settings.retrieval_mode,
        "retrieval_top_k": settings.retrieval_top_k,
        "final_top_k": settings.final_top_k,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "rrf_k": settings.rrf_k,
        "reranker_enabled": settings.reranker_enabled,
        "reranker_model": settings.reranker_model,
        "reranker_top_n": settings.reranker_top_n,
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
    }

    run = EvalRunResult(
        run_name=run_name,
        dataset_version=Path(dataset_path).stem,
        config_snapshot=config_snapshot,
        created_at=datetime.datetime.utcnow().isoformat(),
    )

    logger.info("Running eval: %d questions", len(samples_data))
    sample_results: list[SampleResult] = []

    for sample in samples_data:
        logger.info("Evaluating: %s", sample.question[:60])
        try:
            answer, contexts = _run_pipeline(sample.question)
        except Exception as exc:
            logger.error("Pipeline failed for %s: %s", sample.id, exc)
            answer, contexts = "", []

        sample_results.append(
            SampleResult(
                sample_id=sample.id,
                question=sample.question,
                generated_answer=answer,
                retrieved_contexts=contexts,
                reference_answer=sample.reference_answer,
            )
        )

    # Compute RAGAS metrics
    sample_results = _compute_ragas(sample_results)
    run.samples = sample_results

    # Aggregate means (only where metrics were computed)
    def _mean(attr: str) -> float | None:
        vals = [getattr(s, attr) for s in sample_results if getattr(s, attr) is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    run.mean_faithfulness = _mean("faithfulness")
    run.mean_context_precision = _mean("context_precision")
    run.mean_context_recall = _mean("context_recall")
    run.mean_answer_relevance = _mean("answer_relevance")

    # Pass/fail
    if all(v is None for v in [run.mean_faithfulness, run.mean_context_precision]):
        run.pass_fail = "no_metrics"
    else:
        failed = []
        checks = {
            "faithfulness": run.mean_faithfulness,
            "context_precision": run.mean_context_precision,
            "context_recall": run.mean_context_recall,
            "answer_relevance": run.mean_answer_relevance,
        }
        for metric, value in checks.items():
            if value is not None and value < THRESHOLDS[metric]:
                failed.append(f"{metric}={value:.3f} < {THRESHOLDS[metric]}")
        run.pass_fail = "fail: " + "; ".join(failed) if failed else "pass"

    # Persist results to Supabase (non-fatal)
    try:
        from app.core.telemetry.logger import log_eval_run
        log_eval_run(asdict(run))
    except Exception as exc:
        logger.warning("Supabase eval persistence failed (non-fatal): %s", exc)

    output_path = Path(output_dir) / f"{run_name}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(run), indent=2, default=str), encoding="utf-8"
    )
    logger.info("Eval results saved to %s", output_path)

    _print_summary(run)
    return run


def _print_summary(run: EvalRunResult) -> None:
    print(f"\n{'='*60}")
    print(f"Eval Run: {run.run_name}")
    print(f"Dataset:  {run.dataset_version}")
    print(f"Mode:     {run.config_snapshot['retrieval_mode']}")
    print(f"Questions:{len(run.samples)}")
    print(f"{'─'*60}")
    metrics = [
        ("Faithfulness", run.mean_faithfulness, THRESHOLDS["faithfulness"]),
        ("Context Precision", run.mean_context_precision, THRESHOLDS["context_precision"]),
        ("Context Recall", run.mean_context_recall, THRESHOLDS["context_recall"]),
        ("Answer Relevance", run.mean_answer_relevance, THRESHOLDS["answer_relevance"]),
    ]
    for name, value, threshold in metrics:
        if value is None:
            print(f"  {name:<20} N/A")
        else:
            status = "✓" if value >= threshold else "✗"
            print(f"  {name:<20} {value:.3f}  (threshold {threshold})  {status}")
    print(f"{'─'*60}")
    print(f"  Result: {run.pass_fail}")
    print(f"{'='*60}\n")
