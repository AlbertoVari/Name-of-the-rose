"""Regression checks for high-value findings in the reviewed slice.

These test checked-in evidence artifacts, never the COBOL runtime. CI separately
regenerates the artifacts from exact upstream bytes and checks for drift.
"""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = json.loads((ROOT / "build/evidence.json").read_text())
        cls.files = {item["path"]: item for item in cls.index["files"]}
        cls.lock = json.loads((ROOT / "source-lock.json").read_text())

    def test_no_invented_transaction_to_gl_or_regulatory_call_edges(self):
        for path in ("src/TXNPOST0.cob", "src/GLPOST0.cob", "src/BSACTRO.cob", "src/CTRFIL0.cob"):
            self.assertEqual([edge for edge in self.files[path]["control_references"] if edge["kind"] == "call"], [], path)
        targets = [edge["target"] for edge in self.files["src/EODPROC0.cob"]["control_references"] if edge["kind"] == "call"]
        self.assertEqual(targets, ["GLPOST0", "INTCALC0", "TXNPOST0", "AUDTLOG0"])

    def test_source_pin_constants_and_condition_names_are_not_guesses(self):
        self.assertEqual(self.index["source"]["commit"], self.lock["commit"])
        items = {item["name"]: item for item in self.files["copybooks/CPYCONST.cpy"]["data_items"]}
        self.assertEqual(items["WS-CTR-THRESHOLD"]["value"], "+10000.00")
        self.assertEqual(items["WS-SAR-STRUCT-CEILING"]["value"], "+9999.99")
        for item in self.files["src/TXNPOST0.cob"]["data_items"]:
            self.assertTrue(item["evidence"]["permalink"].startswith("https://github.com/NSEvent/cobol-banking-system/blob/" + self.lock["commit"]))


if __name__ == "__main__":
    unittest.main()
