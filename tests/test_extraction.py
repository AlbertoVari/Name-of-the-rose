"""Synthetic fixtures test parser boundaries, not the upstream banking runtime."""

import unittest

from rose.extract import evidence_ref, parse_source, permalink


REPOSITORY = "owner/example"
COMMIT = "a" * 40


class ExtractionTests(unittest.TestCase):
    def parse(self, source, path="copybooks/DEMO.cpy"):
        return parse_source(path, source.encode(), REPOSITORY, COMMIT)

    def test_group_hierarchy_88_conditions_and_multiline_numeric_value(self):
        source = '''01 BANK.
   05 FLAGS.
      10 STATE PIC X VALUE "A".
         88 ACTIVE VALUE "A".
         88 BLOCKED VALUES ARE "B" "F".
      10 AMOUNT PIC S9(7)V99
         VALUE +10000.00.
   05 ACCOUNT-LIST OCCURS 2 TIMES.
      10 ACCOUNT-ID PIC 9(4).
01 OTHER.
   05 PRICE-VALUE PIC 9(3).
77 STANDALONE PIC 9.
'''
        items = {item["name"]: item for item in self.parse(source)["data_items"]}
        self.assertEqual(items["AMOUNT"]["qualified_name"], "BANK.FLAGS.AMOUNT")
        self.assertEqual(items["ACTIVE"]["parent"], items["STATE"]["id"])
        self.assertEqual(items["BLOCKED"]["parent"], items["STATE"]["id"])
        self.assertEqual(items["BLOCKED"]["kind"], "condition")
        self.assertEqual(items["BLOCKED"]["value"], '"B" "F"')
        self.assertEqual(items["AMOUNT"]["value"], "+10000.00")
        self.assertEqual(items["AMOUNT"]["picture"], "S9(7)V99")
        self.assertEqual(items["AMOUNT"]["evidence"]["start_line"], 6)
        self.assertEqual(items["AMOUNT"]["evidence"]["end_line"], 7)
        self.assertEqual(items["ACCOUNT-ID"]["qualified_name"], "BANK.ACCOUNT-LIST.ACCOUNT-ID")
        self.assertEqual(items["ACCOUNT-LIST"]["occurs"], {"min": 2, "max": 2, "depending_on": None})
        self.assertEqual(items["PRICE-VALUE"]["qualified_name"], "OTHER.PRICE-VALUE")
        self.assertIsNone(items["PRICE-VALUE"]["value"])
        self.assertIsNone(items["STANDALONE"]["parent"])

    def test_literal_keywords_do_not_become_clauses_or_comments(self):
        source = '''01 TEST-RECORD.
   05 NOTE-TEXT PIC X(60) VALUE "*> DISPLAY COMP PIC X(8)".
   05 QUOTED PIC X(30) VALUE 'it''s *> still text'. *> comment
   05 NUMBER-FIELD PIC S9(3) VALUE 12 COMP-3.
'''
        items = {item["name"]: item for item in self.parse(source)["data_items"]}
        self.assertEqual(items["NOTE-TEXT"]["value"], '"*> DISPLAY COMP PIC X(8)"')
        self.assertIsNone(items["NOTE-TEXT"]["usage"])
        self.assertEqual(items["NOTE-TEXT"]["picture"], "X(60)")
        self.assertEqual(items["QUOTED"]["value"], "'it''s *> still text'")
        self.assertEqual(items["NUMBER-FIELD"]["value"], "12")
        self.assertEqual(items["NUMBER-FIELD"]["usage"], "COMP-3")

    def test_only_lexical_call_and_named_perform_references(self):
        source = '''IDENTIFICATION DIVISION.
PROGRAM-ID. DEMO.
DATA DIVISION.
WORKING-STORAGE SECTION.
COPY SHARED.
01 RUN-FLAG PIC X.
PROCEDURE DIVISION.
MAIN.
    DISPLAY "CALL ""GLPOST0"" *> PERFORM PHANTOM"
    *> CALL "MISLEADING-COMMENT"
    PERFORM
       VALIDATE-DATA
    PERFORM UNTIL RUN-FLAG = "Y"
       CONTINUE
    END-PERFORM
    PERFORM 3 TIMES
       CONTINUE
    END-PERFORM
    CALL "ACTUAL" USING RUN-FLAG
    CALL DYNAMIC-NAME
    PERFORM DO-A THRU DO-Z
    GOBACK.
VALIDATE-DATA.
    EXIT PARAGRAPH.
DO-A.
    CONTINUE.
DO-Z.
    EXIT PARAGRAPH.
'''
        result = self.parse(source, "src/DEMO.cob")
        self.assertEqual(result["program_id"], "DEMO")
        self.assertEqual([x["name"] for x in result["copy_references"]], ["SHARED"])
        self.assertEqual([x["name"] for x in result["paragraphs"]], ["MAIN", "VALIDATE-DATA", "DO-A", "DO-Z"])
        self.assertEqual([x["target"] for x in result["control_references"]], ["VALIDATE-DATA", "ACTUAL", "DYNAMIC-NAME", "DO-A"])
        self.assertEqual(result["control_references"][0]["resolution"], "local-paragraph")
        self.assertEqual(result["control_references"][0]["evidence"]["end_line"], 12)
        self.assertEqual(result["control_references"][1]["resolution"], "literal-program")
        self.assertEqual(result["control_references"][2]["resolution"], "dynamic-unresolved")
        self.assertEqual(result["control_references"][3]["through"], "DO-Z")

    def test_unsupported_fixed_format_and_continued_literals_fail_explicitly(self):
        with self.assertRaisesRegex(ValueError, "fixed-format"):
            self.parse("000100 01 RECORD-A.\n")
        with self.assertRaisesRegex(ValueError, "continued literal"):
            self.parse('01 TEXT-FIELD PIC X VALUE "unterminated\n')

    def test_excerpt_hash_preserves_original_bytes_and_links_pin_the_commit(self):
        import hashlib
        reference = evidence_ref("src/A.cob", 2, 3, b"first\r\nsecond\r\nthird", REPOSITORY, COMMIT)
        self.assertEqual(reference["excerpt_sha256"], hashlib.sha256(b"second\r\nthird").hexdigest())
        self.assertEqual(reference["permalink"], f"https://github.com/owner/example/blob/{COMMIT}/src/A.cob#L2-L3")
        self.assertEqual(permalink("https://github.com/owner/example", COMMIT, "src/A.cob", 2, 3), reference["permalink"])


if __name__ == "__main__":
    unittest.main()
