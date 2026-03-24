import logging

from ..schemas import (
    FieldSpec,
    KeyCandidate,
    PageContext,
    ValueCandidate,
    Vertex,
    WordBox,
)

logger = logging.getLogger(__name__)

_SAME_ROW_Y_DRIFT = 4.0
_MAX_H_GAP = 15.0
_BELOW_ROW_Y_DRIFT = 3.0
_VERTEX_TOL = 5.0


def _merge_boxes(words: list[WordBox], zone: str) -> ValueCandidate:
    parts: list[str] = []
    x0 = x1 = top = bottom = 0.0
    for i, w in enumerate(words):
        parts.append(w.text)
        if i == 0:
            x0, x1, top, bottom = w.x0, w.x1, w.top, w.bottom
        else:
            if w.x0 < x0:
                x0 = w.x0
            if w.x1 > x1:
                x1 = w.x1
            if w.top < top:
                top = w.top
            if w.bottom > bottom:
                bottom = w.bottom
    text = " ".join(parts)
    return ValueCandidate(
        raw_text=text,
        bbox=WordBox(text=text, x0=x0, x1=x1, top=top, bottom=bottom),
        zone=zone,
    )


def _group_by_gap(words: list[WordBox]) -> list[list[WordBox]]:
    """Split a sorted word list into groups separated by horizontal gaps."""
    if not words:
        return []
    groups, current = [], [words[0]]
    for w in words[1:]:
        if w.x0 - current[-1].x1 <= _MAX_H_GAP:
            current.append(w)
        else:
            groups.append(current)
            current = [w]
    groups.append(current)
    return groups


def _same_row_words(key: WordBox, ctx: PageContext) -> list[WordBox]:
    return sorted(
        [
            w
            for w in ctx.words
            if w.x0 >= key.x1 - 1.0 and abs(w.top - key.top) <= _SAME_ROW_Y_DRIFT
        ],
        key=lambda w: w.x0,
    )


def _find_right_of_key(key: WordBox, ctx: PageContext) -> list[ValueCandidate]:
    candidates = _same_row_words(key, ctx)
    return [_merge_boxes(g, "right_of_key") for g in _group_by_gap(candidates)]


def _find_same_row_after_colon(key: WordBox, ctx: PageContext) -> list[ValueCandidate]:
    candidates = _same_row_words(key, ctx)
    if candidates and candidates[0].text.strip() in (":", ";"):
        candidates = candidates[1:]
    return [_merge_boxes(g, "same_row_after_colon") for g in _group_by_gap(candidates)]


def _find_below_key(key: WordBox, ctx: PageContext) -> list[ValueCandidate]:
    below = [w for w in ctx.words if w.top >= key.bottom - 1.0]
    if not below:
        return []

    first_top = min(w.top for w in below)
    first_row = sorted(
        [w for w in below if abs(w.top - first_top) <= _BELOW_ROW_Y_DRIFT],
        key=lambda w: w.x0,
    )

    aligned = [w for w in first_row if w.x0 <= key.x1 and w.x1 >= key.x0]
    if not aligned:
        aligned = first_row

    return [_merge_boxes(g, "below_key") for g in _group_by_gap(aligned)]


def _find_cell_by_vertices(
    key: WordBox,
    vertices: list[Vertex],
) -> tuple[float, float, float, float] | None:
    v1_candidates = sorted(
        [
            v
            for v in vertices
            if v.x <= key.x0 + _VERTEX_TOL and v.y <= key.top + _VERTEX_TOL
        ],
        key=lambda v: (-v.y, -v.x),
    )
    for v1 in v1_candidates:
        v2_pool = [
            v
            for v in vertices
            if abs(v.y - v1.y) <= _VERTEX_TOL
            and v.x > v1.x + _VERTEX_TOL
            and v.x >= key.x1 - _VERTEX_TOL
        ]
        if not v2_pool:
            continue
        v2 = min(v2_pool, key=lambda v: v.x)

        v3_pool = [
            v
            for v in vertices
            if abs(v.x - v2.x) <= _VERTEX_TOL
            and v.y > v2.y + _VERTEX_TOL
            and v.y >= key.bottom - _VERTEX_TOL
        ]
        if not v3_pool:
            continue
        v3 = min(v3_pool, key=lambda v: v.y)

        v4_exists = any(
            abs(v.x - v1.x) <= _VERTEX_TOL and abs(v.y - v3.y) <= _VERTEX_TOL
            for v in vertices
        )
        if not v4_exists:
            continue

        return (v1.x, v1.y, v2.x, v3.y)

    return None


def _find_within_cell_bounds(key: WordBox, ctx: PageContext) -> list[ValueCandidate]:
    cell = _find_cell_by_vertices(key, ctx.vertices)
    if cell is None:
        return []

    cell_left, cell_top, cell_right, cell_bottom = cell
    cell_words = sorted(
        [
            w
            for w in ctx.words
            if w.x0 >= cell_left - 1.0
            and w.x1 <= cell_right + 1.0
            and w.top >= cell_top - 1.0
            and w.bottom <= cell_bottom + 1.0
            and abs(w.top - key.top) > _SAME_ROW_Y_DRIFT
        ],
        key=lambda w: (w.top, w.x0),
    )
    if not cell_words:
        return []

    logger.debug("Cell words: %d, %s", len(cell_words), [w.text for w in cell_words])

    candidates: list[ValueCandidate] = []
    current_row: list[WordBox] = [cell_words[0]]
    for w in cell_words[1:]:
        if abs(w.top - current_row[0].top) <= _BELOW_ROW_Y_DRIFT:
            current_row.append(w)
        else:
            for group in _group_by_gap(current_row):
                candidates.append(_merge_boxes(group, "within_cell_bounds"))
            current_row = [w]
    for group in _group_by_gap(current_row):
        candidates.append(_merge_boxes(group, "within_cell_bounds"))

    return candidates


_ZONE_HANDLERS = {
    "right_of_key": _find_right_of_key,
    "same_row_after_colon": _find_same_row_after_colon,
    "below_key": _find_below_key,
    "within_cell_bounds": _find_within_cell_bounds,
}


class ValueCandidateFinder:
    def find(
        self,
        field: FieldSpec,
        key_candidate: KeyCandidate,
        page_context: PageContext,
    ) -> list[ValueCandidate]:
        seen: set[tuple] = set()
        candidates: list[ValueCandidate] = []

        for zone in field.search_zones:
            handler = _ZONE_HANDLERS.get(zone)
            if handler is None:
                logger.warning(
                    "Unknown search zone '%s' for field '%s'.", zone, field.key
                )
                continue

            for vc in handler(key_candidate.bbox, page_context):
                fingerprint = (vc.raw_text, vc.bbox.x0, vc.bbox.top)
                if fingerprint not in seen:
                    seen.add(fingerprint)
                    candidates.append(vc)

        logger.debug(
            "Field '%s': %d value candidates from key at (%.1f, %.1f).",
            field.key,
            len(candidates),
            key_candidate.bbox.x0,
            key_candidate.bbox.top,
        )
        return candidates
