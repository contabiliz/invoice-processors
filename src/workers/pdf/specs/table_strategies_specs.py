"""Ordered catalog of pdfplumber table-extraction strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TableStrategy:
    name: str
    settings: dict[str, Any] = field(default_factory=dict)
    priority: int = 0


DEFAULT_STRATEGIES: list[TableStrategy] = [
    TableStrategy(
        name="lines_strict",
        settings={
            "vertical_strategy": "lines_strict",
            "horizontal_strategy": "lines_strict",
            "snap_tolerance": 2,
            "join_tolerance": 2,
            "intersection_tolerance": 0,
        },
        priority=0,
    ),
    TableStrategy(
        name="lines",
        settings={
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 5,
            "join_tolerance": 5,
            "intersection_tolerance": 0,
        },
        priority=1,
    ),
    TableStrategy(
        name="lines_text",
        settings={
            "vertical_strategy": "lines",
            "horizontal_strategy": "text",
            "snap_tolerance": 5,
            "join_tolerance": 5,
            "text_x_tolerance": 3,
            "text_y_tolerance": 3,
        },
        priority=2,
    ),
    TableStrategy(
        name="text",
        settings={
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "text_x_tolerance": 3,
            "text_y_tolerance": 3,
            "snap_tolerance": 5,
        },
        priority=3,
    ),
]
