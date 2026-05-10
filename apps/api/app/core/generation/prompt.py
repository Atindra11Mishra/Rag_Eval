"""Prompt construction for grounded answer generation."""

SYSTEM_PROMPT = """You are a precise, factual assistant that answers questions strictly from the provided context.

Rules:
- Answer only using information from the CONTEXT section below.
- If the context does not contain enough information to answer, say: "I cannot find a reliable answer in the provided documents."
- Be concise and direct.
- At the end of your answer, list the source file names you used (from the context metadata).
"""


def build_prompt(query: str, chunks: list[dict]) -> list[dict]:
    """
    Build a message list for the OpenAI chat completions API.

    chunks: list of dicts with keys 'text', 'metadata', 'score'
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        file_name = chunk["metadata"].get("file_name", "unknown")
        context_parts.append(f"[{i}] Source: {file_name}\n{chunk['text']}")

    context_block = "\n\n---\n\n".join(context_parts)

    user_message = f"""CONTEXT:
{context_block}

---

QUESTION: {query}

ANSWER:"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
