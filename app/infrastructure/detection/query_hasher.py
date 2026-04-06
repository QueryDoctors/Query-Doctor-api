import hashlib
import re


def compute_query_hash(query: str) -> str:
    """
    Normalize a SQL query and return a short SHA-256 hash.
    Normalization: strip string literals, numbers, and extra whitespace.
    """
    normalized = re.sub(r"'[^']*'", "?", query)
    normalized = re.sub(r"\b\d+\b", "?", normalized)
    normalized = " ".join(normalized.lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]
