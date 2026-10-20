"""Contract tests use synthetic ledger entries, never claimed agent executions."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import unittest


HERE = Path(__file__).parent
ROOT = HERE.parent
SPEC = importlib.util.spec_from_file_location("rose_orchestration_check", HERE / "check.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


def template():
    return json.loads((HERE / "run.example.json").read_text(encoding="utf-8"))


def accepted_fixture():
    """Structurally valid synthetic fixture; this is not an actual run ledger."""
    run = template()
    run.update(run_id="unit-test-fixture", iteration=1, phase="accepted")
    run["execution"] = {"mode": "local-static", "host": "synthetic unittest fixture", "live_copilot": False}
    pin = run["source"]["commit"]
    run["evidence"] = [{
        "id": "e-source", "kind": "source", "description": "Synthetic source reference for contract test",
        "source_commit": pin, "path": "src/EXAMPLE.cob", "start_line": 1, "end_line": 2,
        "uri": f"{run['source']['repository']}/blob/{pin}/src/EXAMPLE.cob#L1-L2",
    }]
    run["claims"] = [{
        "id": "c-one", "author": "Umberto", "classification": "observed", "status": "accepted",
        "statement": "Synthetic example claim", "evidence_refs": ["e-source"], "model_refs": [],
    }]
    run["decisions"] = [{
        "id": f"d-{gate}", "gate": gate, "verdict": "accept", "reviewer": "Eric", "iteration": 1,
        "rationale": "Synthetic fixture verdict", "evidence_refs": ["e-source"],
    } for gate in ("scope", "model", "release")]
    run["checks"] = [{
        "id": "check-one", "argv": ["python", "-m", "rose", "validate", "--source", "../upstream"],
        "cwd": ".", "exit_code": 0, "log_path": "synthetic-test-log.txt",
    }]
    return run


class LedgerTests(unittest.TestCase):
    def test_template_has_no_fabricated_history(self):
        run = template()
        self.assertEqual([], CHECK.validate_ledger(run))
        self.assertEqual("intake", run["phase"])
        self.assertFalse(run["execution"]["live_copilot"])
        for collection in CHECK.COLLECTIONS:
            self.assertEqual([], run[collection])

    def test_valid_accepted_fixture(self):
        self.assertEqual([], CHECK.validate_ledger(accepted_fixture()))

    def test_rejects_unpinned_source_and_wrong_range_link(self):
        run = accepted_fixture()
        run["evidence"][0]["source_commit"] = "0" * 40
        run["evidence"][0]["uri"] = run["evidence"][0]["uri"].replace("L1-L2", "L1-L3")
        errors = "\n".join(CHECK.validate_ledger(run))
        self.assertIn("source commit differs", errors)
        self.assertIn("exact line range", errors)

    def test_rejects_unsupported_observed_claim(self):
        run = accepted_fixture()
        run["claims"][0]["evidence_refs"] = []
        errors = "\n".join(CHECK.validate_ledger(run))
        self.assertIn("require evidence", errors)
        self.assertIn("source or tool evidence", errors)

    def test_standard_does_not_prove_source_behavior(self):
        run = accepted_fixture()
        run["evidence"] = [{
            "id": "e-source", "kind": "standard", "uri": "https://example.invalid/standard",
            "description": "Synthetic standard reference", "accessed_on": "2026-10-18",
            "version": "test", "jurisdiction": "test",
        }]
        self.assertIn("source or tool evidence", "\n".join(CHECK.validate_ledger(run)))

    def test_release_gate_and_checks_cannot_be_skipped(self):
        run = accepted_fixture()
        run["decisions"].pop()
        run["checks"] = []
        errors = "\n".join(CHECK.validate_ledger(run))
        self.assertIn("release acceptance", errors)
        self.assertIn("successful recorded checks", errors)

    def test_scope_change_invalidates_old_model_acceptance(self):
        run = accepted_fixture()
        new_scope = deepcopy(run["decisions"][0])
        new_scope["id"] = "d-scope-again"
        run["decisions"].append(new_scope)
        self.assertIn("model gate predates", "\n".join(CHECK.validate_ledger(run)))

    def test_failed_check_can_be_retried_without_erasing_history(self):
        run = accepted_fixture()
        success = deepcopy(run["checks"][0])
        success["id"] = "check-two"
        run["checks"][0]["exit_code"] = 1
        self.assertIn("successful recorded checks", "\n".join(CHECK.validate_ledger(run)))
        run["checks"].append(success)
        self.assertEqual([], CHECK.validate_ledger(run))

    def test_conflict_blocks_acceptance_and_needs_evidence_to_resolve(self):
        run = accepted_fixture()
        other = deepcopy(run["claims"][0])
        other.update(id="c-two", author="Peter", status="disputed")
        run["claims"].append(other)
        conflict = {
            "id": "conflict-one", "claim_ids": ["c-one", "c-two"], "owner": "Eric",
            "status": "open", "resolution": "", "evidence_refs": [],
        }
        run["conflicts"].append(conflict)
        self.assertIn("open conflicts", "\n".join(CHECK.validate_ledger(run)))
        conflict.update(status="resolved", resolution="Synthetic resolution")
        self.assertIn("resolved conflict needs evidence", "\n".join(CHECK.validate_ledger(run)))
        conflict["evidence_refs"] = ["e-source"]
        self.assertEqual([], CHECK.validate_ledger(run))

    def test_duplicate_and_dangling_references_fail(self):
        run = accepted_fixture()
        run["evidence"].append(deepcopy(run["evidence"][0]))
        run["claims"][0]["evidence_refs"] = ["not-real"]
        errors = "\n".join(CHECK.validate_ledger(run))
        self.assertIn("duplicate IDs", errors)
        self.assertIn("unknown evidence reference", errors)

    def test_live_claim_requires_transcript_and_consistent_mode(self):
        run = template()
        run["execution"]["mode"] = "copilot-delegated"
        self.assertIn("live_copilot=true", "\n".join(CHECK.validate_ledger(run)))
        run["execution"]["live_copilot"] = True
        self.assertIn("transcript reference", "\n".join(CHECK.validate_ledger(run)))

    def test_prior_snapshot_prevents_evidence_rewrite(self):
        old = accepted_fixture()
        new = deepcopy(old)
        new["evidence"][0]["description"] = "Rewritten evidence"
        self.assertIn("evidence must be append-only", "\n".join(CHECK.validate_ledger(new, old)))

    def test_budget_and_noninteger_iterations_fail(self):
        for bad_iteration in (4, True, "1"):
            run = template()
            run["iteration"] = bad_iteration
            self.assertTrue(CHECK.validate_ledger(run))


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"Missing frontmatter: {path}")
    header = text.split("---", 2)[1]
    return dict(line.split(":", 1) for line in header.strip().splitlines())


class CopilotConfigurationTests(unittest.TestCase):
    def test_five_profiles_have_expected_capability_boundaries(self):
        paths = list((ROOT / ".github/agents").glob("*.agent.md"))
        self.assertEqual({"umberto", "peter", "satya", "boris", "eric"}, {p.name.split(".")[0] for p in paths})
        for path in paths:
            fields = {key: value.strip() for key, value in frontmatter(path).items()}
            self.assertTrue(fields["description"])
            tools = set(re.findall(r"[A-Za-z-]+", fields["tools"]))
            self.assertNotIn("*", fields["tools"])
            if fields["name"] in {"Umberto", "Peter", "Eric"}:
                self.assertEqual({"read", "search"}, tools)
            if fields["name"] == "Satya":
                self.assertIn("agent", tools)
                self.assertEqual({"Umberto", "Peter", "Boris", "Eric"}, set(re.findall(r"[A-Za-z]+", fields["agents"])))
            else:
                self.assertNotIn("agent", tools)

    def test_skill_is_project_scoped_without_blanket_tool_preapproval(self):
        path = ROOT / ".github/skills/rose-semiotic-trace/SKILL.md"
        fields = frontmatter(path)
        self.assertEqual("rose-semiotic-trace", fields["name"].strip())
        self.assertTrue(fields["description"].strip())
        self.assertNotIn("allowed-tools", fields)

    def test_prompt_agent_names_resolve(self):
        names = {frontmatter(path)["name"].strip() for path in (ROOT / ".github/agents").glob("*.agent.md")}
        for path in (ROOT / ".github/prompts").glob("*.prompt.md"):
            self.assertIn(frontmatter(path)["agent"].strip(), names)


if __name__ == "__main__":
    unittest.main()
