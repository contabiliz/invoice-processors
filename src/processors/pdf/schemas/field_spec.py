from dataclasses import dataclass
from ..enums import SectionId


@dataclass(frozen=True)
class FieldSpec:
    key: str
    labels: list[str]
    aliases: list[str]
    value_type: str
    min_key_conf: float
    min_score: float
    search_zones: list[str]
    section_id: SectionId | None = None
