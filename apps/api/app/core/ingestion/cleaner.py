"""Text cleaning and normalization."""
import re


def clean_text(text: str) -> str:
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse runs of blank lines to a single blank line
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove form-feed and other control chars (preserve newlines/tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Collapse horizontal whitespace runs (spaces/tabs) within a line
    text = re.sub(r"[^\S\n]+", " ", text)

    # Strip trailing whitespace from each line
    text = "\n".join(line.rstrip() for line in text.splitlines())

    return text.strip()
