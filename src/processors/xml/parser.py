from functools import cache
from pathlib import Path
from typing import Any, cast

from lxml import etree

_SCHEMAS_DIR = Path(__file__).parent / "schemas"

# Keys are (versao, root_tag). nfeProc is the authorized form (NFe + protNFe);
# NFe is the raw NF-e without protocol — both are valid inputs.
_SUPPORTED: dict[tuple[str, str], Path] = {
    ("4.00", "NFe"): _SCHEMAS_DIR / "nfe_v4.00.xsd",
    ("4.00", "nfeProc"): _SCHEMAS_DIR / "nfeProc_v4.00.xsd",
}

# Created once at module load. Stateless and safe to reuse across invocations
# per spec 05.1.4. All four security flags are mandatory (ADR-004).
SECURE_PARSER = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    huge_tree=False,
    load_dtd=False,
)

# Shared namespace binding used by all XPath queries against NF-e documents.
NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


@cache
def _load_schema(version: str, root_tag: str) -> etree.XMLSchema:
    xsd_path = _SUPPORTED[(version, root_tag)]
    xsd_tree = etree.parse(str(xsd_path), parser=SECURE_PARSER)
    return etree.XMLSchema(xsd_tree)


def parse(content: bytes) -> etree._Element:
    return etree.fromstring(content, parser=SECURE_PARSER)


def read_root_tag(tree: etree._Element) -> str:
    """Return the local name of the root element (e.g. 'NFe' or 'nfeProc')."""
    return etree.QName(tree.tag).localname


def read_version(tree: etree._Element) -> str:
    results = cast(list[Any], tree.xpath("//nfe:infNFe/@versao", namespaces=NS))
    if not results:
        raise ValueError("versao attribute not found")
    return str(results[0])


def is_supported(version: str, root_tag: str) -> bool:
    return (version, root_tag) in _SUPPORTED


def validate(tree: etree._Element, version: str, root_tag: str) -> None:
    _load_schema(version, root_tag).assertValid(tree)
