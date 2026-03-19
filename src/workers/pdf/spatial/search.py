import logging

from ..text import normalize
from ..schemas import WordBox

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

    if not all(normalize(w.text) == token for w, token in zip(window, tokens)):
        return False

    y_coords = [w.top for w in window]
    if max(y_coords) - min(y_coords) > MAX_Y_DRIFT:
        return False

    for curr, nxt in zip(window, window[1:]):
        if nxt.x0 - curr.x1 > MAX_X_GAP:
            return False

    return True

def _merge_word_boxes(window: list[WordBox]) -> WordBox:
    """Funde uma lista de WordBoxes numa única WordBox que engloba todas."""
    if not window:
        raise ValueError("Cannot merge an empty window")
        
    return WordBox(
        text=" ".join(w.text for w in window),
        x0=min(w.x0 for w in window),       # Pega o limite mais à esquerda
        x1=max(w.x1 for w in window),       # Pega o limite mais à direita
        top=min(w.top for w in window),     # Pega o teto mais alto
        bottom=max(w.bottom for w in window) # Pega o chão mais baixo
    )

def find_phrase_line(phrases: str | list[str], boxes: list[WordBox]) -> list[WordBox]:
    """Fallback: reconstruct lines and search for phrases as substrings. Not yet implemented."""
    return []

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
                logger.debug("Found matching phrase window, merged anchor: %s", merged_anchor)
                results.append(merged_anchor)

    return results
