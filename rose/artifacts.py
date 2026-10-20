"""Deterministic, text-only semantic exports; raw upstream source is not embedded."""

from __future__ import annotations

import csv
from copy import deepcopy
import io
import json
from pathlib import Path

from .extract import evidence_ref, permalink
from .model import records


def json_text(value) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def enriched(ref: dict, lock: dict, contents: dict[str, bytes]) -> dict:
    return evidence_ref(ref["path"], ref["start_line"], ref["end_line"], contents[ref["path"]], lock["repository"], lock["commit"])


def mapping_rows(model: dict, lock: dict, contents: dict[str, bytes]) -> list[dict]:
    rows = []
    for collection, record in records(model):
        assertions = [(record["id"], collection[:-1] if collection != "properties" else "property", record, "")]
        assertions.extend((record["id"] + "." + prop["name"], "property", prop, prop.get("source_field") or "") for prop in record.get("properties", []))
        for identifier, kind, assertion, source_field in assertions:
            status = assertion.get("epistemic_status", record["epistemic_status"])
            for reference in assertion["evidence"]:
                ev = enriched(reference, lock, contents)
                rows.append({
                    "semantic_id": identifier, "kind": kind, "label": assertion.get("label", assertion.get("name", "")),
                    "epistemic_status": status, "source_field": source_field,
                    **ev,
                })
    return sorted(rows, key=lambda row: (row["semantic_id"], row["path"], row["start_line"], row["end_line"]))


def jsonld(model: dict, lock: dict, contents: dict[str, bytes]) -> dict:
    graph = []
    for collection, original in records(model):
        record = deepcopy(original)
        record["@id"] = "urn:rose:" + record.pop("id")
        record["@type"] = "rose:" + {"objects": "ObjectType", "links": "LinkType", "actions": "ActionType", "rules": "BusinessRule"}[collection]
        record["evidence"] = [enriched(ref, lock, contents) for ref in record["evidence"]]
        for attr in ("from", "to"):
            if attr in record:
                record[attr] = {"@id": "urn:rose:" + record[attr]}
        for attr in ("inputs", "outputs", "rule_ids"):
            if attr in record:
                record[attr] = [{"@id": "urn:rose:" + identifier} for identifier in record[attr]]
        for prop in record.get("properties", []):
            prop["epistemic_status"] = prop.get("epistemic_status", record["epistemic_status"])
            prop["evidence"] = [enriched(ref, lock, contents) for ref in prop["evidence"]]
        graph.append(record)
    return {
        "@context": {"@vocab": "urn:rose:vocab:", "rose": "urn:rose:vocab:", "label": "http://www.w3.org/2000/01/rdf-schema#label", "description": "http://purl.org/dc/terms/description", "evidence": {"@container": "@set"}, "properties": {"@container": "@set"}},
        "@id": "urn:rose:model:" + lock["commit"],
        "source": model["source"], "schema_version": "1.0", "@graph": sorted(graph, key=lambda record: record["@id"]),
    }


def render_artifacts(model: dict, lock: dict, contents: dict[str, bytes], index: dict) -> dict[str, str]:
    rows = mapping_rows(model, lock, contents)
    columns = ["semantic_id", "kind", "label", "epistemic_status", "source_field", "path", "start_line", "end_line", "excerpt_sha256", "permalink"]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    markdown = [
        "# Evidence mappings", "", f"Source commit: `{lock['commit']}`.", "",
        "Generated from reviewed annotations. `observed` cites declarations or operations; `inferred` is an interpretation; `proposed` describes target design. References do not prove runtime behavior or compliance.", "",
        "Excerpt SHA256 hashes cover the exact source bytes for the inclusive line range, preserving line endings. Raw source excerpts are not embedded.", "",
        "| Semantic assertion | Status | Source field | Evidence | Excerpt SHA256 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        md = lambda value: str(value).replace("|", "\\|").replace("\n", " ")
        label = f"{row['path']}:{row['start_line']}-{row['end_line']}"
        markdown.append(f"| `{md(row['semantic_id'])}` | {row['epistemic_status']} | {md(row['source_field'])} | [{md(label)}]({row['permalink']}) | `{row['excerpt_sha256']}` |")
    return {
        "evidence.json": json_text(index),
        "ontology.jsonld": json_text(jsonld(model, lock, contents)),
        "mappings.csv": stream.getvalue(),
        "mappings.md": "\n".join(markdown) + "\n",
    }


def write_artifacts(output: Path, artifacts: dict[str, str], check: bool = False) -> None:
    if check:
        drift = []
        for name, value in artifacts.items():
            target = output / name
            if not target.is_file() or target.read_bytes() != value.encode("utf-8"):
                drift.append(name)
        if drift:
            raise ValueError("Generated artifact drift: " + ", ".join(drift) + "; rerun the build command and review the diff")
        return
    output.mkdir(parents=True, exist_ok=True)
    for name, value in artifacts.items():
        (output / name).write_bytes(value.encode("utf-8"))


def query(model: dict, phrase: str, limit: int = 20) -> list[dict]:
    """Deterministic token search over annotations; does not generate new claims."""
    terms = phrase.casefold().split()
    if not terms:
        return []
    matches = []
    for collection, record in records(model):
        # Include metadata, field names and evidence paths for developer exploration.
        haystack = json.dumps(record, ensure_ascii=False).casefold()
        if not all(term in haystack for term in terms):
            continue
        score = sum(5 if term in record["id"].casefold() else 3 if term in record["label"].casefold() else 1 for term in terms)
        result = deepcopy(record)
        result["kind"] = collection[:-1]
        for ref in result["evidence"]:
            ref["permalink"] = permalink(model["source"]["repository"], model["source"]["commit"], ref["path"], ref["start_line"], ref["end_line"])
        matches.append((score, record["id"], result))
    return [row[2] for row in sorted(matches, key=lambda row: (-row[0], row[1]))[:limit]]
