from invoice_models.extraction import ProcessorResult
from lxml import etree
from pydantic import ValidationError

from . import extractor, parser


def process(content: bytes) -> ProcessorResult:
    if not content[:100].lstrip().startswith(b"<?xml"):
        return ProcessorResult(
            result=None,
            is_terminal_failure=True,
            terminal_reason="magic byte mismatch: not an XML file",
        )

    try:
        tree = parser.parse(content)
    except etree.XMLSyntaxError as exc:
        return ProcessorResult(
            result=None,
            is_terminal_failure=True,
            terminal_reason=f"malformed XML: {exc}",
        )

    root_tag = parser.read_root_tag(tree)

    try:
        version = parser.read_version(tree)
    except ValueError:
        version = ""

    if not parser.is_supported(version, root_tag):
        return ProcessorResult(
            result=None,
            is_terminal_failure=True,
            terminal_reason=f"unsupported NF-e schema version/root: {version!r} / {root_tag!r}",
        )

    try:
        parser.validate(tree, version, root_tag)
    except etree.DocumentInvalid as exc:
        return ProcessorResult(
            result=None,
            is_terminal_failure=True,
            terminal_reason=f"XSD validation failed: {exc}",
        )

    try:
        result = extractor.extract(tree)
    except (ValueError, ValidationError) as exc:
        return ProcessorResult(
            result=None,
            is_terminal_failure=True,
            terminal_reason=f"extraction failed: {exc}",
        )

    return ProcessorResult(result=result)
