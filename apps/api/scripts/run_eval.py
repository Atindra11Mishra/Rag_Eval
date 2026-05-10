#!/usr/bin/env python
"""
CLI entry point for running the evaluation benchmark.

Usage:
    # from apps/api/
    python scripts/run_eval.py --dataset ../../data/eval/benchmark_v1.json
    python scripts/run_eval.py --dataset ../../data/eval/benchmark_v1.json --run-name baseline_v1
"""
import argparse
import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.evaluation.runner import run_eval


def main():
    parser = argparse.ArgumentParser(description="Run RAG evaluation benchmark")
    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to benchmark JSON file",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        help="Name for this eval run (default: timestamped)",
    )
    parser.add_argument(
        "--output-dir",
        default="../../data/eval",
        help="Directory to save results JSON (default: ../../data/eval)",
    )
    args = parser.parse_args()

    result = run_eval(
        dataset_path=args.dataset,
        run_name=args.run_name,
        output_dir=args.output_dir,
    )

    # Exit non-zero if thresholds not met
    if result.pass_fail.startswith("fail"):
        sys.exit(1)


if __name__ == "__main__":
    main()
