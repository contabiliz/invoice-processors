import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path

from invoice_models.extraction import ProcessorResult, RoutingOverride
from invoice_models.extraction.common import FieldOutput as ModelFieldOutput
from invoice_models.extraction.pdf import PdfExtractionResult, PdfLineItem

from .adapters import PdfHandle
from .enums import DocumentStatus
from .factory import create_extraction_service
from .profiles import DanfeNfe55Profile
from .profiles.base import FiscalProfile
from .schemas import FieldOutput as InternalFieldOutput
from .services.extraction import ExtractionOutput, ExtractionService
from .specs.column_specs import HEADER_TO_FIELD, normalize_header


def _to_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(value.replace(",", "."))
    except InvalidOperation:
        return None


def _map_field(f: InternalFieldOutput) -> ModelFieldOutput:
    return ModelFieldOutput(
        value=str(f.value) if f.value is not None else None,
        confidence=f.confidence,
        method=f.method,
        raw_text=f.raw_text,
        errors=list(f.errors),
    )


def _normalize_record(raw: dict[str, str | None]) -> dict[str, str | None]:
    return {
        HEADER_TO_FIELD[normalize_header(k)]: v
        for k, v in raw.items()
        if normalize_header(k) in HEADER_TO_FIELD
    }


def _map_line_items(records: list[dict[str, str | None]]) -> list[PdfLineItem]:
    return [
        PdfLineItem(
            descricao=r.get("descricao") or "",
            quantidade=_to_decimal(r.get("quantidade")),
            unidade=r.get("unidade"),
            valor_unitario=_to_decimal(r.get("valor_unitario")),
            valor_total_item=_to_decimal(r.get("valor_total_item")),
            cfop=r.get("cfop"),
            ncm=r.get("ncm"),
        )
        for r in (_normalize_record(raw) for raw in records)
    ]


def _map_output(output: ExtractionOutput) -> PdfExtractionResult:
    f = output.fields
    items = _map_line_items(output.records)
    return PdfExtractionResult(
        chave_acesso=_map_field(f["chave_acesso"]),
        cnpj_emitente=_map_field(f["cnpj_emitente"]),
        documento_destinatario=_map_field(f["documento_destinatario"]),
        nome_destinatario=_map_field(f["nome_destinatario"]),
        uf_destinatario=_map_field(f["uf_destinatario"]),
        data_emissao=_map_field(f["data_emissao"]),
        valor_total_nota=_map_field(f["valor_total_nota"]),
        numero_nota=_map_field(f["numero_nota"]),
        serie=_map_field(f["serie"]),
        items=items,
        table_confidence=1.0 if items else 0.0,
    )


def process(
    content: bytes,
    *,
    service: ExtractionService | None = None,
    profile: FiscalProfile | None = None,
) -> ProcessorResult:
    if service is None:
        service = create_extraction_service()
    if profile is None:
        profile = DanfeNfe55Profile()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        with PdfHandle(Path(tmp.name)) as pdf:
            output = service.extract_document(pdf, profile)

    if output.status == DocumentStatus.INSUFFICIENT_DATA:
        return ProcessorResult(result=None, routing_override=RoutingOverride.IMAGE)

    return ProcessorResult(result=_map_output(output))
