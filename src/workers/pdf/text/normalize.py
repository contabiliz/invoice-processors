import re
import unicodedata


def normalize(text: str) -> str:
    """Strip accents, collapse whitespace, and upper-case."""
    nfkd = unicodedata.normalize("NFD", text or "")
    stripped = "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")
    collapsed = re.sub(r"\s+", " ", stripped.strip())
    return collapsed.upper()