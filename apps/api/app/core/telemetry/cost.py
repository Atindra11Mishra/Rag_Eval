"""
Estimate LLM cost from token counts.

Prices are per-million tokens (USD). Update as OpenAI pricing changes.
"""

# USD per 1M tokens {model: (input_price, output_price)}
_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (5.00, 15.00),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    # text-embedding models (input only, output = 0)
    "text-embedding-3-small": (0.02, 0.0),
    "text-embedding-3-large": (0.13, 0.0),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated cost in USD. Returns 0.0 if model not in price table."""
    input_price, output_price = _PRICING.get(model, (0.0, 0.0))
    return round(
        (input_tokens / 1_000_000) * input_price
        + (output_tokens / 1_000_000) * output_price,
        8,
    )
