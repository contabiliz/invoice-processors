"""Structural scoring for raw pdfplumber table output.

Pure functions -- no I/O, no side effects.  Operates on the raw
list[list[list[str | None]]] that pdfplumber returns *before* any
header normalization.
"""

from __future__ import annotations

from dataclasses import dataclass

SCORE_THRESHOLD = 0.6

_MIN_COLUMNS = 3
_MAX_COLUMNS = 25

_WEIGHT_HEADER = 0.30
_WEIGHT_CONSISTENCY = 0.30
_WEIGHT_FILL = 0.25
_WEIGHT_ROW_COUNT = 0.15


@dataclass
class TableScore:
    strategy_name: str
    header_score: float
    row_consistency: float
    fill_rate: float
    row_count_score: float
    composite: float
    low_confidence: bool


_MAX_HEADER_CELL_WORDS = 6


def _header_score(first_row: list[str | None]) -> float:
    if not first_row:
        return 0.0

    col_count = len(first_row)
    if col_count < _MIN_COLUMNS or col_count > _MAX_COLUMNS:
        return 0.0

    non_null = [c for c in first_row if c is not None]
    if not non_null:
        return 0.0

    filled = coherent = 0
    for c in non_null:
        s = c.strip()
        if s:
            filled += 1
            if len(s.split()) <= _MAX_HEADER_CELL_WORDS:
                coherent += 1
    fill_ratio = filled / len(non_null)
    coherence = coherent / len(non_null)

    return fill_ratio * coherence


def _row_consistency(header_len: int, data_rows: list[list[str | None]]) -> float:
    if not data_rows or header_len == 0:
        return 0.0

    matching = sum(1 for row in data_rows if len(row) == header_len)
    return matching / len(data_rows)


def _fill_rate(data_rows: list[list[str | None]]) -> float:
    total_cells = sum(len(row) for row in data_rows)
    if total_cells == 0:
        return 0.0

    filled = sum(
        1 for row in data_rows for cell in row if cell is not None and cell.strip()
    )
    return filled / total_cells


def _row_count_score(data_rows: list[list[str | None]]) -> float:
    n = len(data_rows)
    if n == 0:
        return 0.0
    if n == 1:
        return 0.7
    return 1.0


def _flatten_tables(
    tables: list[list[list[str | None]]],
) -> tuple[list[str | None], list[list[str | None]]]:
    """Extract the header row and all data rows from pdfplumber tables.

    Handles both single-table and multi-table (header in table 0,
    data in table 1) layouts that DANFE PDFs produce.
    """
    if not tables or not tables[0]:
        return [], []

    first_row = tables[0][0]

    data_rows = [row for t in tables[1:] for row in t] if len(tables) > 1 else tables[0][1:]

    return first_row, data_rows


def score_table(
    tables: list[list[list[str | None]]] | None,
    strategy_name: str,
) -> TableScore:
    if not tables:
        return TableScore(
            strategy_name=strategy_name,
            header_score=0.0,
            row_consistency=0.0,
            fill_rate=0.0,
            row_count_score=0.0,
            composite=0.0,
            low_confidence=True,
        )

    first_row, data_rows = _flatten_tables(tables)

    h = _header_score(first_row)
    c = _row_consistency(len(first_row), data_rows)
    f = _fill_rate(data_rows)
    r = _row_count_score(data_rows)

    composite = (
        _WEIGHT_HEADER * h
        + _WEIGHT_CONSISTENCY * c
        + _WEIGHT_FILL * f
        + _WEIGHT_ROW_COUNT * r
    )

    return TableScore(
        strategy_name=strategy_name,
        header_score=h,
        row_consistency=c,
        fill_rate=f,
        row_count_score=r,
        composite=composite,
        low_confidence=composite < SCORE_THRESHOLD,
    )
