# python-corvus-json-schema-rs

A [Bowtie](https://github.com/bowtie-json-schema/bowtie) test harness for
[corvus-json-schema-rs](https://pypi.org/project/corvus-json-schema-rs/), the Python evaluator backed by the corvus-json-schema Rust crate of
[Corvus.JsonSchema](https://github.com/corvus-dotnet/Corvus.JsonSchema).

Its image is published to `ghcr.io/bowtie-json-schema/python-corvus-json-schema-rs` and run via
`bowtie run -i python-corvus-json-schema-rs`.

The harness compiles each case's schema with the case's `registry` as the document resolver and validates each
instance. For `annotations` output it evaluates through a verbose results collector and reports each annotation with
its instance location and `#…` keyword location.

The image installs the latest release from PyPI; the `IMPLEMENTATION_VERSION` build argument pins another.
