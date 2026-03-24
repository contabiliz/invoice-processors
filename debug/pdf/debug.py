"""Quick local script — parse PDFs and generate debug overlays."""

import csv
import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from invoice_models.extraction.pdf import PdfExtractionResult, PdfLineItem

from processors import process

try:
    from .drawer import draw_debug_pdf
except ImportError:
    from drawer import draw_debug_pdf

DEBUG_ROOT = Path(__file__).resolve().parent.parent / "output"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class Flags:
    create_json: bool = False
    create_table_csv: bool = False
    draw_sections: bool = False
    draw_edges: bool = False
    draw_vertices: bool = False


def main(pdf_path: Path, flags: Flags) -> None:
    start_time = time.time()

    debug_dir = DEBUG_ROOT / f"pdf_{pdf_path.stem}"
    debug_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Reading PDF: %s", pdf_path)
    result = process(pdf_path.read_bytes())

    elapsed = time.time() - start_time
    logger.info("Processing time: %.2f seconds", elapsed)

    if result.is_terminal_failure:
        logger.error("Terminal failure: %s", result.terminal_reason)
        return

    if result.routing_override:
        logger.warning(
            "Routing override: %s — insufficient text, would be sent to image branch",
            result.routing_override,
        )
        return

    assert isinstance(result.result, PdfExtractionResult)
    extraction = result.result

    needs_pdf = flags.draw_sections or flags.draw_edges or flags.draw_vertices
    if needs_pdf:
        # Sections require the internal service; edges/vertices only need PdfHandle.parse()
        from processors.pdf.adapters import PdfHandle, WordExtractionConfig
        from processors.pdf.factory import create_extraction_service
        from processors.pdf.profiles import DanfeNfe55Profile

        word_config = WordExtractionConfig(
            x_tolerance=1,
            y_tolerance=2,
            keep_blank_chars=False,
            use_text_flow=False,
        )

        sections = None
        edges = None
        vertices = None

        with PdfHandle(pdf_path, word_extraction_config=word_config) as pdf:
            doc = pdf.parse()
            page = doc.pages[0]

            if flags.draw_edges:
                edges = page.lines
            if flags.draw_vertices:
                vertices = page.vertices
            if flags.draw_sections:
                service = create_extraction_service()
                output = service.extract_document(pdf, DanfeNfe55Profile())
                sections = output.sections

        logger.info("Generating debug PDF…")
        draw_debug_pdf(
            input_path=pdf_path,
            output_path=debug_dir / f"{pdf_path.stem}_debug.pdf",
            page_index=0,
            sections=sections,
            edges=edges,
            vertices=vertices,
        )

    if flags.create_table_csv:
        csv_path = debug_dir / f"{pdf_path.stem}_table.csv"
        if extraction.items:
            fieldnames = list(PdfLineItem.model_fields.keys())
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows([item.model_dump() for item in extraction.items])
            logger.info(
                "Table CSV saved to %s (%d rows)", csv_path, len(extraction.items)
            )
        else:
            logger.warning("No table records extracted — CSV not created.")

    if flags.create_json:
        fields_path = debug_dir / f"{pdf_path.stem}_fields.json"
        print(extraction.items)
        fields_json = extraction.model_dump(mode="json")
        fields_path.write_text(json.dumps(fields_json, ensure_ascii=False, indent=2))
        logger.info("Fields saved to %s", fields_path)


if __name__ == "__main__":
    try:
        pdf_path = Path(sys.argv[1])
    except IndexError:
        print(
            "Usage: python -m debug.pdf.debug <pdf_path> [--json] [--table] [--sections] [--edges] [--vertices]"
        )
        print(
            "       Run from the project root with the package installed (pip install -e .)"
        )
        sys.exit(1)

    flags = Flags(
        create_json="--json" in sys.argv,
        create_table_csv="--table" in sys.argv,
        draw_sections="--sections" in sys.argv,
        draw_edges="--edges" in sys.argv,
        draw_vertices="--vertices" in sys.argv,
    )

    main(pdf_path, flags)
