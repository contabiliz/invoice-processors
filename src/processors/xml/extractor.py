from decimal import Decimal, DecimalException
from typing import Any, cast

from invoice_models.extraction.xml import NfeLineItem, NfeXmlResult
from lxml import etree

from .parser import NS


def _to_decimal(value: str, field: str) -> Decimal:
    try:
        return Decimal(value)
    except DecimalException as exc:
        raise ValueError(f"invalid decimal value for {field!r}: {value!r}") from exc


def _xpath_list(node: etree._Element, path: str) -> list[Any]:
    return cast(list[Any], node.xpath(path, namespaces=NS))


def _node_text(node: Any) -> str:
    """Extract text from an XPath result — handles both element nodes and string/attribute values."""
    if isinstance(node, etree._Element):
        return (node.text or "").strip()
    return str(node).strip()


def _xpath_text(tree: etree._Element, path: str) -> str:
    results = _xpath_list(tree, path)
    if not results:
        raise ValueError(f"mandatory XPath field not found: {path}")
    return _node_text(results[0])


def _xpath_text_optional(tree: etree._Element, path: str) -> str | None:
    results = _xpath_list(tree, path)
    if not results:
        return None
    return _node_text(results[0]) or None


def _extract_documento_destinatario(tree: etree._Element) -> str:
    cnpj = _xpath_text_optional(tree, "//nfe:dest/nfe:CNPJ")
    if cnpj:
        return cnpj
    cpf = _xpath_text_optional(tree, "//nfe:dest/nfe:CPF")
    if cpf:
        return cpf
    raise ValueError("mandatory XPath field not found: //nfe:dest/nfe:CNPJ or nfe:CPF")


def _item_field(node: etree._Element, path: str) -> str:
    results = _xpath_list(node, path)
    if not results:
        raise ValueError(f"mandatory item field not found: {path}")
    return _node_text(results[0])


def _extract_cst_csosn(node: etree._Element) -> str:
    # CST is used by regular tax regime; CSOSN by Simples Nacional. Both live under
    # <imposto><ICMS><ICMS*> — the wildcard matches any ICMS subgroup (ICMS00, ICMS20, etc.).
    cst = _xpath_text_optional(node, "nfe:imposto/nfe:ICMS/*/nfe:CST")
    if cst:
        return cst
    csosn = _xpath_text_optional(node, "nfe:imposto/nfe:ICMS/*/nfe:CSOSN")
    if csosn:
        return csosn
    raise ValueError("mandatory item field not found: CST or CSOSN under nfe:imposto/nfe:ICMS")


def _extract_items(tree: etree._Element) -> list[NfeLineItem]:
    det_nodes = cast(list[etree._Element], _xpath_list(tree, "//nfe:det"))
    if not det_nodes:
        raise ValueError("NF-e contains no line items (//nfe:det not found)")
    items = []
    for node in det_nodes:
        numero_item_raw = _xpath_list(node, "@nItem")
        if not numero_item_raw:
            raise ValueError("mandatory item attribute @nItem not found")
        items.append(
            NfeLineItem(
                numero_item=int(numero_item_raw[0]),
                codigo_produto=_item_field(node, "nfe:prod/nfe:cProd"),
                descricao=_item_field(node, "nfe:prod/nfe:xProd"),
                quantidade=_to_decimal(_item_field(node, "nfe:prod/nfe:qCom"), "quantidade"),
                unidade=_item_field(node, "nfe:prod/nfe:uCom"),
                valor_unitario=_to_decimal(
                    _item_field(node, "nfe:prod/nfe:vUnCom"), "valor_unitario"
                ),
                valor_total_item=_to_decimal(
                    _item_field(node, "nfe:prod/nfe:vProd"), "valor_total_item"
                ),
                ncm=_item_field(node, "nfe:prod/nfe:NCM"),
                cfop=_item_field(node, "nfe:prod/nfe:CFOP"),
                cst_csosn=_extract_cst_csosn(node),
            )
        )
    return items


def extract(tree: etree._Element) -> NfeXmlResult:
    return NfeXmlResult(
        chave_acesso=_xpath_text(tree, "//nfe:infProt/nfe:chNFe"),
        cnpj_emitente=_xpath_text(tree, "//nfe:emit/nfe:CNPJ"),
        nome_emitente=_xpath_text(tree, "//nfe:emit/nfe:xNome"),
        documento_destinatario=_extract_documento_destinatario(tree),
        nome_destinatario=_xpath_text(tree, "//nfe:dest/nfe:xNome"),
        data_emissao=_xpath_text(tree, "//nfe:ide/nfe:dhEmi")[:10],  # type: ignore[arg-type]
        valor_total_nota=_to_decimal(
            _xpath_text(tree, "//nfe:total/nfe:ICMSTot/nfe:vNF"), "valor_total_nota"
        ),
        numero_nota=_xpath_text(tree, "//nfe:ide/nfe:nNF"),
        serie=_xpath_text(tree, "//nfe:ide/nfe:serie"),
        items=_extract_items(tree),
    )
