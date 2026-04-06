from ..enums import SearchZone, ValueType
from ..schemas import FieldSpec

FIELD_SPECS: list[FieldSpec] = [
    # HEADER
    FieldSpec(
        key="numero_nota",
        labels=("NUMERO DA NOTA", "NUMERO DO DOCUMENTO", "N°", "Nº"),
        aliases=("NNF", "NUMERO", "N. NF", "N DA NOTA"),
        value_type=ValueType.NUMERO_NOTA,
        min_key_conf=0.80,
        min_score=0.82,
        search_zones=(SearchZone.RIGHT_OF_KEY, SearchZone.SAME_ROW_AFTER_COLON),
    ),
    FieldSpec(
        key="chave_acesso",
        labels=("CHAVE DE ACESSO",),
        aliases=("CHAVE ACESSO", "CHAVE DA NFE", "CHAVE NFE"),
        value_type=ValueType.TEXTO_NUMERICO_44,
        min_key_conf=0.90,
        min_score=0.92,
        search_zones=(SearchZone.WITHIN_CELL_BOUNDS, SearchZone.BELOW_KEY),
    ),
    FieldSpec(
        key="data_emissao",
        labels=("DATA DE EMISSAO", "DATA EMISSAO"),
        aliases=("DATA", "DT EMISSAO", "DATA DE EMISSÃO"),
        value_type=ValueType.DATA,
        min_key_conf=0.82,
        min_score=0.84,
        search_zones=(
            SearchZone.RIGHT_OF_KEY,
            SearchZone.SAME_ROW_AFTER_COLON,
            SearchZone.BELOW_KEY,
        ),
    ),
    FieldSpec(
        key="serie",
        labels=("SÉRIE",),
        aliases=("SÉRIE:",),
        value_type=ValueType.SERIE,
        min_key_conf=0.80,
        min_score=0.82,
        search_zones=(
            SearchZone.INLINE_AFTER_COLON,
            SearchZone.RIGHT_OF_KEY,
            SearchZone.SAME_ROW_AFTER_COLON,
        ),
    ),
    # EMITENTE
    FieldSpec(
        key="cnpj_emitente",
        labels=("CNPJ DO EMITENTE", "CNPJ EMITENTE"),
        aliases=("CNPJ/CPF", "CPF/CNPJ", "CNPJ"),
        value_type=ValueType.CNPJ,
        min_key_conf=0.88,
        min_score=0.90,
        search_zones=(SearchZone.WITHIN_CELL_BOUNDS,),
    ),
    # DESTINATARIO
    FieldSpec(
        key="nome_destinatario",
        labels=("NOME / RAZAO SOCIAL", "RAZAO SOCIAL"),
        aliases=("NOME/RAZAO SOCIAL",),
        value_type=ValueType.TEXTO,
        min_key_conf=0.80,
        min_score=0.78,
        search_zones=(SearchZone.WITHIN_CELL_BOUNDS, SearchZone.BELOW_KEY),
    ),
    FieldSpec(
        key="uf_destinatario",
        labels=("UF",),
        aliases=("MUNICIPIO UF", "U.F."),
        value_type=ValueType.UF,
        min_key_conf=0.78,
        min_score=0.5,
        search_zones=(SearchZone.WITHIN_CELL_BOUNDS, SearchZone.RIGHT_OF_KEY, SearchZone.BELOW_KEY),
    ),
    FieldSpec(
        key="documento_destinatario",
        labels=("CNPJ / CPF", "CNPJ/CPF", "C.N.P.J / C.P.F.", "C.N.P.J /C.P.F."),
        aliases=("CNPJ/CPF DEST", "CPF/CNPJ DEST", "CNPJ DESTINATARIO"),
        value_type=ValueType.CPF_OU_CNPJ,
        min_key_conf=0.86,
        min_score=0.88,
        search_zones=(SearchZone.WITHIN_CELL_BOUNDS, SearchZone.RIGHT_OF_KEY, SearchZone.BELOW_KEY),
    ),
    FieldSpec(
        key="valor_total_nota",
        labels=("VALOR TOTAL DA NOTA",),
        aliases=("TOTAL DA NOTA", "VLR TOTAL NOTA", "VALOR TOTAL NF"),
        value_type=ValueType.MOEDA_BRL,
        min_key_conf=0.85,
        min_score=0.87,
        search_zones=(SearchZone.WITHIN_CELL_BOUNDS,),
    ),
]
