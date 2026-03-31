from enum import StrEnum


class SectionId(StrEnum):
    DESTINATARIO_REMETENTE = "DESTINATARIO_REMETENTE"
    HEADER = "HEADER"
    DADOS_PRODUTOS_SERVICOS = "DADOS_PRODUTOS_SERVICOS"
    CALCULO_IMPOSTO = "CALCULO_IMPOSTO"
    INFORMACOES_ENTREGA = "INFORMACOES_ENTREGA"


class DocumentStatus(StrEnum):
    OK = "ok"
    INSUFFICIENT_DATA = "insufficient_data"


class ValueType(StrEnum):
    TEXTO = "texto"
    TEXTO_NUMERICO_44 = "texto_numerico_44"
    DATA = "data"
    CNPJ = "cnpj"
    UF = "uf"
    CPF_OU_CNPJ = "cpf_ou_cnpj"
    MOEDA_BRL = "moeda_brl"


class SearchZone(StrEnum):
    RIGHT_OF_KEY = "right_of_key"
    SAME_ROW_AFTER_COLON = "same_row_after_colon"
    BELOW_KEY = "below_key"
    WITHIN_CELL_BOUNDS = "within_cell_bounds"


class ExtractionMethod(StrEnum):
    NGRAM = "ngram"
    ALIAS = "alias"
    LINE_FALLBACK = "line_fallback"
    NOT_FOUND = "not_found"
