"""Validate reviewed semantic annotations against a pinned lexical evidence index."""

from __future__ import annotations

from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import urlparse

from .extract import evidence_ref


COLLECTIONS = ("objects", "links", "actions", "rules")
STATUSES = {"observed", "inferred", "proposed"}


def read_json(path: Path) -> dict:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(result, dict):
        raise ValueError(f"{path}: top-level JSON object required")
    return result


def records(model: dict):
    for collection in COLLECTIONS:
        for record in model.get(collection, []):
            yield collection, record


def validate_model(model: dict, lock: dict, contents: dict[str, bytes], index: dict) -> None:
    errors: list[str] = []
    if model.get("schema_version") != "1.0":
        errors.append("model.schema_version must be '1.0'")
    if model.get("source") != {"repository": lock["repository"], "commit": lock["commit"]}:
        errors.append("model.source must exactly match the locked repository and commit")
    for collection in COLLECTIONS:
        if not isinstance(model.get(collection), list):
            errors.append(f"model.{collection} must be an array")
    if errors:
        raise ValueError("Model validation failed:\n" + "\n".join(errors))

    ids = []
    sets = {collection: set() for collection in COLLECTIONS}
    for collection, record in records(model):
        if not isinstance(record, dict):
            errors.append(f"model.{collection}: each record must be an object")
            continue
        identifier = record.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"model.{collection}: record requires a nonempty string id")
        else:
            ids.append(identifier)
            sets[collection].add(identifier)
    errors.extend(f"Duplicate id: {identifier}" for identifier, count in Counter(ids).items() if count > 1)
    line_counts = {path: len(content.decode("utf-8").splitlines()) for path, content in contents.items()}
    fields = {file["path"]: file["data_items"] for file in index["files"]}

    def check_evidence(value, context: str, status: str) -> list[dict]:
        if not isinstance(value, list):
            errors.append(f"{context}.evidence must be an array")
            return []
        if not value and status != "proposed":
            errors.append(f"{context}: {status} assertion requires evidence")
        valid = []
        for position, reference in enumerate(value):
            label = f"{context}.evidence[{position}]"
            if not isinstance(reference, dict):
                errors.append(f"{label}: evidence must be an object")
                continue
            path, start, end = reference.get("path"), reference.get("start_line"), reference.get("end_line")
            if not isinstance(path, str) or path not in contents:
                errors.append(f"{label}: evidence path is not a locked source file: {path!r}")
                continue
            if type(start) is not int or type(end) is not int or not (1 <= start <= end <= line_counts[path]):
                errors.append(f"{label}: invalid evidence range {start!r}..{end!r}; {path} has {line_counts[path]} lines")
                continue
            actual = evidence_ref(path, start, end, contents[path], lock["repository"], lock["commit"])
            if "excerpt_sha256" in reference and reference["excerpt_sha256"] != actual["excerpt_sha256"]:
                errors.append(f"{label}: excerpt SHA256 mismatch")
            valid.append(reference)
        return valid

    def check_refs(value, targets: set, context: str) -> None:
        if not isinstance(value, list):
            errors.append(f"{context}: expected array of IDs")
            return
        for target in value:
            if not isinstance(target, str) or target not in targets:
                errors.append(f"{context}: dangling or wrong-kind reference {target!r}")

    for collection, record in records(model):
        if not isinstance(record, dict):
            continue
        identifier = record.get("id", f"unnamed {collection}")
        for attr in ("label", "description"):
            if not isinstance(record.get(attr), str) or not record[attr].strip():
                errors.append(f"{identifier}.{attr}: nonempty string required")
        status = record.get("epistemic_status")
        if status not in STATUSES:
            errors.append(f"{identifier}: epistemic_status must be observed, inferred, or proposed")
        check_evidence(record.get("evidence"), str(identifier), status)
        if collection == "links":
            for attr in ("from", "to"):
                target = record.get(attr)
                if not isinstance(target, str) or target not in sets["objects"]:
                    errors.append(f"{identifier}.{attr}: dangling object reference {target!r}")
        if collection == "actions":
            for attr in ("inputs", "outputs"):
                check_refs(record.get(attr), sets["objects"], f"{identifier}.{attr}")
            check_refs(record.get("rule_ids"), sets["rules"], f"{identifier}.rule_ids")
        if collection != "objects":
            continue
        properties = record.get("properties")
        if not isinstance(properties, list):
            errors.append(f"{identifier}.properties must be an array")
            continue
        names: set[str] = set()
        for prop in properties:
            if not isinstance(prop, dict):
                errors.append(f"{identifier}: property must be an object")
                continue
            name = prop.get("name")
            label = f"{identifier}.{name}"
            if not isinstance(name, str) or not name.strip():
                errors.append(f"{label}: property requires nonempty name")
            elif name in names:
                errors.append(f"{label}: duplicate property name")
            else:
                names.add(name)
            for attr in ("datatype", "description"):
                if not isinstance(prop.get(attr), str) or not prop[attr].strip():
                    errors.append(f"{label}.{attr}: nonempty string required")
            prop_status = prop.get("epistemic_status", status)
            if prop_status not in STATUSES:
                errors.append(f"{label}: invalid epistemic_status")
            references = check_evidence(prop.get("evidence"), label, prop_status)
            source_field = prop.get("source_field")
            if source_field is None and prop_status == "proposed":
                continue
            if not isinstance(source_field, str) or not source_field:
                errors.append(f"{label}: source_field must name a declaration")
                continue
            matches = [field for reference in references for field in fields.get(reference["path"], []) if field["name"] == source_field and reference["start_line"] <= field["evidence"]["start_line"] <= reference["end_line"]]
            if not matches:
                errors.append(f"{label}: source_field {source_field!r} has no declaration in its evidence ranges")
            datatype = prop.get("datatype", "")
            if isinstance(datatype, str) and datatype.upper().startswith("PIC ") and matches:
                if datatype[4:].upper() not in {field["picture"] for field in matches}:
                    errors.append(f"{label}: datatype does not match the source PIC clause")
    if errors:
        raise ValueError("Model validation failed:\n" + "\n".join(errors))


