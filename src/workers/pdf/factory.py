from .adapters import PdfHandle, WordExtractionConfig
from .profiles import FiscalProfile
from .services import (
    ExtractionService,
    KeyCandidateFinder,
    TableItemsExtractor,
    ValueCandidateFinder,
    TypeValidator,
    FieldScorer,
    ConflictResolver,
)
from .services.extraction import ExtractionOutput

def create_extraction_service(pdf: PdfHandle, profile: FiscalProfile) -> ExtractionService:
    return ExtractionService(
        key_candidate_finder=KeyCandidateFinder(),
        value_candidate_finder=ValueCandidateFinder(),
        type_validator=TypeValidator(),
        table_items_extractor=TableItemsExtractor(),
        scorer=FieldScorer(),
        conflict_resolver=ConflictResolver(),
    )