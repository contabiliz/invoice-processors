from ..schemas import WordBox
from dataclasses import dataclass

@dataclass(frozen=True)
class KeyCandidate:
    key: str
    confidence: float
    method: str
    bbox: WordBox