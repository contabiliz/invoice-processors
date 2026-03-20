import logging
from dataclasses import dataclass, field
from typing import Callable

from ..adapters import PdfHandle
from ..specs import TableStrategy, DEFAULT_STRATEGIES
from ..table import score_table, TableScore
from ..schemas import Section

logger = logging.getLogger(__name__)

RawTables = list[list[list[str | None]]]

@dataclass
class TableExtractionCandidate:
    strategy_name: str
    tables: RawTables | None
    score: TableScore

@dataclass
class TableExtractionResult:
    tables: RawTables | None
    strategy_name: str
    score: TableScore
    all_candidates: list[TableExtractionCandidate] = field(default_factory=list)

class TableItemsExtractor:
    def extract(
        self,
        handle: PdfHandle,
        region: Section,
        page_index: int = 0,
        strategies: list[TableStrategy] = DEFAULT_STRATEGIES,
        scorer: Callable[[RawTables | None, str], TableScore] = score_table,
    ) -> TableExtractionResult:
        """Try every strategy, score each result, return the best one."""
        ordered = sorted(strategies, key=lambda s: s.priority)

        candidates: list[TableExtractionCandidate] = []
        for strategy in ordered:
            tables = handle.parse_tables_from_region(
                region,
                page_index=page_index,
                table_settings=strategy.settings,
            )
            sc = scorer(tables, strategy.name)
            candidates.append(TableExtractionCandidate(strategy.name, tables, sc))

            logger.debug(
                "Strategy '%s': composite=%.3f (header=%.2f consistency=%.2f "
                "fill=%.2f rows=%.2f) low_confidence=%s",
                strategy.name,
                sc.composite,
                sc.header_score,
                sc.row_consistency,
                sc.fill_rate,
                sc.row_count_score,
                sc.low_confidence,
            )

        best = max(candidates, key=lambda c: c.score.composite)

        logger.info(
            "Selected strategy '%s' with composite score %.3f.",
            best.strategy_name,
            best.score.composite,
        )

        return TableExtractionResult(
            tables=best.tables,
            strategy_name=best.strategy_name,
            score=best.score,
            all_candidates=candidates,
        )