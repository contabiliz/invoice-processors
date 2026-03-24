import logging

from ..schemas import FieldSpec, ScoredCandidate

logger = logging.getLogger(__name__)


class ConflictResolver:
    def pick_best(
        self,
        field: FieldSpec,
        candidates: list[ScoredCandidate],
    ) -> ScoredCandidate | None:
        if not candidates:
            logger.info("Field '%s': no candidates to resolve.", field.key)
            return None

        above_threshold = [c for c in candidates if c.score_final >= field.min_score]

        if not above_threshold:
            best_rejected = max(candidates, key=lambda c: c.score_final)
            logger.warning(
                "Field '%s': all %d candidates below threshold %.2f (best was %.3f).",
                field.key,
                len(candidates),
                field.min_score,
                best_rejected.score_final,
            )
            return None

        winner = max(
            above_threshold,
            key=lambda c: (c.score_final, c.type_score),
        )

        logger.info(
            "Field '%s': picked candidate with score=%.3f method='%s' value='%s'.",
            field.key,
            winner.score_final,
            winner.key.method,
            winner.value.raw_text,
        )
        return winner
