import unicodedata

# Maps canonical PdfLineItem field names → known column header aliases.
# Aliases are matched after unicode normalization (accent removal, lowercase, strip).
COLUMN_SPECS: dict[str, list[str]] = {
    "descricao": [
        "descrição dos produtos / serviços",
        "descrição do produto / serviço",
        "descrição dos produtos/serviços",
        "descrição do produto/serviço",
        "descrição",
        "descricao",
    ],
    "quantidade": ["quant.", "qtde", "quantidade", "qtd", "qtd."],
    "unidade": ["unid", "unid.", "unidade"],
    "valor_unitario": [
        "valor unitário",
        "vl. unitário",
        "valor unit.",
        "vl unitario",
        "vlr unit.",
    ],
    "valor_total_item": ["valor total", "vl. total", "vl total"],
    "cfop": ["cfop"],
    "ncm": ["ncm/sh", "ncm", "ncm sh"],
}


def normalize_header(text: str) -> str:
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .strip()
    )


# Reverse lookup: normalized alias → canonical field name.
HEADER_TO_FIELD: dict[str, str] = {
    normalize_header(alias): field
    for field, aliases in COLUMN_SPECS.items()
    for alias in aliases
}
