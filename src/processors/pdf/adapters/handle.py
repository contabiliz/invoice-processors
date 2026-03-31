"""Composite PDF handle — merges PdfPlumber (text/tables) and Fitz (edges)."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from ..schemas import Document, Section
from ..types import RawTables
from .pdfplumber_adapter import PdfPlumberAdapter, WordExtractionConfig
from .pymupdf_adapter import EdgeExtractionConfig, PyMuPDFAdapter

logger = logging.getLogger(__name__)


class PdfHandle:
    """Single entry-point that composes PdfPlumber and Fitz behind one interface."""

    def __init__(
        self,
        path: Path | str,
        word_extraction_config: WordExtractionConfig | None = None,
        edge_extraction_config: EdgeExtractionConfig | None = None,
    ) -> None:
        self._path = Path(path)
        self._plumber = PdfPlumberAdapter(path, word_extraction_config)
        self._pymupdf = PyMuPDFAdapter(path, edge_extraction_config)

    @property
    def path(self) -> Path:
        return self._path

    def __enter__(self) -> PdfHandle:
        self._plumber.__enter__()
        return self

    def __exit__(self, *exc: object) -> None:
        self._plumber.__exit__(*exc)

    def parse(self) -> Document:
        doc = self._plumber.parse()

        t0 = time.perf_counter()
        edges_and_vertices_by_page = self._pymupdf.extract_edges_and_vertices()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info("Fitz edge extraction: %.1f ms", elapsed_ms)

        for page in doc.pages:
            lines, vertices = edges_and_vertices_by_page.get(page.page_number, ([], []))
            page.lines = lines
            page.vertices = vertices

        return doc

    def parse_tables_from_region(
        self,
        region: Section,
        page_index: int = 0,
        table_settings: dict[str, Any] | None = None,
    ) -> RawTables | None:
        return self._plumber.parse_tables_from_region(
            region,
            page_index,
            table_settings,
        )
