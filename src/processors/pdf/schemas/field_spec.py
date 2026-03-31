from dataclasses import dataclass

from ..enums import SearchZone, SectionId, ValueType


@dataclass(frozen=True)
class FieldSpec:
    key: str
    labels: tuple[str, ...]
    aliases: tuple[str, ...]
    value_type: ValueType
    min_key_conf: float
    min_score: float
    search_zones: tuple[SearchZone, ...]
    section_id: SectionId | None = None
