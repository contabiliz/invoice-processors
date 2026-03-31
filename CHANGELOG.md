# CHANGELOG

<!-- version list -->

## v1.2.0 (2026-03-31)

### Bug Fixes

- **table_items_extractor**: Use None sentinel for mutable default strategies arg
  ([`21309b7`](https://github.com/contabiliz/invoice-processors/commit/21309b7baad0a5270a31de29fc08fddaf4545fde))

### Features

- **enums**: Add ValueType, SearchZone, and ExtractionMethod
  ([`0b0faf9`](https://github.com/contabiliz/invoice-processors/commit/0b0faf97d151370f1d82a3bc24a3d51d0ee95263))

### Refactoring

- **adapters**: Extract RawTables to types module and fix IndexError on empty pages
  ([`7d98ca9`](https://github.com/contabiliz/invoice-processors/commit/7d98ca94c2ec3c698e66456d942b4e7b76491fcc))

- **process**: Decouple module-level singletons from process()
  ([`0861b74`](https://github.com/contabiliz/invoice-processors/commit/0861b74ed17e9de54fad62a09c8ec96217301fe5))

- **schemas**: Replace str fields with typed enums and tuples
  ([`ab7be6a`](https://github.com/contabiliz/invoice-processors/commit/ab7be6a1f2f5975d63efaa04bb7b0c52008b5d0f))

- **services**: Replace string literals with enum members
  ([`c2e93c6`](https://github.com/contabiliz/invoice-processors/commit/c2e93c6c2e7a57d6c7afbdaeb3ab09b2d0117569))


## v1.1.0 (2026-03-30)

### Chores

- **deps**: Add lxml and lxml-stubs for XML processor
  ([`d26bbe2`](https://github.com/contabiliz/invoice-processors/commit/d26bbe2fb3a62c00b5aa881ac629b2d7353874ae))

### Documentation

- Update README with XML processor pipeline, security flags, and debug usage
  ([`0a66e03`](https://github.com/contabiliz/invoice-processors/commit/0a66e0392436e8a3d43f9d2489fd07cffd05158d))

### Features

- **debug**: Add XML debug script for NF-e extraction inspection
  ([`5d72cc7`](https://github.com/contabiliz/invoice-processors/commit/5d72cc773529b8c3939d593a84328f74dbbd28d7))

- **xml**: Add NF-e XML processor with XSD validation and XPath extraction
  ([`1b4533a`](https://github.com/contabiliz/invoice-processors/commit/1b4533a9fc3539d0fc49bf4a07846dda575451a2))


## v1.0.1 (2026-03-25)

### Bug Fixes

- **types**: Resolve pyright errors across pdf files
  ([`5aaeb38`](https://github.com/contabiliz/invoice-processors/commit/5aaeb384bfbbc85a9a728e894a529b28a27e8dcd))

### Continuous Integration

- Clean up workflow formatting and step ordering
  ([`09c3a47`](https://github.com/contabiliz/invoice-processors/commit/09c3a4734e588ace8a85305f8912821f4f358043))


## v1.0.0 (2026-03-23)

- Initial Release
