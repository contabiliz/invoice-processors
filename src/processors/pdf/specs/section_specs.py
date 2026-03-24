"""Canonical section specs for DANFE NF-e 55 layout."""

from typing import Final

from ..enums import SectionId

SECTION_LABELS: Final[dict[SectionId, str]] = {
    SectionId.DESTINATARIO_REMETENTE: "DESTINATÁRIO / REMETENTE",
    SectionId.HEADER: "CABEÇALHO",
    SectionId.DADOS_PRODUTOS_SERVICOS: "DADOS DOS PRODUTOS / SERVIÇOS",
    SectionId.CALCULO_IMPOSTO: "CÁLCULO DO IMPOSTO",
    SectionId.INFORMACOES_ENTREGA: "INFORMAÇÕES DA ENTREGA",
}


START_ANCHORS: Final[dict[SectionId, tuple[str, ...]]] = {
    SectionId.DESTINATARIO_REMETENTE: (
        "DESTINATÁRIO / REMETENTE",
        "DESTINATÁRIO/REMETENTE",
    ),
    SectionId.HEADER: (
        "DANFE",
        "DANFE NF-e",
        "DANFE NF-e modelo 55",
    ),
    SectionId.DADOS_PRODUTOS_SERVICOS: (
        "DADOS DO PRODUTO / SERVIÇOS",
        "DADOS DO PRODUTO / SERVIÇO",
        "DADOS DOS PRODUTOS/SERVIÇOS",
        "DADOS DO PRODUTO/SERVIÇO",
        "DADOS DOS PRODUTOS",
    ),
    SectionId.CALCULO_IMPOSTO: ("CÁLCULO DO IMPOSTO",),
    SectionId.INFORMACOES_ENTREGA: ("INFORMAÇÕES DO LOCAL DE ENTREGA",),
}


END_ANCHORS: Final[dict[SectionId, tuple[str, ...]]] = {
    SectionId.DESTINATARIO_REMETENTE: (
        "FATURA / DUPLICATA",
        "FATURA/DUPLICATA",
        "FATURA / DUPLICATAS",
        "FATURA/DUPLICATAS",
        "FATURA",
    ),
    SectionId.HEADER: START_ANCHORS[SectionId.DESTINATARIO_REMETENTE],
    SectionId.DADOS_PRODUTOS_SERVICOS: (
        "CÁLCULO DO ISSQN",
        "DADOS ADICIONAIS",
    ),
    SectionId.CALCULO_IMPOSTO: (
        "TRANSPORTADOR / VOLUMES",
        "TRANSPORTADOR/VOLUMES",
        "TRANSPORTADOR/VOLUME",
        "TRANSPORTADOR",
    ),
    SectionId.INFORMACOES_ENTREGA: START_ANCHORS[SectionId.DADOS_PRODUTOS_SERVICOS],
}
