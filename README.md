# invoice-processors

Structured data extraction from Brazilian fiscal documents (NF-e modelo 55). Supports two processor branches:

- **XML** — deterministic extraction from NF-e XML files (SEFAZ schema): XSD validation + XPath field mapping, no AI.
- **PDF** — spatial extraction from DANFE PDFs: geometric edge/vertex analysis + weighted candidate scoring.

## Requirements

- Python >= 3.12
- [lxml](https://lxml.de/) — secure XML parsing and XSD validation (XML processor)
- [pdfplumber](https://github.com/jsvine/pdfplumber) — word extraction and table detection (PDF processor)
- [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) — geometric edge/vertex extraction from vector drawings (PDF processor)

## Installation

```bash
uv pip install -e .
```

## Project structure

```
├── src/processors/
│   ├── xml/                             # XML processor
│   │   ├── parser.py                    # Secure lxml parser + XSD validation
│   │   ├── extractor.py                 # XPath field extraction → NfeXmlResult
│   │   ├── process.py                   # Public API: process(bytes) → ProcessorResult
│   │   └── schemas/                     # Bundled SEFAZ XSD files (v4.00)
│   │       ├── nfe_v4.00.xsd            # Root schema for <NFe> documents
│   │       ├── nfeProc_v4.00.xsd        # Root schema for <nfeProc> documents (authorized)
│   │       └── leiauteNFe_v4.00.xsd     # Full NF-e layout definitions (included by above)
│   │
│   └── pdf/                             # PDF processor
│   ├── adapters/                     # PDF library wrappers
│   │   ├── handle.py                 # PdfHandle — single entry-point composing both adapters
│   │   ├── pdfplumber_adapter.py     # Text/word extraction, table cropping
│   │   └── pymupdf_adapter.py       # Edge/vertex extraction from drawings
│   ├── profiles/                     # Document layout definitions
│   │   ├── base.py                   # FiscalProfile — abstract base
│   │   └── danfe_nfe55.py            # DANFE NF-e 55 layout rules
│   ├── schemas/                      # Immutable data models
│   │   ├── document.py               # WordBox, Edge, Vertex, Section, Column, Page, Document
│   │   ├── field_spec.py             # FieldSpec — declarative field definitions
│   │   ├── field_output.py           # FieldOutput — extraction result per field
│   │   └── ...                       # KeyCandidate, ValueCandidate, ScoredCandidate, etc.
│   ├── services/                     # Extraction pipeline
│   │   ├── extraction.py             # ExtractionService — orchestrates the full pipeline
│   │   ├── key_candidate_finder.py
│   │   ├── value_candidate_finder.py
│   │   ├── type_validator.py         # CNPJ, CPF, moeda, data, etc.
│   │   ├── field_scorer.py           # Weighted scoring (key match, distance, type validity)
│   │   ├── conflict_resolver.py      # Picks best candidate above threshold
│   │   └── table_items_extractor.py
│   ├── spatial/                      # Geometry helpers and section slicing
│   ├── specs/                        # Declarative configuration
│   │   ├── fields_specs.py           # FIELD_SPECS — labels, aliases, value types, zones
│   │   ├── section_specs.py          # START_ANCHORS / END_ANCHORS per SectionId
│   │   └── table_strategies_specs.py
│   ├── table/                        # Table parsing and scoring
│   ├── text/                         # Normalization and validation
│   ├── enums.py                      # SectionId enum
│   └── factory.py                    # create_extraction_service() — DI wiring
│
├── debug/                            # Debug tooling (not part of the package)
│   ├── pdf/
│   │   ├── debug.py                  # CLI entry-point
│   │   └── drawer.py                 # PDF overlay rendering
│   └── output/                       # Generated debug artifacts (gitignored)
│
├── pyproject.toml
└── README.md
```

## XML processor

### Pipeline

```
bytes
  │
  ▼
Magic byte check (must start with <?xml)
  │ fail → terminal failure
  ▼
lxml.etree.fromstring() with SECURE_PARSER
  │ XMLSyntaxError → terminal failure
  ▼
Detect root element (NFe or nfeProc) + read versao attribute
  │ unsupported → terminal failure
  ▼
XSD validation (nfe_v4.00.xsd or nfeProc_v4.00.xsd)
  │ invalid → terminal failure
  ▼
XPath extraction (header fields + line items)
  │
  ▼
NfeXmlResult (Pydantic validators handle CNPJ, CPF, chave de acesso, date)
```

Both `<NFe>` (raw) and `<nfeProc>` (SEFAZ-authorized, with `<protNFe>`) are supported. All failures are terminal — no retries.

### Security

All four lxml parser flags are mandatory (ADR-004):

| Flag | Protection |
|---|---|
| `resolve_entities=False` | XXE injection |
| `no_network=True` | SSRF via external DTD/entity |
| `huge_tree=False` | XML bomb / stack exhaustion |
| `load_dtd=False` | DTD loading (NF-e has no DTDs) |

### Extracted fields

| Field | XPath |
|---|---|
| `chave_acesso` | `//nfe:infProt/nfe:chNFe` |
| `cnpj_emitente` | `//nfe:emit/nfe:CNPJ` |
| `nome_emitente` | `//nfe:emit/nfe:xNome` |
| `documento_destinatario` | `//nfe:dest/nfe:CNPJ` or `//nfe:dest/nfe:CPF` |
| `nome_destinatario` | `//nfe:dest/nfe:xNome` |
| `data_emissao` | `//nfe:ide/nfe:dhEmi` |
| `valor_total_nota` | `//nfe:total/nfe:ICMSTot/nfe:vNF` |
| `numero_nota` | `//nfe:ide/nfe:nNF` |
| `serie` | `//nfe:ide/nfe:serie` |

Line items extracted from each `<det>` element: `numero_item`, `codigo_produto`, `descricao`, `quantidade`, `unidade`, `valor_unitario`, `valor_total_item`, `ncm`, `cfop`.

### Debug tooling

```bash
python -m debug.xml.debug <xml_path> [--json] [--table]
```

| Flag | Output |
|---|---|
| `--json` | `debug/output/xml_{stem}/{stem}_fields.json` — full `NfeXmlResult` dump |
| `--table` | `debug/output/xml_{stem}/{stem}_items.csv` — one row per line item |

---

## PDF extraction pipeline

```
PDF file
  │
  ├─ PdfPlumberAdapter ──→ WordBox[] per page
  ├─ PyMuPDFAdapter ─────→ Edge[] + Vertex[] per page
  │
  ▼
PdfHandle.parse() → Document (pages with words, edges, vertices)
  │
  ▼
FiscalProfile.extract(page) → Section[] (anchor-based slicing)
  │
  ▼
Per field (from FieldSpec):
  ├─ KeyCandidateFinder  → label/alias match via n-gram phrase search
  ├─ ValueCandidateFinder → spatial zones (right_of_key, below_key, within_cell_bounds, ...)
  ├─ TypeValidator        → CNPJ, CPF, moeda_brl, data, texto_numerico_44, ...
  ├─ FieldScorer          → weighted composite score
  └─ ConflictResolver     → best candidate above min_score
  │
  ▼
Table extraction:
  ├─ Tries strategies in priority order (lines_strict → lines → lines_text → text)
  ├─ Scores each result (header quality, row consistency, fill rate)
  └─ parse_table() → list[dict] (handles double-line headers, merged spans)
  │
  ▼
ExtractionOutput { sections, fields, records }
```

## PDF debug tooling

The `debug/pdf/` directory contains a CLI tool for inspecting PDF extraction results visually. Requires the package installed in editable mode (`pip install -e .`).

### Usage

```bash
python -m debug.pdf.debug <pdf_path> [flags]
```

### Flags

| Flag           | Effect                                                      |
|----------------|-------------------------------------------------------------|
| `--json`       | Dump extracted fields to `{stem}_fields.json`               |
| `--table`      | Dump extracted table records to `{stem}_table.csv`           |
| `--sections`   | Draw section boundaries (blue filled rectangles with labels) |
| `--edges`      | Draw detected edges (red = horizontal, blue = vertical)     |
| `--vertices`   | Draw detected vertices (green circles at edge intersections) |

### Examples

```bash
# Full debug — sections, edges, vertices, JSON, and table CSV
python -m debug.pdf.debug invoices/danfe_001.pdf --sections --edges --vertices --json --table

# Only visual section boundaries
python -m debug.pdf.debug invoices/danfe_001.pdf --sections

# Only geometric overlay
python -m debug.pdf.debug invoices/danfe_001.pdf --edges --vertices
```

### Output

Artifacts are written to `debug/output/pdf_{stem}/`:

```
debug/output/pdf_1/
├── 1_debug.pdf          # Annotated PDF with requested overlays
├── 1_fields.json        # Extracted field values (when --json is used)
└── 1_table.csv          # Product/service table records (when --table is used)
```

### Debug overlay colors

| Element    | Color        |
|------------|--------------|
| Sections   | Blue (10% fill) with label text |
| Anchors    | Red outlines |
| Columns    | Green outlines with label text |
| H-edges    | Red lines    |
| V-edges    | Blue lines   |
| Vertices   | Green filled circles |

## Adding a new field

1. Add a `FieldSpec` entry to `src/processors/pdf/specs/fields_specs.py`:

```python
FieldSpec(
    key="inscricao_estadual",
    labels=["INSCRIÇÃO ESTADUAL"],
    aliases=["IE", "INSC ESTADUAL"],
    value_type="texto",
    min_key_conf=0.80,
    min_score=0.78,
    search_zones=["right_of_key", "below_key"],
)
```

2. If the field belongs to a specific section, add a `section_id` override in the profile (`profiles/danfe_nfe55.py`).

3. If the field needs a new value type, implement a validator in `text/` and register it in `TypeValidator`.

## Adding a new document profile

1. Subclass `FiscalProfile` in `profiles/`.
2. Define `section_rules` (section order, start/end anchors).
3. Define `field_overrides` to scope fields to sections.
4. Define `table_strategies` and `table_section_id`.
