"""Quick local script — parse PDFs and generate debug overlays."""

import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from workers.pdf import PdfHandle, WordExtractionConfig, DanfeNfe55Profile, create_extraction_service

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
    draw_sections: bool = False
    draw_edges: bool = False
    draw_vertices: bool = False


def main(pdf_path: Path, flags: Flags) -> None:
    start_time = time.time()

    debug_dir = DEBUG_ROOT / f"pdf_{pdf_path.stem}"
    debug_dir.mkdir(parents=True, exist_ok=True)

    word_config = WordExtractionConfig(
        x_tolerance=1,
        y_tolerance=2,
        keep_blank_chars=False,
        use_text_flow=False,
    )

    with PdfHandle(pdf_path, word_extraction_config=word_config) as pdf:
        logger.info("Reading PDF: %s", pdf_path)
        service = create_extraction_service(pdf, DanfeNfe55Profile())
        output = service.extract_document(pdf, DanfeNfe55Profile())

        edges = None
        vertices = None
        if flags.draw_edges or flags.draw_vertices:
            doc = pdf.parse()
            page = doc.pages[0]
            edges = page.lines if flags.draw_edges else None
            vertices = page.vertices if flags.draw_vertices else None

    elapsed = time.time() - start_time
    logger.info("Processing time: %.2f seconds", elapsed)

    needs_pdf = flags.draw_sections or flags.draw_edges or flags.draw_vertices
    if needs_pdf:
        logger.info("Generating debug PDF…")
        draw_debug_pdf(
            input_path=pdf_path,
            output_path=debug_dir / f"{pdf_path.stem}_debug.pdf",
            page_index=0,
            sections=output.sections if flags.draw_sections else None,
            edges=edges,
            vertices=vertices,
        )

    if flags.create_json:
        fields_path = debug_dir / f"{pdf_path.stem}_fields.json"
        fields_json = {
            key: {
                "value": fo.value,
                "confidence": fo.confidence,
                "bbox": fo.bbox,
                "page": fo.page,
                "method": fo.method,
                "raw_text": fo.raw_text,
                "errors": fo.errors,
            }
            for key, fo in output.fields.items()
        }
        fields_path.write_text(json.dumps(fields_json, ensure_ascii=False, indent=2))
        logger.info("Fields saved to %s", fields_path)


if __name__ == "__main__":
    try:
        pdf_path = Path(sys.argv[1])
    except IndexError:
        print("Usage: python -m debug.pdf.debug <pdf_path> [--json] [--sections] [--edges] [--vertices]")
        print("       Run from the project root with the package installed (pip install -e .)")
        sys.exit(1)

    flags = Flags(
        create_json="--json" in sys.argv,
        draw_sections="--sections" in sys.argv,
        draw_edges="--edges" in sys.argv,
        draw_vertices="--vertices" in sys.argv,
    )

    main(pdf_path, flags)
