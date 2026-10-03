"""A Bowtie (https://github.com/bowtie-json-schema/bowtie) harness for corvus-json-schema-rs.

It speaks IHOP (one JSON request per line on standard input, one response per line on standard output):

- ``start`` reports the implementation and its dialects;
- ``dialect`` sets the dialect for schemas without ``$schema``;
- ``run`` compiles the case's schema with the case's ``registry`` as the document resolver and validates each
  instance (for ``annotations`` output, through a verbose results collector, reporting each annotation with its
  instance location and ``#…`` keyword location);
- ``stop`` exits.
"""

import json
import platform
import sys
import traceback

import corvus_json_schema_rs as cjs

DIALECTS = {
    "https://json-schema.org/draft/2020-12/schema": cjs.Dialect.DRAFT202012,
    "https://json-schema.org/draft/2019-09/schema": cjs.Dialect.DRAFT201909,
    "http://json-schema.org/draft-07/schema#": cjs.Dialect.DRAFT7,
    "http://json-schema.org/draft-06/schema#": cjs.Dialect.DRAFT6,
    "http://json-schema.org/draft-04/schema#": cjs.Dialect.DRAFT4,
}


def errored(error):
    return {
        "errored": True,
        "context": {"message": str(error), "traceback": "".join(traceback.format_exception(error))},
    }


# The characters a URI fragment keeps unencoded.
FRAGMENT_SAFE = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~!$&'()*+,;=:@/?")


def percent_encode(text):
    """Percent-encodes text as a URI fragment does (upper-case hex, UTF-8)."""
    return "".join(chr(b) if b in FRAGMENT_SAFE else f"%{b:02X}" for b in text.encode("utf-8"))


def annotations_of(grouped):
    """The annotations a verbose collector grouped (instance location, then keyword as a JSON-pointer token, then
    schema location as a ``#…`` fragment; the same in every Corvus implementation) as Bowtie lists them: each with its
    keyword unescaped, and its keyword location the schema location's fragment followed by ``/`` and the keyword
    token, percent-encoded as the fragment is."""
    return [
        {
            "keyword": token.replace("~1", "/").replace("~0", "~"),
            "instanceLocation": instance_location,
            "keywordLocation": f"{schema_location}/{percent_encode(token)}",
            "annotation": value,
        }
        for instance_location, keywords in grouped.items()
        for token, locations in keywords.items()
        for schema_location, value in locations.items()
    ]


def strip_fragment(uri):
    return uri.split("#", 1)[0]


class Harness:
    def __init__(self):
        self.started = False
        self.dialect = cjs.Dialect.DRAFT202012

    def start(self, request):
        if request.get("version") != 1:
            raise ValueError(f"Unsupported IHOP version {request.get('version')!r}")
        self.started = True
        return {
            "version": 1,
            "implementation": {
                "language": "python",
                "name": "corvus-json-schema-rs",
                "version": cjs.__version__,
                "homepage": "https://github.com/corvus-dotnet/Corvus.JsonSchema",
                "documentation": "https://pypi.org/project/corvus-json-schema-rs/",
                "issues": "https://github.com/corvus-dotnet/Corvus.JsonSchema/issues",
                "source": "https://github.com/corvus-dotnet/Corvus.JsonSchema",
                "dialects": list(DIALECTS),
                "os": platform.system(),
                "os_version": platform.release(),
                "language_version": platform.python_version(),
            },
        }

    def set_dialect(self, request):
        self.require_started()
        dialect = DIALECTS.get(request.get("dialect"))
        if dialect is None:
            return {"ok": False}
        self.dialect = dialect
        return {"ok": True}

    def run(self, request):
        self.require_started()
        case = request["case"]
        seq = request["seq"]
        registry = {strip_fragment(uri): schema for uri, schema in (case.get("registry") or {}).items()}
        try:
            validator = cjs.compile(
                case["schema"],
                default_dialect=self.dialect,
                resolve_document=lambda uri: registry.get(strip_fragment(uri)),
            )
        except Exception as error:  # every compilation failure is reported for the case
            return {"seq": seq, **errored(error)}
        annotations = request.get("output") == "annotations"
        results = []
        for test in case["tests"]:
            instance = test["instance"]
            try:
                if not annotations:
                    results.append({"valid": validator(instance)})
                    continue
                collector = cjs.JsonSchemaResultsCollector(cjs.ResultsLevel.VERBOSE)
                valid = validator.evaluate(instance, collector)
                results.append({"valid": valid, "annotations": annotations_of(cjs.collect_annotations(collector))})
            except Exception as error:  # an error for one instance does not stop the others
                results.append(errored(error))
        return {"seq": seq, "results": results}

    def require_started(self):
        if not self.started:
            raise RuntimeError("Not started")


def main():
    harness = Harness()
    for line in sys.stdin:
        if not line.strip():
            continue
        request = json.loads(line)
        cmd = request.get("cmd")
        if cmd == "start":
            response = harness.start(request)
        elif cmd == "dialect":
            response = harness.set_dialect(request)
        elif cmd == "run":
            response = harness.run(request)
        elif cmd == "stop":
            harness.require_started()
            return
        else:
            raise ValueError(f"Unknown command {cmd!r}")
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
