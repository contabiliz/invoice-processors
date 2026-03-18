from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldOutput:
    value: str | int | float | dict | list | None
    confidence: float
    bbox: dict[str, float] | None
    page: int | None
    method: str
    raw_text: str | None
    errors: list[str] = field(default_factory=list)
