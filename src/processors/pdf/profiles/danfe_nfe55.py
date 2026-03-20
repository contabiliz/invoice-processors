"""Concrete extraction profile for DANFE NF-e modelo 55."""

from __future__ import annotations

from typing import List

from ..specs import TableStrategy, DEFAULT_STRATEGIES
from ..specs import END_ANCHORS, SECTION_LABELS, START_ANCHORS, SectionId
from .base import FiscalProfile, SectionRule

_SECTION_ORDER: tuple[SectionId, ...] = (
    SectionId.HEADER,
    SectionId.DESTINATARIO_REMETENTE,
    SectionId.CALCULO_IMPOSTO,
    SectionId.INFORMACOES_ENTREGA,
    SectionId.DADOS_PRODUTOS_SERVICOS,
)


class DanfeNfe55Profile(FiscalProfile):
    """Layout rules for DANFE NF-e 55."""

    @property
    def table_strategies(self) -> list[TableStrategy]:
        return DEFAULT_STRATEGIES

    @property
    def table_section_id(self) -> SectionId:
        return SectionId.DADOS_PRODUTOS_SERVICOS

    def field_overrides(self) -> dict[str, dict]:
        return {
            "cnpj_emitente": {"section_id": SectionId.HEADER},
            "nome_destinatario": {"section_id": SectionId.DESTINATARIO_REMETENTE},
            "documento_destinatario": {"section_id": SectionId.DESTINATARIO_REMETENTE},
            "valor_total_nota": {"section_id": SectionId.CALCULO_IMPOSTO},
        }

    @property
    def section_rules(self) -> List[SectionRule]:
        return [
            SectionRule(
                section_id=section_id,
                label=SECTION_LABELS[section_id],
                start_anchors=list(START_ANCHORS[section_id]),
                end_anchors=list(END_ANCHORS[section_id]),
            )
            for section_id in _SECTION_ORDER
        ]
