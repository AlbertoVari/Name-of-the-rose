from copy import deepcopy
import unittest

from rose.model import validate_crosswalk


class CrosswalkValidationTests(unittest.TestCase):
    def setUp(self):
        self.model = {"objects": [{"id": "object.account"}], "links": [], "actions": [], "rules": []}
        self.crosswalk = {
            "reviewed_on": "2026-10-18",
            "references": [{"id": "ref.standard", "title": "Example reference", "url": "https://example.org/standard", "version_scope": "Concept only; not a verified implementation"}],
            "mappings": [{"id": "alignment.account", "model_ids": ["object.account"], "reference_ids": ["ref.standard"], "relation": "conceptual_alignment", "status": "proposed", "target_concept": "Account concept", "gap": "No conformance evidence", "required_evidence": ["Approved interpretation and integration tests"]}],
        }

    def test_proposed_crosswalk_passes(self):
        validate_crosswalk(self.crosswalk, self.model)

    def test_dangling_source_reference_and_model_id_fail(self):
        for key in ("model_ids", "reference_ids"):
            bad = deepcopy(self.crosswalk)
            bad["mappings"][0][key] = ["missing"]
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "dangling reference"):
                validate_crosswalk(bad, self.model)

    def test_equivalence_and_observed_compliance_are_not_accepted(self):
        for key, value in (("relation", "exactMatch"), ("status", "observed"), ("status", "compliant")):
            bad = deepcopy(self.crosswalk)
            bad["mappings"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, "equivalence|proposed"):
                validate_crosswalk(bad, self.model)

    def test_duplicate_ids_are_rejected(self):
        self.crosswalk["mappings"][0]["id"] = "ref.standard"
        with self.assertRaisesRegex(ValueError, "Duplicate crosswalk id"):
            validate_crosswalk(self.crosswalk, self.model)

    def test_missing_gaps_and_required_evidence_fail(self):
        for key, value in (("gap", ""), ("required_evidence", []), ("required_evidence", "unspecified")):
            bad = deepcopy(self.crosswalk)
            bad["mappings"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_crosswalk(bad, self.model)

    def test_date_and_reference_metadata_are_required(self):
        self.crosswalk["reviewed_on"] = "2026-02-30"
        with self.assertRaisesRegex(ValueError, "valid ISO"):
            validate_crosswalk(self.crosswalk, self.model)
        self.crosswalk["reviewed_on"] = "2026-10-18"
        self.crosswalk["references"][0]["url"] = "javascript:alert(1)"
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            validate_crosswalk(self.crosswalk, self.model)
        self.crosswalk["references"][0]["url"] = "https://example.org"
        self.crosswalk["references"][0]["version_scope"] = ""
        with self.assertRaisesRegex(ValueError, "version_scope"):
            validate_crosswalk(self.crosswalk, self.model)


if __name__ == "__main__":
    unittest.main()
