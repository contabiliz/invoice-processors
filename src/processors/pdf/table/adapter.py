"""Normalize raw pdfplumber tables into structured records."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _has_double_line_header(second_row: list[str | None]) -> bool:
    return any(value is None for value in second_row)


def _resolve_embedded_spans(
    headers: list[str | None], second_row: list[str | None]
) -> tuple[list[str | None], list[str | None]]:
    """Handle header cells where pdfplumber embeds sub-header text via newlines.

    When a cell like ``'ALÍQUOTAS\\nICMS IPI'`` is followed by None
    (spanning), the text after the newline contains the sub-headers for
    each spanned column.  This function distributes them so the standard
    merging pass works correctly.

    Non-spanning cells with newlines are simply flattened (newline -> space).
    """
    resolved_h: list[str | None] = list(headers)
    resolved_s: list[str | None] = list(second_row) + [None] * max(
        0, len(headers) - len(second_row)
    )

    i = 0
    while i < len(resolved_h):
        cell = resolved_h[i]

        if cell is not None and "\n" in cell:
            group, embedded = cell.split("\n", 1)
            group = group.strip()
            embedded = embedded.strip()

            span = 0
            for j in range(i + 1, len(resolved_h)):
                if resolved_h[j] is None:
                    span += 1
                else:
                    break

            if span > 0:
                words = embedded.split()
                if len(words) == span + 1:
                    for k, word in enumerate(words):
                        resolved_h[i + k] = group
                        resolved_s[i + k] = word
                    i += span + 1
                    continue
                else:
                    resolved_h[i] = f"{group} {embedded}"
            else:
                resolved_h[i] = f"{group} {embedded}"

        i += 1

    return resolved_h, resolved_s


def _merge_double_header(
    headers: list[str | None], second_row: list[str | None]
) -> list[str]:
    """Combine a double-line header into a single row.

    First resolves embedded spanning text, then merges the sub-header
    row into the main header using the spanning-group pattern.

    Example (clean spans)::

        headers:    ['VALOR', None,  None,  'ALIQUOTA', None]
        second_row: ['ICMS',  'IPI', 'IBS', 'ICMS %',  'IPI %']
        result:     ['VALOR ICMS', 'VALOR IPI', 'VALOR IBS',
                     'ALIQUOTA ICMS %', 'ALIQUOTA IPI %']

    Example (embedded spans)::

        headers:    ['ALÍQUOTAS\\nICMS IPI', None]
        second_row: [None,                   'IPI']
        result:     ['ALÍQUOTAS ICMS', 'ALÍQUOTAS IPI']
    """
    resolved_h, resolved_s = _resolve_embedded_spans(headers, second_row)

    result: list[str] = []
    current_group: str | None = None

    for i, header in enumerate(resolved_h):
        sub = resolved_s[i] if i < len(resolved_s) else None

        if header is not None:
            current_group = header.strip()

        if sub and current_group:
            result.append(f"{current_group} {sub.strip()}")
        elif header is not None:
            result.append(current_group or "")

    return result


def _normalize_row(row: list[str | None], expected_len: int) -> list[str | None]:
    """Pad or trim *row* to *expected_len* so DataFrame construction never breaks."""
    if len(row) < expected_len:
        return row + [None] * (expected_len - len(row))
    return row[:expected_len]


def parse_table(
    tables: list[list[list[str | None]]],
    *,
    debug_csv: Path | None = None,
) -> list[dict[str, str | None]]:
    """Parse raw pdfplumber tables into a flat list of dicts.

    Handles double-line headers and the multi-table layout where the
    header lives in ``tables[0]`` and data rows in ``tables[1]``.
    """
    if not tables:
        return []

    rows_table_index = 0
    rows_data_index = 1

    columns: list[str | None] = tables[0][0] if tables[0] else []
    second_row: list[str | None] = tables[0][1] if len(tables[0]) > 1 else []

    if len(tables) > 1:
        logger.warning("Layout with separation between header and content detected.")
        rows_table_index = 1
        rows_data_index = 0

    if _has_double_line_header(second_row):
        logger.info("Double line header detected. Merging headers...")
        if rows_table_index == 0:
            rows_data_index = 2
        columns = _merge_double_header(columns, second_row)

    str_columns = [(c or "").replace("\n", " ").strip() for c in columns]

    col_count = len(str_columns)
    content = [
        _normalize_row(row, col_count)
        for row in tables[rows_table_index][rows_data_index:]
    ]
    records: list[dict[str, str | None]] = [
        dict(zip(str_columns, row)) for row in content
    ]

    return records
