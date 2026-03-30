"""Quick local script — parse NF-e XML files and dump extracted fields."""

import csv
import json
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from invoice_models.extraction.xml import NfeLineItem, NfeXmlResult

from processors.xml import process

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


def main(xml_path: Path, flags: Flags) -> None:
    start_time = time.time()

    debug_dir = DEBUG_ROOT / f"xml_{xml_path.stem}"
    debug_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Reading XML: %s", xml_path)
    result = process(xml_path.read_bytes())

    elapsed = time.time() - start_time
    logger.info("Processing time: %.2f seconds", elapsed)

    if result.is_terminal_failure:
        logger.error("Terminal failure: %s", result.terminal_reason)
        return

    assert isinstance(result.result, NfeXmlResult)
    extraction = result.result

    logger.info(
        "Extracted — emitente: %s, nota: %s/%s, items: %d",
        extraction.nome_emitente,
        extraction.numero_nota,
        extraction.serie,
        len(extraction.items),
    )

    if flags.create_table_csv:
        csv_path = debug_dir / f"{xml_path.stem}_items.csv"
        if extraction.items:
            fieldnames = list(NfeLineItem.model_fields.keys())
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows([item.model_dump() for item in extraction.items])
            logger.info("Items CSV saved to %s (%d rows)", csv_path, len(extraction.items))
        else:
            logger.warning("No line items extracted — CSV not created.")

    if flags.create_json:
        json_path = debug_dir / f"{xml_path.stem}_fields.json"
        fields_json = extraction.model_dump(mode="json")
        json_path.write_text(json.dumps(fields_json, ensure_ascii=False, indent=2))
        logger.info("Fields saved to %s", json_path)


if __name__ == "__main__":
    try:
        xml_path = Path(sys.argv[1])
    except IndexError:
        print("Usage: python -m debug.xml.debug <xml_path> [--json] [--table]")
        print("       Run from the project root with the package installed (pip install -e .)")
        sys.exit(1)

    flags = Flags(
        create_json="--json" in sys.argv,
        create_table_csv="--table" in sys.argv,
    )

    main(xml_path, flags)
