"""LLM answer generation."""
import logging
import time
from dataclasses import dataclass

from openai import OpenAI

from app.config import settings
from app.core.generation.prompt import build_prompt

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


@dataclass
class GenerationResult:
    answer: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    model: str


def generate_answer(query: str, chunks: list[dict]) -> GenerationResult:
    """Generate a grounded answer from retrieved chunks."""
    messages = build_prompt(query, chunks)
    client = _get_client()

    start = time.perf_counter()
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.0,  # deterministic for reproducibility
        max_tokens=1024,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    answer = response.choices[0].message.content or ""
    usage = response.usage

    logger.info(
        "Generated answer in %.0fms | in=%d out=%d tokens",
        latency_ms,
        usage.prompt_tokens,
        usage.completion_tokens,
    )

    return GenerationResult(
        answer=answer,
        input_tokens=usage.prompt_tokens,
        output_tokens=usage.completion_tokens,
        latency_ms=round(latency_ms, 1),
        model=settings.llm_model,
    )
