"""Construction functions for slicing Sections and Columns from spatial data."""

from __future__ import annotations

import logging

from ..schemas import Page, Section
from ..specs import SectionId
from .geometry import filter_words_in_rect
from .search import find_phrase_ngram

logger = logging.getLogger(__name__)


def slice_section(
    page: Page,
    section_id: SectionId,
    label: str,
    start_phrases: str | list[str],
    end_phrases: str | list[str] = None,
) -> Section | None:
    """Slice a Section from *page* using anchor phrases for vertical bounds."""
    start_matches = find_phrase_ngram(start_phrases, page.words)
    start_anchor = min(start_matches, key=lambda w: w.top) if start_matches else None

    if not start_anchor:
        logger.warning(
            "Start anchor not found for section '%s' on page %d.",
            section_id,
            page.page_number,
        )
        return None

    top = start_anchor.bottom
    bottom = page.height

    if end_phrases:
        end_matches = find_phrase_ngram(end_phrases, page.words)
        end_anchor = min(
            (w for w in end_matches if w.top > start_anchor.bottom),
            key=lambda w: w.top,
            default=None,
        )
        if end_anchor:
            bottom = end_anchor.top
        else:
            logger.warning(
                "End anchor not found for section '%s' on page %d. Using page bottom.",
                section_id,
                page.page_number,
            )

    if top >= bottom:
        logger.warning(
            "Invalid section '%s' on page %d: start anchor is below end anchor.",
            section_id,
            page.page_number,
        )
        return None

    section = Section(
        section_id=section_id,
        label=label,
        x0=0.0,
        top=top,
        x1=page.width,
        bottom=bottom,
    )
    section.words = filter_words_in_rect(page.words, section)
    return section
