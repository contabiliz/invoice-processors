from dataclasses import dataclass
from ..schemas import WordBox


@dataclass(frozen=True)
class ValueCandidate:
    raw_text: str
    bbox: WordBox
    zone: str
