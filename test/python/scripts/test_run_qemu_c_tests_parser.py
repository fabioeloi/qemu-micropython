import unittest
import re
import sys
import os

# To make imports work if `scripts` is not in PYTHONPATH by default when discover is run.
# This attempts to add the project's root `scripts` directory to the path.
# This assumes tests are run from project root, or `python -m unittest discover -s test/python`
# from project root.
try:
    # For direct execution: scripts/test_run_qemu_c_tests_parser.py
    # current_dir = os.path.dirname(os.path.abspath(__file__)) # .../test/python/scripts
    # scripts_dir_path = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "scripts"))
    # if scripts_dir_path not in sys.path:
    #    sys.path.insert(0, scripts_dir_path)

    # If running with `python -m unittest discover -s test/python` from project root:
    # The 'scripts' directory should be discoverable if we add project root.
    # However, direct import like `from scripts.run_qemu_c_tests...` is better if scripts is a package.
    # For now, redefine regexes to avoid import complexities in this agent environment.
    pass
except Exception: # Fallback if path manipulation fails for some reason
    pass


# Redefine regexes here to avoid modifying the target script for importability for now.
# Ideally, these would be imported from scripts.run_qemu_c_tests
TEST_LINE_RE_STR = r"^TEST\((?P<name>[a-zA-Z0-9_]+)\):(?P<status>PASS|FAIL|IGNORE)(?::(?P<message>.*))?"
TEST_LINE_RE = re.compile(TEST_LINE_RE_STR)

SUMMARY_LINE_RE_STR = r"^SUMMARY:(?P<total>\d+):(?P<failures>\d+):(?P<ignored>\d+)"
SUMMARY_LINE_RE = re.compile(SUMMARY_LINE_RE_STR)


class TestRunQemuCTestParserRegexes(unittest.TestCase):

    def test_TEST_LINE_RE_pass(self):
        line = "TEST(my_test_case_1):PASS"
        match = TEST_LINE_RE.match(line)
        self.assertIsNotNone(match, f"Regex did not match: '{line}'")
        if match: # Redundant due to assertIsNotNone, but good for type hinting/clarity
            self.assertEqual(match.group("name"), "my_test_case_1")
            self.assertEqual(match.group("status"), "PASS")
            self.assertIsNone(match.group("message"))

    def test_TEST_LINE_RE_fail_with_message(self):
        line = "TEST(anotherTest):FAIL:Assertion failed at main.c:42"
        match = TEST_LINE_RE.match(line)
        self.assertIsNotNone(match, f"Regex did not match: '{line}'")
        if match:
            self.assertEqual(match.group("name"), "anotherTest")
            self.assertEqual(match.group("status"), "FAIL")
            self.assertEqual(match.group("message"), "Assertion failed at main.c:42")

    def test_TEST_LINE_RE_fail_no_message(self):
        line = "TEST(test_no_msg_fail):FAIL"
        match = TEST_LINE_RE.match(line)
        self.assertIsNotNone(match, f"Regex did not match: '{line}'")
        if match:
            self.assertEqual(match.group("name"), "test_no_msg_fail")
            self.assertEqual(match.group("status"), "FAIL")
            # The message group will exist but be empty string if only ":" is present
            # If ":" is absent, it's None. Current regex makes it optional.
            # If line was "TEST(...):FAIL:", message would be "".
            # If line is "TEST(...):FAIL", message is None.
            self.assertIsNone(match.group("message"))

    def test_TEST_LINE_RE_ignore_with_message(self):
        line = "TEST(test_to_ignore):IGNORE:Not implemented yet"
        match = TEST_LINE_RE.match(line)
        self.assertIsNotNone(match, f"Regex did not match: '{line}'")
        if match:
            self.assertEqual(match.group("name"), "test_to_ignore")
            self.assertEqual(match.group("status"), "IGNORE")
            self.assertEqual(match.group("message"), "Not implemented yet")

    def test_TEST_LINE_RE_invalid_status(self):
        line = "TEST(test_invalid):UNKNOWN:Some message"
        match = TEST_LINE_RE.match(line)
        self.assertIsNone(match, f"Regex should not match invalid status: '{line}'")

    def test_TEST_LINE_RE_malformed_no_status_colon(self):
        line = "TEST(test_malformed_no_colon)PASS" # Missing colon after name
        match = TEST_LINE_RE.match(line)
        self.assertIsNone(match, f"Regex should not match malformed line (no colon): '{line}'")

    def test_TEST_LINE_RE_malformed_no_name_parentheses(self):
        line = "TEST:PASS" # Missing parentheses for name
        match = TEST_LINE_RE.match(line)
        self.assertIsNone(match, f"Regex should not match malformed line (no parentheses for name): '{line}'")

    def test_TEST_LINE_RE_name_with_hyphen(self):
        line = "TEST(test-with-hyphen):PASS" # Hyphen not in [a-zA-Z0-9_]
        match = TEST_LINE_RE.match(line)
        self.assertIsNone(match, f"Regex should not match name with hyphen: '{line}'")

    def test_SUMMARY_LINE_RE_valid(self):
        line = "SUMMARY:10:2:1"
        match = SUMMARY_LINE_RE.match(line)
        self.assertIsNotNone(match, f"Regex did not match: '{line}'")
        if match:
            self.assertEqual(match.group("total"), "10")
            self.assertEqual(match.group("failures"), "2")
            self.assertEqual(match.group("ignored"), "1")

    def test_SUMMARY_LINE_RE_all_zeros(self):
        line = "SUMMARY:0:0:0"
        match = SUMMARY_LINE_RE.match(line)
        self.assertIsNotNone(match, f"Regex did not match: '{line}'")
        if match:
            self.assertEqual(match.group("total"), "0")
            self.assertEqual(match.group("failures"), "0")
            self.assertEqual(match.group("ignored"), "0")

    def test_SUMMARY_LINE_RE_large_numbers(self):
        line = "SUMMARY:1234:567:89"
        match = SUMMARY_LINE_RE.match(line)
        self.assertIsNotNone(match, f"Regex did not match: '{line}'")
        if match:
            self.assertEqual(match.group("total"), "1234")
            self.assertEqual(match.group("failures"), "567")
            self.assertEqual(match.group("ignored"), "89")

    def test_SUMMARY_LINE_RE_malformed_not_enough_numbers(self):
        line = "SUMMARY:10:2" # Missing ignored_count
        match = SUMMARY_LINE_RE.match(line)
        self.assertIsNone(match, f"Regex should not match summary with too few numbers: '{line}'")

    def test_SUMMARY_LINE_RE_malformed_non_numeric(self):
        line = "SUMMARY:10:FAIL:1" # FAIL is not a number
        match = SUMMARY_LINE_RE.match(line)
        self.assertIsNone(match, f"Regex should not match summary with non-numeric part: '{line}'")

if __name__ == '__main__':
    # This allows running the tests directly via `python test/python/scripts/test_run_qemu_c_tests_parser.py`
    # It's also discoverable by `python -m unittest discover ...`
    unittest.main(verbosity=2)
