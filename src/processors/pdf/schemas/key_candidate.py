from dataclasses import dataclass

from ..schemas import WordBox


@dataclass(frozen=True)
class KeyCandidate:
    key: str
    confidence: float
    method: str
    bbox: WordBox
