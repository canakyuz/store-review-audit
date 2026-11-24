"""Tests for the rejection notice reader."""
import contextlib
import io
import json
import unittest
from pathlib import Path

from diagnose_rejection import REFERENCES, diagnose, main

BENCH_NOTICE = Path(__file__).resolve().parents[3] / "bench" / "coin-quiz" / "store" / "review-message.txt"


def ids(message):
    return [c["id"] for c in diagnose(message)]


class AppleTests(unittest.TestCase):
    def test_bench_notice_names_the_subscription_guideline(self):
        cited = diagnose(BENCH_NOTICE.read_text())
        self.assertEqual([(c["id"], c["cited_as"]) for c in cited], [("apple:3.1.2", ["3.1.2"])])
        self.assertEqual(cited[0]["url"], "https://developer.apple.com/app-store/review/guidelines/#3.1.2")
        self.assertEqual(cited[0]["quote"], "Guideline 3.1.2 - Business - Payments - Subscriptions")

    def test_sub_clause_letter_is_kept_and_mapped_to_its_clause(self):
        cited = diagnose("Guideline 5.1.1(v) - Legal - Privacy - Data Collection and Storage")
        self.assertEqual([(c["id"], c["cited_as"]) for c in cited], [("apple:5.1.1", ["5.1.1(v)"])])

    def test_each_guideline_once_in_notice_order(self):
        message = "Guideline 4.8 - Design\ntext\nGuideline 2.1 - Performance\nGuideline 4.8 again\nGuideline 2.1(b)"
        cited = diagnose(message)
        self.assertEqual([c["id"] for c in cited], ["apple:4.8", "apple:2.1"])
        self.assertEqual(cited[1]["cited_as"], ["2.1", "2.1(b)"])

    def test_a_version_number_is_not_a_guideline(self):
        self.assertEqual(ids("Coin Quiz 1.4.0 (11) crashed on iOS 19.2.1 in section 4.2 of our test plan"), [])

    def test_unknown_clause_falls_back_to_its_parent(self):
        self.assertEqual(ids("Guideline 4.3.9 - Design - Spam"), ["apple:4.3"])
        self.assertEqual(ids("Guideline 9.9 - Nothing"), [])


    def test_words_after_guidelines_that_are_not_clause_numbers(self):
        for text in ("Please read the guidelines 3 times", "Guidelines 2025 update", "Guideline 12"):
            self.assertEqual(ids(text), [], text)

    def test_several_clauses_in_one_citation(self):
        self.assertEqual(ids("Guidelines 2.1 and 4.3(a) were not met"), ["apple:2.1", "apple:4.3"])
        self.assertEqual(ids("Guideline 3.1.1 & 3.1.2 - Business"), ["apple:3.1.1", "apple:3.1.2"])
        self.assertEqual(ids("See section 5.1.1 of the App Store Review Guidelines."), ["apple:5.1.1"])
        self.assertEqual(ids("Guideline 4.0 - Design"), ["apple:4"])


class GoogleTests(unittest.TestCase):
    def test_policy_names_and_console_sections(self):
        message = ("Issue found: Violation of User Data policy\nYour app is not compliant with the Subscriptions "
                   "policy. Fix the Data safety section. Review the Permissions policy.")
        self.assertEqual(ids(message), [
            "google:policy:9888076", "google:policy:9900533",
            "topic:support.google.com/googleplay/android-developer/answer/10787469", "google:policy:12579724"])

    def test_console_words_without_a_policy_are_not_cited(self):
        self.assertEqual(ids("We updated the payments form and the ads section and the data access form."), [])

    def test_wrapped_and_double_spaced_names(self):
        self.assertEqual(ids("Violation of Deceptive\nBehavior policy"), ["google:policy:9888077"])
        self.assertEqual(ids("Fix the Data  Safety form"), ["topic:support.google.com/googleplay/android-developer/answer/10787469"])
        self.assertEqual(ids("Issue: Gambling policy"), ["google:policy:9877032"])

    def test_the_program_policies_as_a_whole_are_not_an_issue(self):
        self.assertEqual(ids("Please review the Developer Program Policies and resubmit."), [])

    def test_a_policy_word_without_the_word_policy_is_not_cited(self):
        self.assertEqual(ids("We removed spam and ads from the payments screen and updated metadata."), [])

    def test_requirements_come_from_the_digest_only_while_its_hash_matches(self):
        catalog = {i["id"]: i for i in json.loads((REFERENCES / "policy-catalog.json").read_text())["items"]}
        digest = {d["id"]: d for d in json.loads((REFERENCES / "policy-digest.json").read_text())}
        cited = diagnose("Violation of Subscriptions policy")[0]
        current = digest[cited["id"]]["sha256"] == catalog[cited["id"]]["sha256"]
        self.assertEqual(bool(cited["requirements"]), current)


class CommandTests(unittest.TestCase):
    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = main(list(argv))
        return code, out.getvalue()

    def test_standard_input_with_bytes_that_are_not_utf8(self):
        import subprocess, sys
        from diagnose_rejection import __file__ as script
        done = subprocess.run([sys.executable, script], input=b"Guideline 2.1 caf\xe9", capture_output=True)
        self.assertEqual(done.returncode, 0)
        self.assertIn(b"apple:2.1", done.stdout)

    def test_exit_codes_and_json(self):
        code, text = self.run_main(str(BENCH_NOTICE))
        self.assertEqual(code, 0)
        self.assertIn("apple:3.1.2  (cited as 3.1.2)", text)
        code, text = self.run_main(str(BENCH_NOTICE), "--json")
        self.assertEqual(json.loads(text)["cited"][0]["id"], "apple:3.1.2")
        self.assertEqual(self.run_main(str(BENCH_NOTICE.parent / "missing.txt"))[0], 1)
        code, text = self.run_main(str(BENCH_NOTICE.parent / "console-export" / "play-console.json"))
        self.assertEqual(code, 1)
        self.assertIn("No Apple guideline number or Google Play policy name was recognised", text)


if __name__ == "__main__":
    unittest.main()
