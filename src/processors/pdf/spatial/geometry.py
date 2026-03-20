"""Geometric functions for filtering words in a region."""

from __future__ import annotations

from typing import Protocol
from ..schemas import WordBox


class HasRect(Protocol):
    """Any object with full rectangular boundaries."""

    x0: float
    top: float
    x1: float
    bottom: float


def filter_words_in_rect(
    words: list[WordBox],
    region: HasRect,
) -> list[WordBox]:
    """Return words whose centre falls inside *region*, sorted by (top, x0)."""
    result = []
    for word in words:
        cx = (word.x0 + word.x1) / 2
        cy = (word.top + word.bottom) / 2
        if region.x0 <= cx <= region.x1 and region.top <= cy <= region.bottom:
            result.append(word)
    result.sort(key=lambda w: (w.top, w.x0))
    return result
