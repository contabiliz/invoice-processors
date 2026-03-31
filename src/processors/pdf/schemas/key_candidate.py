from dataclasses import dataclass

from ..enums import ExtractionMethod
from ..schemas import WordBox


@dataclass(frozen=True)
class KeyCandidate:
    key: str
    confidence: float
    method: ExtractionMethod
    bbox: WordBox
