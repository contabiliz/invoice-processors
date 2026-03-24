"""Overlay debug annotations on a PDF via PyMuPDF (fitz)."""

import logging
from pathlib import Path

import fitz

from processors.pdf.enums import SectionId
from processors.pdf.schemas import Column, Edge, Section, Vertex, WordBox

logger = logging.getLogger(__name__)


def draw_debug_pdf(
    input_path: Path,
    output_path: Path,
    page_index: int = 0,
    sections: list[Section] | dict[SectionId, Section] | None = None,
    anchors: list[WordBox] | None = None,
    columns: list[Column] | dict[str, Column] | None = None,
    edges: list[Edge] | None = None,
    vertices: list[Vertex] | None = None,
) -> None:
    """Overlay debug annotations on a single PDF page and save the result."""
    doc = fitz.open(input_path)

    if page_index >= len(doc):
        logger.error("Page %d does not exist (total: %d).", page_index, len(doc))
        return

    page = doc[page_index]

    if sections:
        _draw_sections(page, sections)

    if anchors:
        _draw_anchors(page, anchors)

    if columns:
        _draw_columns(page, columns)

    if edges:
        _draw_edges(page, edges)

    if vertices:
        _draw_vertices(page, vertices)

    doc.save(output_path)
    logger.info("Debug PDF saved to: %s", output_path)


def _draw_sections(
    page: fitz.Page,
    sections: list[Section] | dict[SectionId, Section],
) -> None:
    items = sections.values() if isinstance(sections, dict) else sections
    for section in items:
        rect = fitz.Rect(section.x0, section.top, section.x1, section.bottom)
        page.draw_rect(rect, color=(0, 0, 1), width=1, fill=(0, 0, 1), fill_opacity=0.1)
        page.insert_text(
            (section.x1 - 200, section.top - 2),
            section.label,
            color=(0, 0, 1),
            fontsize=6,
        )


def _draw_anchors(page: fitz.Page, anchors: list[WordBox]) -> None:
    for box in anchors:
        rect = fitz.Rect(box.x0, box.top, box.x1, box.bottom)
        page.draw_rect(rect, color=(1, 0, 0), width=1.0)


def _draw_columns(
    page: fitz.Page,
    columns: list[Column] | dict[str, Column],
) -> None:
    items = columns.values() if isinstance(columns, dict) else columns
    for col in items:
        rect = fitz.Rect(col.x0, col.top, col.x1, col.bottom)
        page.draw_rect(rect, color=(0, 0.6, 0), width=1.0)
        page.insert_text(
            (col.x0, col.top - 2), col.label, color=(0, 0.6, 0), fontsize=6
        )


def _draw_edges(page: fitz.Page, edges: list[Edge]) -> None:
    for e in edges:
        color = (1, 0, 0) if e.orientation == "h" else (0, 0, 1)
        page.draw_line(
            fitz.Point(e.x0, e.y0),
            fitz.Point(e.x1, e.y1),
            color=color,
            width=1.5,
        )


def _draw_vertices(page: fitz.Page, vertices: list[Vertex]) -> None:
    for v in vertices:
        page.draw_circle(
            fitz.Point(v.x, v.y),
            radius=3,
            color=(0, 0.7, 0),
            fill=(0, 0.7, 0),
        )
