"""Adapter that isolates the pdfplumber library and produces domain objects."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pdfplumber

from ..schemas import Document, Page, Section, WordBox

logger = logging.getLogger(__name__)

RawTables = list[list[list[str | None]]]

@dataclass
class WordExtractionConfig:
    x_tolerance: int = 1
    y_tolerance: int = 2
    keep_blank_chars: bool = False
    use_text_flow: bool = False

class PdfPlumberAdapter:
    """Holds a pdfplumber PDF open for the entire processing pipeline.

    Use as a context manager so the file is opened once and closed
    automatically when processing is done.
    """

    def __init__(
        self,
        path: Path | str,
        word_extraction_config: WordExtractionConfig | None = None,
    ) -> None:
        self._path: Path = Path(path)
        self._pdf: pdfplumber.PDF | None = None
        self._word_extraction_config: WordExtractionConfig = word_extraction_config or WordExtractionConfig()

    @property
    def path(self) -> Path:
        return self._path

    def __enter__(self) -> PdfPlumberAdapter:
        self._pdf = pdfplumber.open(self._path)
        return self

    def __exit__(self, *exc: object) -> None:
        if self._pdf:
            self._pdf.close()
            self._pdf = None

    def _require_open(self) -> pdfplumber.PDF:
        if self._pdf is None:
            raise RuntimeError(
                "PdfPlumberAdapter must be used as a context manager (with ... as handle:)"
            )
        return self._pdf

    def parse(self) -> Document:
        """Extract words from all pages and return domain objects."""
        pdf = self._require_open()
        pages: list[Page] = []

        for i, pdf_page in enumerate(pdf.pages, start=1):
            words: list[WordBox] = [
                WordBox(
                    text=w["text"],
                    x0=w["x0"],
                    top=w["top"],
                    x1=w["x1"],
                    bottom=w["bottom"],
                )

                for w in pdf_page.extract_words(
                    x_tolerance=self._word_extraction_config.x_tolerance,
                    y_tolerance=self._word_extraction_config.y_tolerance,
                    keep_blank_chars=self._word_extraction_config.keep_blank_chars,
                    use_text_flow=self._word_extraction_config.use_text_flow,
                )
            ]

            pages.append(
                Page(
                    width=float(pdf_page.width),
                    height=float(pdf_page.height),
                    words=words,
                    page_number=i,
                )
            )

            logger.info("Page %d: %d word boxes extracted.", i, len(words))

        return Document(pages=pages)

    def parse_tables_from_region(
        self,
        region: Section,
        page_index: int = 0,
        table_settings: dict[str, Any] | None = None,
    ) -> RawTables | None:
        """Crop *region* from a page and run ``extract_tables``.

        Uses the already-open PDF — no re-read from disk.
        """
        pdf = self._require_open()
        bbox = (region.x0, region.top, region.x1, region.bottom)
        settings = table_settings or {}

        if page_index >= len(pdf.pages):
            logger.error(
                "Page %d does not exist (total: %d).", page_index, len(pdf.pages)
            )
            return None

        cropped = pdf.pages[page_index].crop(bbox)
        tables = cropped.extract_tables(settings)

        if tables:
            logger.info(
                "Extracted %d tables from region '%s'.",
                len(tables),
                region.label,
            )

        return tables or None

