#!/usr/bin/env python
"""
Compare two or more eval run result JSON files side-by-side.

Usage:
    python scripts/benchmark_compare.py \\
        ../../data/eval/baseline_v1.json \\
        ../../data/eval/hybrid_v1.json \\
        ../../data/eval/reranked_v1.json
"""
import sys
import json
from pathlib import Path


METRICS = [
    ("mean_faithfulness", "Faithfulness"),
    ("mean_context_precision", "Context Precision"),
    ("mean_context_recall", "Context Recall"),
    ("mean_answer_relevance", "Answer Relevance"),
]


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fmt(value) -> str:
    if value is None:
        return "  N/A  "
    return f" {value:.3f} "


def main():
    if len(sys.argv) < 2:
        print("Usage: benchmark_compare.py <run1.json> [run2.json …]")
        sys.exit(1)

    runs = [load(p) for p in sys.argv[1:]]
    names = [r["run_name"] for r in runs]
    col_width = max(len(n) for n in names) + 2

    # Header
    header = f"{'Metric':<25}" + "".join(f"{n:>{col_width}}" for n in names)
    print("\n" + "=" * len(header))
    print(header)
    print("-" * len(header))

    for key, label in METRICS:
        row = f"{label:<25}"
        for run in runs:
            row += fmt(run.get(key)).rjust(col_width)
        print(row)

    print("-" * len(header))

    # Pass/fail
    row = f"{'Pass/Fail':<25}"
    for run in runs:
        pf = run.get("pass_fail", "unknown")
        short = "PASS" if pf == "pass" else ("N/A" if pf == "no_metrics" else "FAIL")
        row += short.rjust(col_width)
    print(row)
    print("=" * len(header) + "\n")

    # Delta vs first run
    if len(runs) > 1:
        print("Deltas vs first run:")
        base = runs[0]
        for run in runs[1:]:
            print(f"  {run['run_name']} vs {base['run_name']}:")
            for key, label in METRICS:
                b = base.get(key)
                r = run.get(key)
                if b is not None and r is not None:
                    delta = r - b
                    sign = "+" if delta >= 0 else ""
                    print(f"    {label:<22} {sign}{delta:+.3f}")
        print()


if __name__ == "__main__":
    main()
