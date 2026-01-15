import re

MIN_TAG_LENGTH = 4


def extract_tags(text):
    """
    Very simple keyword-based tag extractor.
    Deterministic and transparent by design.
    """
    words = re.findall(r"\b[a-zA-Z0-9']+\b", text.lower())

    tags = []
    for w in words:
        if len(w) >= MIN_TAG_LENGTH:
            tags.append(w)

    return list(set(tags))
