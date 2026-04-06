import logging

from ..schemas import WordBox
from ..text import normalize

logger = logging.getLogger(__name__)

MAX_Y_DRIFT = 3.0
MAX_X_GAP = 20.0


# -- single-word helpers -----------------------------------------------------


def find_word_occurrences(word: str, boxes: list[WordBox]) -> list[WordBox]:
    """Return every WordBox whose text matches *word* (accent-insensitive)."""
    target = normalize(word)
    return [b for b in boxes if normalize(b.text) == target]


def log_word_occurrences(word: str, boxes: list[WordBox]) -> None:
    found = find_word_occurrences(word, boxes)
    if found:
        logger.debug("Found '%s' in %d boxes: %s", word, len(found), found)
    else:
        logger.debug("Word '%s' not found.", word)


# -- phrase helpers -----------------------------------------------------------


def _validate_phrase_window(window: list[WordBox], tokens: list[str]) -> bool:
    """Check that *window* texts match *tokens* and are spatially contiguous."""
    if len(window) != len(tokens):
        return False

    if not all(normalize(w.text) == token for w, token in zip(window, tokens, strict=True)):
        return False

    y_coords = [w.top for w in window]
    if max(y_coords) - min(y_coords) > MAX_Y_DRIFT:
        return False

    return all(nxt.x0 - curr.x1 <= MAX_X_GAP for curr, nxt in zip(window, window[1:], strict=False))


def _merge_word_boxes(window: list[WordBox]) -> WordBox:
    """Funde uma lista de WordBoxes numa única WordBox que engloba todas."""
    if not window:
        raise ValueError("Cannot merge an empty window")

    parts: list[str] = []
    x0 = x1 = top = bottom = 0.0
    for i, w in enumerate(window):
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
    return WordBox(text=" ".join(parts), x0=x0, x1=x1, top=top, bottom=bottom)


def find_phrase_line(phrases: str | list[str], boxes: list[WordBox]) -> list[WordBox]:
    """Fallback: reconstruct lines and search for phrases as dense substrings.

    Groups boxes into lines by vertical proximity, concatenates normalized text
    without spaces (dense), then searches for each phrase (also space-stripped)
    as a substring. Handles both merged words (e.g. "VALORTOTAL" as one box)
    and normally separated words uniformly.
    """
    if isinstance(phrases, str):
        phrases = [phrases]
    if not boxes:
        return []

    # Group boxes into lines sorted by (top, x0)
    sorted_boxes = sorted(boxes, key=lambda w: (w.top, w.x0))
    lines: list[list[WordBox]] = []
    current_line: list[WordBox] = []
    ref_top = sorted_boxes[0].top

    for box in sorted_boxes:
        if current_line and abs(box.top - ref_top) > MAX_Y_DRIFT:
            lines.append(current_line)
            current_line = []
            ref_top = box.top
        current_line.append(box)

    if current_line:
        lines.append(current_line)

    results: list[WordBox] = []
    for line in lines:
        # Build dense (spaceless) text and a parallel char-to-box index
        dense = ""
        char_to_box: list[int] = []
        for idx, box in enumerate(line):
            norm = normalize(box.text)
            dense += norm
            char_to_box.extend([idx] * len(norm))

        if not dense:
            continue

        for phrase in phrases:
            target = normalize(phrase).replace(" ", "")
            if not target:
                continue
            start = 0
            while (pos := dense.find(target, start)) != -1:
                end = pos + len(target)
                contributing = sorted(set(char_to_box[pos:end]))
                merged = _merge_word_boxes([line[i] for i in contributing])
                logger.debug("find_phrase_line matched '%s' -> %s", phrase, merged)
                results.append(merged)
                start = pos + 1

    return results


def find_phrase_ngram(phrases: str | list[str], boxes: list[WordBox]) -> list[WordBox]:
    """Return all WordBoxes matching any phrase in *phrases* via sliding n-gram window.

    Accepts a single phrase string or a list of alternative phrases.
    Returns all matches found across the entire boxes list.
    """
    if isinstance(phrases, str):
        phrases = [phrases]

    results = []
    for phrase in phrases:
        tokens = normalize(phrase).split()
        if not tokens:
            continue

        first, length = tokens[0], len(tokens)

        for i, box in enumerate(boxes):
            if normalize(box.text) != first:
                continue

            if i + length > len(boxes):
                break

            window = boxes[i : i + length]

            if _validate_phrase_window(window, tokens):
                merged_anchor = _merge_word_boxes(window)
                logger.debug(
                    "Found matching phrase window, merged anchor: %s", merged_anchor
                )
                results.append(merged_anchor)

    return results
