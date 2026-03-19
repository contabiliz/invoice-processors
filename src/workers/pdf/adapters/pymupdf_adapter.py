"""Adapter that isolates PyMuPDF (fitz) and extracts geometric edges."""

from __future__ import annotations

import logging
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from pathlib import Path
from typing import List

import fitz

from ..schemas import Edge, Vertex

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EdgeExtractionConfig:
    dedup_tolerance: float = 1.0
    orientation_threshold: float = 2.0
    full_page_ratio: float = 0.9
    vertex_tolerance: float = 1.0
    min_edge_length: float = 10.0


class PyMuPDFAdapter:
    """Extracts geometric edges from a PDF using PyMuPDF."""

    def __init__(
        self,
        path: Path | str,
        config: EdgeExtractionConfig | None = None,
    ) -> None:
        self._path = Path(path)
        self._config = config or EdgeExtractionConfig()

    def extract_edges_and_vertices(self) -> dict[int, tuple[list[Edge], list[Vertex]]]:
        """Return deduplicated edges per page (1-indexed)."""
        doc = fitz.open(self._path)
        try:
            result: dict[int, tuple[list[Edge], list[Vertex]]] = {}
            for i, page in enumerate(doc, start=1):
                drawings = page.get_drawings()
                edges = self._normalize(drawings, page.rect)
                vertices = self._compute_vertices(edges)
                result[i] = (edges, vertices)
                logger.info("Page %d: %d edges extracted.", i, len(edges))
                logger.info("Page %d: %d vertices extracted.", i, len(vertices))
            return result
        finally:
            doc.close()

    # ------------------------------------------------------------------
    # Internal: vertex computation
    # ------------------------------------------------------------------

    def _h_contains_x(self, edge: Edge, x: float) -> bool:
        return (min(edge.x0, edge.x1) - self._config.vertex_tolerance) <= x <= (max(edge.x0, edge.x1) + self._config.vertex_tolerance)

    def _v_contains_y(self, edge: Edge, y: float) -> bool:
        return (min(edge.y0, edge.y1) - self._config.vertex_tolerance) <= y <= (max(edge.y0, edge.y1) + self._config.vertex_tolerance)

    def _compute_vertices(self, edges: List[Edge]) -> List[Vertex]:
        vertex_tolerance = self._config.vertex_tolerance
        min_edge_length = self._config.min_edge_length
        h_edges = [e for e in edges if e.orientation == "h" and e.length >= min_edge_length]
        v_edges = sorted(
            (e for e in edges if e.orientation == "v" and e.length >= min_edge_length),
            key=lambda e: e.x0,
        )
        v_edges_x = [e.x0 for e in v_edges]

        vertices: list[Vertex] = []
        seen: set[tuple] = set()

        for h in h_edges:
            h_left = min(h.x0, h.x1) - vertex_tolerance
            h_right = max(h.x0, h.x1) + vertex_tolerance
            v_start = bisect_left(v_edges_x, h_left)
            v_end = bisect_right(v_edges_x, h_right)

            for v in v_edges[v_start:v_end]:
                if self._h_contains_x(h, v.x0) and self._v_contains_y(v, h.y0):
                    key = (round(v.x0 / vertex_tolerance), round(h.y0 / vertex_tolerance))
                    if key not in seen:
                        seen.add(key)
                        vertices.append(Vertex(x=v.x0, y=h.y0))

        return vertices

    # ------------------------------------------------------------------
    # Internal: normalisation pipeline
    # ------------------------------------------------------------------

    def _normalize(
        self,
        drawings: list[dict],
        page_rect: fitz.Rect,
    ) -> list[Edge]:
        seen: set[tuple] = set()
        edges: list[Edge] = []

        for drawing in drawings:
            for item in drawing["items"]:
                for edge in self._parse_item(item, page_rect):
                    key = self._dedupe_key(edge)
                    if key not in seen:
                        seen.add(key)
                        edges.append(edge)

        return edges

    def _parse_item(
        self,
        item: tuple,
        page_rect: fitz.Rect,
    ) -> list[Edge]:
        kind = item[0]
        if kind == "l":
            return self._from_line(item)
        if kind == "qu":
            return self._from_quad(item)
        if kind == "re":
            return self._from_rect(item, page_rect)
        return []

    def _classify_orientation(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
    ) -> str | None:
        threshold = self._config.orientation_threshold
        if abs(y1 - y0) < threshold:
            return "h"
        if abs(x1 - x0) < threshold:
            return "v"
        return None

    def _from_line(self, item: tuple) -> list[Edge]:
        p1, p2 = item[1], item[2]
        orientation = self._classify_orientation(p1.x, p1.y, p2.x, p2.y)
        if orientation is None:
            return []
        return [Edge(x0=p1.x, y0=p1.y, x1=p2.x, y1=p2.y, orientation=orientation)]

    def _from_quad(self, item: tuple) -> list[Edge]:
        quad = item[1]
        ul, ur, ll, lr = quad.ul, quad.ur, quad.ll, quad.lr
        segments = [
            (ul.x, ul.y, ur.x, ur.y),
            (ll.x, ll.y, lr.x, lr.y),
            (ul.x, ul.y, ll.x, ll.y),
            (ur.x, ur.y, lr.x, lr.y),
        ]
        edges: list[Edge] = []
        for x0, y0, x1, y1 in segments:
            orientation = self._classify_orientation(x0, y0, x1, y1)
            if orientation is not None:
                edges.append(Edge(x0=x0, y0=y0, x1=x1, y1=y1, orientation=orientation))
        return edges

    def _from_rect(self, item: tuple, page_rect: fitz.Rect) -> list[Edge]:
        rect = item[1]
        ratio = self._config.full_page_ratio
        if rect.width > page_rect.width * ratio and rect.height > page_rect.height * ratio:
            return []
        return [
            Edge(x0=rect.x0, y0=rect.y0, x1=rect.x1, y1=rect.y0, orientation="h"),
            Edge(x0=rect.x0, y0=rect.y1, x1=rect.x1, y1=rect.y1, orientation="h"),
            Edge(x0=rect.x0, y0=rect.y0, x1=rect.x0, y1=rect.y1, orientation="v"),
            Edge(x0=rect.x1, y0=rect.y0, x1=rect.x1, y1=rect.y1, orientation="v"),
        ]

    def _dedupe_key(self, edge: Edge) -> tuple:
        t = self._config.dedup_tolerance
        return (
            edge.orientation,
            round(edge.x0 / t),
            round(edge.y0 / t),
            round(edge.x1 / t),
            round(edge.y1 / t),
        )
