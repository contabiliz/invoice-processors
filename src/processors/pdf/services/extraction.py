import logging
from dataclasses import dataclass

from ..enums import DocumentStatus
from ..schemas import (
    FieldOutput,
    FieldSpec,
    ScoredCandidate,
    Page,
    PageContext,
    Section,
    WordBox,
)
from .key_candidate_finder import KeyCandidateFinder
from .value_candidate_finder import ValueCandidateFinder
from .type_validator import TypeValidator
from .table_items_extractor import TableItemsExtractor
from .field_scorer import FieldScorer
from .conflict_resolver import ConflictResolver
from ..adapters import PdfHandle
from ..profiles.base import FiscalProfile
from ..specs import FIELD_SPECS, SectionId
from ..table import parse_table

logger = logging.getLogger(__name__)


@dataclass
class ExtractionOutput:
    sections: dict[SectionId, Section]
    fields: dict[str, FieldOutput]
    records: list[dict[str, str | None]]
    status: DocumentStatus = DocumentStatus.OK


def _bbox_to_dict(bbox: WordBox) -> dict[str, float]:
    return {"x0": bbox.x0, "top": bbox.top, "x1": bbox.x1, "bottom": bbox.bottom}


def _winner_to_output(winner: ScoredCandidate, page_number: int) -> FieldOutput:
    return FieldOutput(
        value=winner.type_result.normalized_value,
        confidence=winner.score_final,
        bbox=_bbox_to_dict(winner.value.bbox),
        page=page_number,
        method=winner.key.method,
        raw_text=winner.value.raw_text,
        errors=[],
    )


def _missing_to_output(reason: str) -> FieldOutput:
    return FieldOutput(
        value=None,
        confidence=0.0,
        bbox=None,
        page=None,
        method="not_found",
        raw_text=None,
        errors=[reason],
    )


class ExtractionService:
    def __init__(
        self,
        key_candidate_finder: KeyCandidateFinder,
        value_candidate_finder: ValueCandidateFinder,
        type_validator: TypeValidator,
        table_items_extractor: TableItemsExtractor,
        scorer: FieldScorer,
        conflict_resolver: ConflictResolver,
    ):
        self.key_candidate_finder = key_candidate_finder
        self.value_candidate_finder = value_candidate_finder
        self.type_validator = type_validator
        self.table_items_extractor = table_items_extractor
        self.scorer = scorer
        self.conflict_resolver = conflict_resolver

    def _extract_field(
        self,
        field: FieldSpec,
        page_context: PageContext,
        page_number: int,
    ) -> FieldOutput:
        scored_candidates: list[ScoredCandidate] = []
        key_candidates = self.key_candidate_finder.find(field, page_context.words)
        logger.info("Field '%s': %d key candidates.", field.key, len(key_candidates))

        for key_candidate in key_candidates:
            value_candidates = self.value_candidate_finder.find(
                field, key_candidate, page_context
            )
            logger.debug(
                "Field '%s' (key %s at %.1f,%.1f): %d value candidates.",
                field.key,
                key_candidate.bbox.text,
                key_candidate.bbox.x0,
                key_candidate.bbox.top,
                len(value_candidates),
            )

            for value_candidate in value_candidates:
                type_result = self.type_validator.validate(
                    field.value_type, value_candidate.raw_text
                )
                scored = self.scorer.evaluate(
                    field, key_candidate, value_candidate, type_result
                )
                scored_candidates.append(scored)
                logger.debug(
                    "Field '%s': value='%s' score=%.3f type_ok=%s, zone='%s'.",
                    field.key,
                    value_candidate.raw_text,
                    scored.score_final,
                    type_result.ok,
                    value_candidate.zone,
                )

        winner = self.conflict_resolver.pick_best(field, scored_candidates)
        if winner:
            return _winner_to_output(winner, page_number)

        reason = (
            "no_key_found" if not key_candidates else "no_candidate_above_threshold"
        )
        return _missing_to_output(reason)

    def _extract_fields(
        self,
        fields: list[FieldSpec],
        page: Page,
        sections: dict[SectionId, Section],
    ) -> dict[str, FieldOutput]:
        full_ctx = PageContext(
            words=page.words, lines=page.lines, vertices=page.vertices
        )
        results: dict[str, FieldOutput] = {}
        for field in fields:
            if field.section_id and field.section_id in sections:
                section = sections[field.section_id]
                ctx = PageContext(
                    words=section.words, lines=page.lines, vertices=page.vertices
                )
            else:
                ctx = full_ctx
            results[field.key] = self._extract_field(field, ctx, page.page_number)

        return results

    def _extract_tables(
        self,
        pdf: PdfHandle,
        table_section: Section,
        profile: FiscalProfile,
    ) -> list[dict[str, str | None]]:
        table_output = self.table_items_extractor.extract(
            pdf,
            table_section,
            page_index=0,
            strategies=profile.table_strategies,
        )

        if not table_output.tables:
            logger.warning("No tables extracted by any strategy.")
            return []

        records = parse_table(table_output.tables)
        logger.info("Parsed %d records.", len(records))
        return records

    def extract_document(
        self, pdf: PdfHandle, profile: FiscalProfile
    ) -> ExtractionOutput:
        doc = pdf.parse()

        if doc.metadata and doc.metadata.status != DocumentStatus.OK:
            logger.warning(
                "Document skipped: status=%s (%d words across %d pages).",
                doc.metadata.status,
                doc.metadata.total_words,
                doc.metadata.total_pages,
            )
            return ExtractionOutput(
                sections={},
                fields={},
                records=[],
                status=doc.metadata.status,
            )

        first_page = doc.pages[0]

        sections = profile.extract(page=first_page)
        fields = profile.resolve_fields(FIELD_SPECS)

        field_outputs = self._extract_fields(fields, first_page, sections)

        records = self._extract_tables(
            pdf=pdf,
            table_section=sections[profile.table_section_id],
            profile=profile,
        )

        return ExtractionOutput(
            sections=sections,
            fields=field_outputs,
            records=records,
            status=DocumentStatus.OK,
        )
