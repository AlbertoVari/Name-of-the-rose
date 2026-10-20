from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from rose.artifacts import query, render_artifacts, write_artifacts
from rose.extract import blob_sha, digest, extract, safe_path, verify_source
from rose.model import validate_model


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.contents = {"DEMO.cpy": b"01 BANK.\n   05 BALANCE PIC S9(7)V99.\n"}
        (self.root / "DEMO.cpy").write_bytes(self.contents["DEMO.cpy"])
        self.lock = {
            "schema_version": "1.0", "repository": "owner/example", "commit": "a" * 40,
            "files": [{"path": path, "sha256": digest(content), "git_blob_sha": blob_sha(content)} for path, content in self.contents.items()],
        }
        self.index = extract(self.lock, self.contents)
        self.evidence = {"path": "DEMO.cpy", "start_line": 2, "end_line": 2}
        self.model = {
            "schema_version": "1.0", "source": {"repository": self.lock["repository"], "commit": self.lock["commit"]},
            "objects": [{"id": "object.account", "label": "Account", "description": "A ledger account", "epistemic_status": "observed", "evidence": [self.evidence], "properties": [{"name": "balance", "datatype": "PIC S9(7)V99", "description": "Recorded amount", "source_field": "BALANCE", "evidence": [self.evidence]}]}],
            "links": [], "actions": [], "rules": [],
        }

    def validate(self, model=None):
        validate_model(self.model if model is None else model, self.lock, self.contents, self.index)

    def test_valid_source_and_model(self):
        self.assertEqual(verify_source(self.lock, self.root), self.contents)
        self.validate()

    def test_source_drift_including_line_endings_fails(self):
        (self.root / "DEMO.cpy").write_bytes(self.contents["DEMO.cpy"].replace(b"\n", b"\r\n"))
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            verify_source(self.lock, self.root)

    def test_git_blob_mismatch_fails_even_with_correct_sha256(self):
        self.lock["files"][0]["git_blob_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "Git blob SHA mismatch"):
            verify_source(self.lock, self.root)

    def test_path_traversal_absolute_path_and_symlink_escape_rejected(self):
        for path in ("../secret", "/etc/passwd", "dir/../../secret", "..\\secret"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                safe_path(self.root, path)
        (self.root / "escape").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "escapes"):
            safe_path(self.root, "escape/outside")

    def test_bad_evidence_ranges_and_unlocked_paths_fail(self):
        for bad in ({"path": "../secret", "start_line": 1, "end_line": 1}, {"path": "DEMO.cpy", "start_line": 0, "end_line": 1}, {"path": "DEMO.cpy", "start_line": 1, "end_line": 99}, {"path": "DEMO.cpy", "start_line": True, "end_line": 1}, {"path": "DEMO.cpy", "start_line": 2, "end_line": 1}):
            model = deepcopy(self.model)
            model["objects"][0]["evidence"] = [bad]
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "evidence"):
                self.validate(model)

    def test_wrong_excerpt_digest_rejected(self):
        self.model["objects"][0]["evidence"][0]["excerpt_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "excerpt SHA256 mismatch"):
            self.validate()

    def test_field_must_be_declared_in_cited_range_and_have_matching_picture(self):
        prop = self.model["objects"][0]["properties"][0]
        prop["source_field"] = "INVENTED-FIELD"
        with self.assertRaisesRegex(ValueError, "no declaration"):
            self.validate()
        prop["source_field"] = "BALANCE"
        prop["datatype"] = "PIC X(10)"
        with self.assertRaisesRegex(ValueError, "source PIC"):
            self.validate()
        prop["datatype"] = "PIC S9(7)V99"
        prop["evidence"] = [{"path": "DEMO.cpy", "start_line": 1, "end_line": 1}]
        with self.assertRaisesRegex(ValueError, "no declaration"):
            self.validate()

    def test_duplicate_ids_dangling_links_and_wrong_kind_action_refs_fail(self):
        record = {"id": "link.owner", "label": "Owner", "description": "Ownership interpretation", "epistemic_status": "inferred", "evidence": [self.evidence], "from": "object.account", "to": "object.missing"}
        self.model["links"] = [record]
        with self.assertRaisesRegex(ValueError, "dangling object"):
            self.validate()
        record["to"] = "object.account"
        self.model["actions"] = [{"id": "action.post", "label": "Post", "description": "Posting", "epistemic_status": "observed", "evidence": [self.evidence], "inputs": ["link.owner"], "outputs": ["object.account"], "rule_ids": ["rule.missing"]}]
        with self.assertRaisesRegex(ValueError, "wrong-kind reference"):
            self.validate()
        self.model["actions"] = []
        record["id"] = "object.account"
        with self.assertRaisesRegex(ValueError, "Duplicate id"):
            self.validate()

    def test_observed_requires_evidence_proposed_remains_explicit(self):
        record = self.model["objects"][0]
        record["evidence"] = []
        with self.assertRaisesRegex(ValueError, "requires evidence"):
            self.validate()
        record["epistemic_status"] = "proposed"
        self.validate()
        graph = __import__("json").loads(render_artifacts(self.model, self.lock, self.contents, self.index)["ontology.jsonld"])
        self.assertEqual(graph["@graph"][0]["epistemic_status"], "proposed")
        record["epistemic_status"] = "certain"
        with self.assertRaisesRegex(ValueError, "epistemic_status"):
            self.validate()

    def test_model_cannot_silently_change_source_commit(self):
        self.model["source"]["commit"] = "b" * 40
        with self.assertRaisesRegex(ValueError, "locked repository and commit"):
            self.validate()

    def test_build_is_deterministic_and_check_never_repairs_drift(self):
        artifacts = render_artifacts(self.model, self.lock, self.contents, self.index)
        self.assertEqual(artifacts, render_artifacts(self.model, self.lock, self.contents, self.index))
        output = self.root / "generated"
        write_artifacts(output, artifacts)
        write_artifacts(output, artifacts, check=True)
        target = output / "mappings.csv"
        target.write_text("tampered\n")
        with self.assertRaisesRegex(ValueError, "Generated artifact drift: mappings.csv"):
            write_artifacts(output, artifacts, check=True)
        self.assertEqual(target.read_text(), "tampered\n")

    def test_query_returns_reviewed_records_with_status_and_absolute_pinned_links(self):
        matches = query(self.model, "balance")
        self.assertEqual([record["id"] for record in matches], ["object.account"])
        self.assertEqual(matches[0]["epistemic_status"], "observed")
        self.assertIn("https://github.com/owner/example/blob/" + "a" * 40, matches[0]["evidence"][0]["permalink"])
        self.assertEqual(query(self.model, "nonexistent"), [])


if __name__ == "__main__":
    unittest.main()
