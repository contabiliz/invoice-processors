from dataclasses import dataclass, field

from ..enums import ExtractionMethod


@dataclass(frozen=True)
class FieldOutput:
    value: str | int | float | dict | list | None
    confidence: float
    bbox: dict[str, float] | None
    page: int | None
    method: ExtractionMethod
    raw_text: str | None
    errors: list[str] = field(default_factory=list)
