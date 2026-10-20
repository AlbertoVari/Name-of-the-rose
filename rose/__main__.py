"""CLI entry point. All commands work offline after acquiring the locked source."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from . import __version__
from .artifacts import json_text, query, render_artifacts, write_artifacts
from .extract import extract, verify_source
from .model import read_json, validate_crosswalk, validate_model


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="python -m rose", description="Evidence-bound COBOL semantic exploration (static lexical analysis).")
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("extract", "validate", "build"):
        command = commands.add_parser(name)
        command.add_argument("--source", type=Path, required=True, help="separately acquired, locked upstream source directory")
        command.add_argument("--lock", type=Path, default=Path("source-lock.json"))
        if name != "extract":
            command.add_argument("--model", type=Path, default=Path("model/ontology.json"))
            command.add_argument("--crosswalk", type=Path, help="optional standards crosswalk; defaults to standards-crosswalk.json beside the model when present")
        if name == "extract":
            command.add_argument("--output", type=Path, default=Path("build/evidence.json"))
        if name == "build":
            command.add_argument("--output", type=Path, default=Path("build"))
            command.add_argument("--check", action="store_true", help="verify generated files match exactly; never writes")
    search = commands.add_parser("query", help="deterministic search of reviewed model annotations")
    search.add_argument("term")
    search.add_argument("--model", type=Path, default=Path("model/ontology.json"))
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--json", action="store_true")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "query":
            if args.limit < 1:
                raise ValueError("--limit must be positive")
            model = read_json(args.model)
            matches = query(model, args.term, args.limit)
            if args.json:
                print(json_text({"source": model["source"], "query": args.term, "matches": matches}), end="")
            else:
                print(f"Reviewed annotations at {model['source']['commit']}; search does not execute or revalidate source.")
                if not matches:
                    print("No matching annotations. Try a shorter term or a COBOL field name.")
                for record in matches:
                    print(f"\n{record['id']} — {record['label']} [{record['epistemic_status']}]")
                    print(record["description"])
                    for ev in record["evidence"]:
                        print("  " + ev["permalink"])
            return 0
        lock = read_json(args.lock)
        contents = verify_source(lock, args.source)
        index = extract(lock, contents)
        if args.command == "extract":
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(json_text(index).encode("utf-8"))
            print(f"Indexed {len(index['files'])} locked source files → {args.output}")
            return 0
        model = read_json(args.model)
        validate_model(model, lock, contents, index)
        crosswalk_path = args.crosswalk or args.model.parent / "standards-crosswalk.json"
        crosswalk_count = None
        if args.crosswalk is not None or crosswalk_path.exists():
            crosswalk = read_json(crosswalk_path)
            validate_crosswalk(crosswalk, model)
            crosswalk_count = len(crosswalk["mappings"])
        if args.command == "validate":
            count = sum(len(model[name]) for name in ("objects", "links", "actions", "rules"))
            print(f"Validated {len(contents)} exact source files and {count} semantic records. Static evidence checks only.")
            if crosswalk_count is not None:
                print(f"Validated {crosswalk_count} proposed standards mappings and their reference IDs; no compliance certification.")
            return 0
        artifacts = render_artifacts(model, lock, contents, index)
        write_artifacts(args.output, artifacts, args.check)
        print(("Verified" if args.check else "Generated") + f" {len(artifacts)} deterministic artifacts in {args.output}")
        return 0
    except (ValueError, OSError, UnicodeDecodeError, KeyError, TypeError) as exc:
        print(f"rose: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
