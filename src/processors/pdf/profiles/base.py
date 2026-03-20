"""Abstract base for fiscal-document extraction profiles."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, fields, replace
from typing import List, Union

from ..specs import SectionId, TableStrategy
from ..schemas import FieldSpec, Page, Section
from ..spatial import slice_section

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SectionRule:
    """Declarative rule describing how to slice a Section from a Page."""

    section_id: SectionId
    label: str
    start_anchors: Union[str, List[str]]
    end_anchors: Union[str, List[str], None] = None


class FiscalProfile(ABC):
    """
    Interface for any fiscal-document layout.

    Sub-classes declare *what* to extract (section and column rules);
    the base class implements *how* (orchestrating slicing functions).
    """

    @property
    @abstractmethod
    def section_rules(self) -> List[SectionRule]:
        """Return the ordered list of section rules for this layout."""

    @property
    def table_strategies(self) -> list[TableStrategy] | None:
        """Override to customize extraction strategies per layout."""
        return None

    @property
    def table_section_id(self) -> SectionId | None:
        """Override to customize the section ID for table extraction."""
        return None

    def extract_sections(self, page: Page) -> dict[SectionId, Section]:
        """Slice every declared section from *page*."""
        sections: dict[SectionId, Section] = {}

        for rule in self.section_rules:
            section = slice_section(
                page,
                section_id=rule.section_id,
                label=rule.label,
                start_phrases=rule.start_anchors,
                end_phrases=rule.end_anchors,
            )
            if section is not None:
                sections[rule.section_id] = section
        return sections

    def field_overrides(self) -> dict[str, dict]:
        """Override to provide layout-specific field customizations.

        Keys are FieldSpec.key values; values are dicts of FieldSpec fields to override.
        Only labels, aliases, search_zones, and similar layout-dependent fields should be overridden here.
        """
        return {}

    def resolve_fields(self, base_specs: list[FieldSpec]) -> list[FieldSpec]:
        """Merge base field specs with layout-specific overrides from this profile."""
        overrides = self.field_overrides()
        valid_field_names = {f.name for f in fields(FieldSpec)}
        resolved = []
        for spec in base_specs:
            if spec.key in overrides:
                invalid = set(overrides[spec.key]) - valid_field_names
                if invalid:
                    raise ValueError(
                        f"Invalid override keys for '{spec.key}' in "
                        f"{self.__class__.__name__}.field_overrides(): {invalid}"
                    )
                resolved.append(replace(spec, **overrides[spec.key]))
            else:
                resolved.append(spec)
        return resolved

    def extract(self, page: Page) -> dict[SectionId, Section]:
        """Run the full extraction pipeline on a single page."""
        sections = self.extract_sections(page)
        return sections
