"""Load and validate evaluation benchmark datasets."""
import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class EvalSample:
    id: str
    question: str
    reference_answer: str
    expected_sources: list[str]


def load_dataset(path: str | Path) -> list[EvalSample]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Benchmark dataset not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    samples = []
    for item in data.get("questions", []):
        samples.append(
            EvalSample(
                id=item.get("id", ""),
                question=item["question"],
                reference_answer=item.get("reference_answer", ""),
                expected_sources=item.get("expected_sources", []),
            )
        )
    return samples
