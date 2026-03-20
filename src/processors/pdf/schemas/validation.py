from dataclasses import dataclass


@dataclass(frozen=True)
class TypeValidationResult:
    ok: bool
    normalized_value: str | None
    reason: str | None
