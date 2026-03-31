from dataclasses import dataclass

from ..enums import SearchZone
from ..schemas import WordBox


@dataclass(frozen=True)
class ValueCandidate:
    raw_text: str
    bbox: WordBox
    zone: SearchZone