def validate_crosswalk(crosswalk: dict, model: dict) -> None:
    """Check conceptual alignment references; never certify regulatory compliance."""
    errors = []
    reviewed_on = crosswalk.get("reviewed_on")
    try:
        if not isinstance(reviewed_on, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", reviewed_on):
            raise ValueError
        date.fromisoformat(reviewed_on)
    except ValueError:
        errors.append("crosswalk.reviewed_on must be a valid ISO YYYY-MM-DD date")
    references, mappings = crosswalk.get("references"), crosswalk.get("mappings")
    for label, value in (("references", references), ("mappings", mappings)):
        if not isinstance(value, list) or not value:
            errors.append(f"crosswalk.{label} must be a nonempty array")
    if errors:
        raise ValueError("Crosswalk validation failed:\n" + "\n".join(errors))

    def required_text(item: dict, field: str, context: str) -> None:
        if not isinstance(item.get(field), str) or not item[field].strip():
            errors.append(f"{context}.{field} must be a nonempty string")

    ids = []
    reference_ids = set()
    for reference in references:
        if not isinstance(reference, dict):
            errors.append("crosswalk reference must be an object")
            continue
        context = str(reference.get("id", "unnamed reference"))
        for field in ("id", "title", "url", "version_scope"):
            required_text(reference, field, context)
        if isinstance(reference.get("id"), str):
            ids.append(reference["id"])
            reference_ids.add(reference["id"])
        url = reference.get("url")
        if isinstance(url, str):
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
                errors.append(f"{context}.url must be an HTTPS reference without credentials")
    model_ids = {record["id"] for _, record in records(model)}
    for mapping in mappings:
        if not isinstance(mapping, dict):
            errors.append("crosswalk mapping must be an object")
            continue
        context = str(mapping.get("id", "unnamed mapping"))
        for field in ("id", "target_concept", "gap"):
            required_text(mapping, field, context)
        if isinstance(mapping.get("id"), str):
            ids.append(mapping["id"])
        if mapping.get("relation") not in ("conceptual_alignment", "gap"):
            errors.append(f"{context}.relation must be conceptual_alignment or gap; equivalence is not supported")
        if mapping.get("status") != "proposed":
            errors.append(f"{context}.status must remain proposed; source evidence cannot establish regulatory compliance")
        for field, available in (("model_ids", model_ids), ("reference_ids", reference_ids)):
            values = mapping.get(field)
            if not isinstance(values, list) or not values:
                errors.append(f"{context}.{field} must be a nonempty array of IDs")
                continue
            for identifier in values:
                if not isinstance(identifier, str) or identifier not in available:
                    errors.append(f"{context}.{field}: dangling reference {identifier!r}")
        required = mapping.get("required_evidence")
        if not isinstance(required, list) or not required or any(not isinstance(value, str) or not value.strip() for value in required):
            errors.append(f"{context}.required_evidence must be a nonempty array of strings")
    errors.extend(f"Duplicate crosswalk id: {identifier}" for identifier, count in Counter(ids).items() if count > 1)
    if errors:
        raise ValueError("Crosswalk validation failed:\n" + "\n".join(errors))
