"""Pure data models — no logic, no imports beyond stdlib."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal

from ..specs import SectionId


@dataclass(frozen=True, slots=True)
class WordBox:
    """Immutable document atom: a word and its bounding box."""

    text: str
    x0: float
    top: float
    x1: float
    bottom: float


@dataclass(frozen=True, slots=True)
class Edge:
    """Immutable geometric edge extracted from PDF drawings."""

    x0: float
    y0: float
    x1: float
    y1: float
    orientation: Literal["h", "v"]

    @property
    def top(self) -> float:
        return min(self.y0, self.y1)

    @property
    def bottom(self) -> float:
        return max(self.y0, self.y1)

    @property
    def left(self) -> float:
        return min(self.x0, self.x1)

    @property
    def right(self) -> float:
        return max(self.x0, self.x1)

    @property
    def length(self) -> float:
        if self.orientation == "h":
            return abs(self.x1 - self.x0)
        return abs(self.y1 - self.y0)

@dataclass(frozen=True, slots=True)
class Vertex:
    """Immutable geometric vertex extracted from PDF drawings."""

    x: float
    y: float


@dataclass(frozen=True, slots=True)
class PageContext:
    """Immutable snapshot of a page's spatial data for field extraction."""
    words: List[WordBox]
    lines: List[Edge]
    vertices: List[Vertex]


@dataclass
class Section:
    """Rectangular region of a page with its filtered words."""

    section_id: SectionId
    label: str
    x0: float
    top: float
    x1: float
    bottom: float
    words: List[WordBox] = field(default_factory=list)


@dataclass
class Column:
    """Vertical strip inside a section with its filtered words."""

    label: str
    x0: float
    top: float
    x1: float
    bottom: float
    words: List[WordBox] = field(default_factory=list)


@dataclass
class Page:
    """Single page: dimensions and raw word boxes."""

    width: float
    height: float
    words: List[WordBox] = field(default_factory=list)
    lines: List[Edge] = field(default_factory=list)
    vertices: List[Vertex] = field(default_factory=list)
    page_number: int = 1


@dataclass
class Document:
    """Aggregates multiple pages."""

    pages: List[Page] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.pages) == 0