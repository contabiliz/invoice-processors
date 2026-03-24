import logging
from invoice_models.validators import ValidationResult
from ..schemas import (
    FieldSpec,
    KeyCandidate,
    ValueCandidate,
    ScoredCandidate,
    WordBox,
)

logger = logging.getLogger(__name__)

# weights: (w_key, w_distance, w_type, w_cross)
_FIELD_WEIGHTS: dict[str, tuple[float, float, float, float]] = {
    "chave_acesso": (0.25, 0.10, 0.45, 0.20),
    "cnpj_emitente": (0.25, 0.10, 0.45, 0.20),
    "documento_destinatario": (0.25, 0.10, 0.45, 0.20),
    "valor_total_nota": (0.30, 0.20, 0.35, 0.15),
    "valor_total": (0.30, 0.20, 0.35, 0.15),
    "data_emissao": (0.30, 0.20, 0.35, 0.15),
    "numero_documento": (0.30, 0.20, 0.35, 0.15),
    "nome_destinatario": (0.40, 0.30, 0.20, 0.10),
    "uf_destinatario": (0.35, 0.30, 0.25, 0.10),
}
_DEFAULT_WEIGHTS = (0.30, 0.20, 0.35, 0.15)

_MAX_GAP_PT = 250.0


def _bbox_gap(key: WordBox, value: WordBox) -> float:
    """Manhattan gap distance between two bounding boxes (0 if overlapping)."""
    h_gap = max(0.0, value.x0 - key.x1, key.x0 - value.x1)
    v_gap = max(0.0, value.top - key.bottom, key.top - value.bottom)
    return h_gap + v_gap


def _distance_score(key: WordBox, value: WordBox) -> float:
    gap = _bbox_gap(key, value)
    return max(0.0, 1.0 - gap / _MAX_GAP_PT)


def _type_score(type_result: ValidationResult) -> float:
    return 1.0 if type_result.ok else 0.0


def _cross_field_score() -> float:
    # v1: neutral placeholder — cross-field validation not yet implemented
    return 1.0


class FieldScorer:
    def score(
        self,
        field: FieldSpec,
        key: KeyCandidate,
        value: ValueCandidate,
        type_result: ValidationResult,
    ) -> float:
        return self.evaluate(field, key, value, type_result).score_final

    def evaluate(
        self,
        field: FieldSpec,
        key: KeyCandidate,
        value: ValueCandidate,
        type_result: ValidationResult,
    ) -> ScoredCandidate:
        w_key, w_dist, w_type, w_cross = _FIELD_WEIGHTS.get(field.key, _DEFAULT_WEIGHTS)

        ks = key.confidence
        ds = _distance_score(key.bbox, value.bbox)
        ts = _type_score(type_result)
        cs = _cross_field_score()

        final = w_key * ks + w_dist * ds + w_type * ts + w_cross * cs

        logger.debug(
            "Field '%s': key_score=%.2f dist_score=%.2f type_score=%.2f cross=%.2f → final=%.3f",
            field.key,
            ks,
            ds,
            ts,
            cs,
            final,
        )

        return ScoredCandidate(
            key=key,
            value=value,
            type_result=type_result,
            score_final=final,
            key_score=ks,
            distance_score=ds,
            type_score=ts,
            cross_field_score=cs,
        )
