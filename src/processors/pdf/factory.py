from .services import (
    ConflictResolver,
    ExtractionService,
    FieldScorer,
    KeyCandidateFinder,
    TableItemsExtractor,
    TypeValidator,
    ValueCandidateFinder,
)


def create_extraction_service() -> ExtractionService:
    return ExtractionService(
        key_candidate_finder=KeyCandidateFinder(),
        value_candidate_finder=ValueCandidateFinder(),
        type_validator=TypeValidator(),
        table_items_extractor=TableItemsExtractor(),
        scorer=FieldScorer(),
        conflict_resolver=ConflictResolver(),
    )
