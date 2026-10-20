"""Validate collaboration-ledger shape and review invariants; never launch agents.

Uses only the JSON Schema keywords present in run.schema.json. It is deliberately
not a general JSON Schema implementation or an attestation of recorded events.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


SCHEMA_PATH = Path(__file__).with_name("run.schema.json")
COLLECTIONS = ("evidence", "claims", "handoffs", "conflicts", "decisions", "checks")


def _shape(value: Any, spec: dict, root: dict, at: str, errors: list[str]) -> None:
    if "$ref" in spec:
        resolved = root
        for part in spec["$ref"].split("/")[1:]:
            resolved = resolved[part]
        _shape(value, resolved, root, at, errors)
        return
    kinds = {
        "object": lambda x: isinstance(x, dict),
        "array": lambda x: isinstance(x, list),
        "string": lambda x: isinstance(x, str),
        "integer": lambda x: type(x) is int,
        "boolean": lambda x: type(x) is bool,
    }
    kind = spec.get("type")
    if kind and not kinds[kind](value):
        errors.append(f"{at}: expected {kind}")
        return
    if "const" in spec and (value != spec["const"] or type(value) is not type(spec["const"])):
        errors.append(f"{at}: expected constant {spec['const']!r}")
    if "enum" in spec and value not in spec["enum"]:
        errors.append(f"{at}: unsupported value {value!r}")
    if isinstance(value, dict):
        for key in spec.get("required", []):
            if key not in value:
                errors.append(f"{at}.{key}: missing required field")
        properties = spec.get("properties", {})
        for key, item in value.items():
            if key in properties:
                _shape(item, properties[key], root, f"{at}.{key}", errors)
            elif spec.get("additionalProperties") is False:
                errors.append(f"{at}.{key}: unexpected field")
    elif isinstance(value, list):
        if len(value) < spec.get("minItems", 0):
            errors.append(f"{at}: too few items")
        for index, item in enumerate(value):
            if "items" in spec:
                _shape(item, spec["items"], root, f"{at}[{index}]", errors)
    elif isinstance(value, str):
        if len(value.strip()) < spec.get("minLength", 0):
            errors.append(f"{at}: empty text")
        if "pattern" in spec and not re.search(spec["pattern"], value):
            errors.append(f"{at}: invalid format")
    elif type(value) is int:
        if "minimum" in spec and value < spec["minimum"]:
            errors.append(f"{at}: below minimum")
        if "maximum" in spec and value > spec["maximum"]:
            errors.append(f"{at}: above maximum")


def validate_ledger(ledger: Any, previous: Any = None) -> list[str]:
    """Return human-readable errors; no file contents or commands are executed."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    _shape(ledger, schema, schema, "run", errors)
    if errors:
        return errors
    indexes = {}
    for collection in COLLECTIONS:
        records = ledger[collection]
        indexes[collection] = {record["id"]: record for record in records}
        if len(indexes[collection]) != len(records):
            errors.append(f"{collection}: duplicate IDs")

    def refs(values: list[str], collection: str, at: str) -> None:
        for value in values:
            if value not in indexes[collection]:
                errors.append(f"{at}: unknown {collection} reference {value!r}")

    pin = ledger["source"]["commit"]
    base = ledger["source"]["repository"]
    for item in ledger["evidence"]:
        at = f"evidence.{item['id']}"
        if item["kind"] == "source":
            required = ("source_commit", "path", "start_line", "end_line")
            if not all(key in item for key in required):
                errors.append(f"{at}: source requires commit, path, and line range")
                continue
            if item["source_commit"] != pin:
                errors.append(f"{at}: source commit differs from run pin")
            path = item["path"]
            if path.startswith("/") or ".." in path.split("/") or "\\" in path:
                errors.append(f"{at}: source path must be repository-relative")
            if item["end_line"] < item["start_line"]:
                errors.append(f"{at}: reversed source line range")
            start, end = item["start_line"], item["end_line"]
            permalink = f"{base}/blob/{pin}/{path}#L{start}"
            valid_links = {permalink + f"-L{end}"}
            if start == end:
                valid_links.add(permalink)
            if item["uri"] not in valid_links:
                errors.append(f"{at}: URI must match pinned path and exact line range")
        if item["kind"] == "tool-output":
            if not all(key in item for key in ("argv", "exit_code", "log_path")):
                errors.append(f"{at}: tool-output requires argv, exit_code, and log_path")
        if item["kind"] == "standard":
            if not all(key in item for key in ("accessed_on", "version", "jurisdiction")):
                errors.append(f"{at}: standard requires date, version, and jurisdiction")

    for claim in ledger["claims"]:
        at = f"claim.{claim['id']}"
        refs(claim["evidence_refs"], "evidence", at)
        if "supersedes" in claim:
            refs([claim["supersedes"]], "claims", at)
            if claim["supersedes"] == claim["id"]:
                errors.append(f"{at}: cannot supersede itself")
        if claim["classification"] in ("observed", "inferred") and not claim["evidence_refs"]:
            errors.append(f"{at}: observed/inferred claims require evidence")
        if claim["classification"] == "observed" and claim["status"] == "accepted":
            kinds = {indexes["evidence"].get(ref, {}).get("kind") for ref in claim["evidence_refs"]}
            if not kinds.intersection({"source", "tool-output"}):
                errors.append(f"{at}: accepted observed claim needs source or tool evidence")

    for conflict in ledger["conflicts"]:
        at = f"conflict.{conflict['id']}"
        refs(conflict["claim_ids"], "claims", at)
        refs(conflict["evidence_refs"], "evidence", at)
        if len(set(conflict["claim_ids"])) < 2:
            errors.append(f"{at}: must identify at least two distinct claims")
        if conflict["status"] != "open" and not conflict["resolution"].strip():
            errors.append(f"{at}: closed/deferred conflict needs a resolution")
        if conflict["status"] == "resolved" and not conflict["evidence_refs"]:
            errors.append(f"{at}: resolved conflict needs evidence")
        if conflict["status"] in ("open", "deferred"):
            if any(indexes["claims"].get(cid, {}).get("status") == "accepted" for cid in conflict["claim_ids"]):
                errors.append(f"{at}: unresolved conflicting claims cannot be accepted")

    for handoff in ledger["handoffs"]:
        refs(handoff["claim_ids"], "claims", f"handoff.{handoff['id']}")
        if handoff["iteration"] > ledger["iteration"]:
            errors.append(f"handoff.{handoff['id']}: future iteration")
        if handoff["from"] == handoff["to"]:
            errors.append(f"handoff.{handoff['id']}: self-delegation is not supported")

    latest = {}
    last_iteration = 0
    for index, decision in enumerate(ledger["decisions"]):
        at = f"decision.{decision['id']}"
        refs(decision["evidence_refs"], "evidence", at)
        if decision["iteration"] < last_iteration or decision["iteration"] > ledger["iteration"]:
            errors.append(f"{at}: decisions must be ordered within the current iteration")
        last_iteration = decision["iteration"]
        gate = decision["gate"]
        if decision["verdict"] == "accept" and gate != "scope":
            if not decision["evidence_refs"]:
                errors.append(f"{at}: accepted model/release gate needs evidence")
            prior_gate = "scope" if gate == "model" else "model"
            if prior_gate not in latest or latest[prior_gate][1]["verdict"] != "accept":
                errors.append(f"{at}: {prior_gate} gate must be accepted first")
        latest[gate] = (index, decision)

    def accepted(gate: str) -> bool:
        return gate in latest and latest[gate][1]["verdict"] == "accept"

    phase = ledger["phase"]
    if phase not in ("intake", "blocked") and not accepted("scope"):
        errors.append(f"phase {phase}: scope gate is not accepted")
    if phase in ("implement", "validate", "review", "accepted"):
        if not accepted("model"):
            errors.append(f"phase {phase}: model gate is not accepted")
        elif accepted("scope") and latest["model"][0] < latest["scope"][0]:
            errors.append(f"phase {phase}: model gate predates the latest scope decision")
    if phase != "intake" and ledger["iteration"] == 0:
        errors.append("non-intake phase requires iteration >= 1")
    if phase == "accepted":
        if not accepted("release"):
            errors.append("accepted phase requires Eric's release acceptance")
        elif accepted("model") and latest["release"][0] < latest["model"][0]:
            errors.append("accepted phase: release gate predates the latest model decision")
        if any(item["status"] == "open" for item in ledger["conflicts"]):
            errors.append("accepted phase cannot have open conflicts")
        latest_checks = {(tuple(item["argv"]), item["cwd"]): item for item in ledger["checks"]}
        if not latest_checks or any(item["exit_code"] != 0 for item in latest_checks.values()):
            errors.append("accepted phase requires successful recorded checks")
        if not any(item["status"] == "accepted" for item in ledger["claims"]):
            errors.append("accepted phase requires accepted semantic claims")
    execution = ledger["execution"]
    if execution["mode"] == "copilot-delegated" and not execution["live_copilot"]:
        errors.append("copilot-delegated mode requires live_copilot=true")
    if execution["mode"] == "local-static" and execution["live_copilot"]:
        errors.append("local-static mode cannot claim live Copilot execution")
    if execution["live_copilot"] and not execution.get("transcript_path"):
        errors.append("live Copilot execution requires a genuine transcript reference")

    if previous is not None:
        prior_errors: list[str] = []
        _shape(previous, schema, schema, "previous", prior_errors)
        if prior_errors:
            errors.extend(prior_errors)
            return errors
        for key in ("run_id", "source", "execution", "question", "scope", "max_iterations"):
            if ledger[key] != previous[key]:
                errors.append(f"snapshot: immutable run field changed: {key}")
        if ledger["iteration"] not in (previous["iteration"], previous["iteration"] + 1):
            errors.append("snapshot: iteration may stay the same or advance by one")
        for key in ("evidence", "handoffs", "decisions", "checks"):
            if ledger[key][:len(previous[key])] != previous[key]:
                errors.append(f"snapshot: {key} must be append-only")
        for old in previous["claims"]:
            new = indexes["claims"].get(old["id"], {})
            if any(new.get(key) != value for key, value in old.items() if key != "status"):
                errors.append(f"snapshot: claim {old['id']} removed or rewritten")
        for old in previous["conflicts"]:
            new = indexes["conflicts"].get(old["id"], {})
            if any(new.get(key) != old[key] for key in ("id", "claim_ids", "owner")):
                errors.append(f"snapshot: conflict {old['id']} removed or rewritten")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--previous", type=Path)
    args = parser.parse_args(argv)
    try:
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
        previous = json.loads(args.previous.read_text(encoding="utf-8")) if args.previous else None
        errors = validate_ledger(ledger, previous)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read ledger: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("Ledger structure and review invariants passed; execution/source truth is not attested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
