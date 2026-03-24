from dataclasses import dataclass

from invoice_models.validators import ValidationResult

from .key_candidate import KeyCandidate
from .value_candidate import ValueCandidate


@dataclass(frozen=True)
class ScoredCandidate:
    key: KeyCandidate
    value: ValueCandidate
    type_result: ValidationResult
    score_final: float
    key_score: float
    distance_score: float
    type_score: float
    cross_field_score: float
