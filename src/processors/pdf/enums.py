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
    SERIE = "serie"
    NUMERO_NOTA = "numerto_nota"


class SearchZone(StrEnum):
    # Key and value are separate boxes on the same row, value starts where key ends.
    # Example: ["SÉRIE"] ["002"]  →  value = "002"
    RIGHT_OF_KEY = "right_of_key"

    # Key and value are separate boxes; a standalone colon/semicolon sits between them.
    # Example: ["SÉRIE"] [":"] ["002"]  →  skip ":", value = "002"
    SAME_ROW_AFTER_COLON = "same_row_after_colon"

    # Key and value are merged into a single box; a colon acts as the inline delimiter.
    # Example: ["SERIE:002"]  →  split on ":", value = "002"
    INLINE_AFTER_COLON = "inline_after_colon"

    # Value is in a separate box directly below the key, within the same column.
    # Example: ["SÉRIE"]
    #          ["002"]   →  value = "002"
    BELOW_KEY = "below_key"

    # Value is any box that falls inside the cell boundaries defined by the surrounding
    # table grid (vertices), excluding the key's own row.
    # Example: cell top-left corner + bottom-right corner → collect all enclosed words
    WITHIN_CELL_BOUNDS = "within_cell_bounds"


class ExtractionMethod(StrEnum):
    NGRAM = "ngram"
    ALIAS = "alias"
    LINE_FALLBACK = "line_fallback"
    NOT_FOUND = "not_found"
