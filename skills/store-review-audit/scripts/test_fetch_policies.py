import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import fetch_policies as fp

APPLE_PAGE = """<html><nav>menu 2026</nav><main>
<h2 id="introduction">Introduction</h2><p>The guiding principle.</p>
<h3 id="1">1. Safety</h3><p>Intro to safety.</p>
<ul><li id="1.1.1"><strong>1.1.1</strong> Defamatory content.</li>
<li id="1.1.2"><strong>1.1.2</strong> Realistic violence.</li></ul>
<h2 id="after-you-submit">After You Submit</h2><p>Timing.</p>
</main><footer>Copyright 2026</footer></html>"""


class AppleGuidelinesTest(unittest.TestCase):
    def test_splits_numbered_clauses_and_framing_sections(self):
        items = fp.apple_guidelines(APPLE_PAGE)
        self.assertEqual([i["id"] for i in items], ["apple:introduction", "apple:1", "apple:1.1.1", "apple:1.1.2", "apple:after-you-submit"])
        clause = next(i for i in items if i["id"] == "apple:1.1.1")
        self.assertEqual(clause["_text"], "1.1.1 Defamatory content.")
        self.assertEqual(clause["url"], fp.APPLE_GUIDELINES + "#1.1.1")

    def test_page_chrome_does_not_change_clause_hashes(self):
        changed = APPLE_PAGE.replace("menu 2026", "menu 2027").replace("Copyright 2026", "Copyright 2027")
        self.assertEqual([i["sha256"] for i in fp.apple_guidelines(APPLE_PAGE)], [i["sha256"] for i in fp.apple_guidelines(changed)])

    def test_a_clause_edit_changes_only_that_clause(self):
        before = {i["id"]: i["sha256"] for i in fp.apple_guidelines(APPLE_PAGE)}
        after = {i["id"]: i["sha256"] for i in fp.apple_guidelines(APPLE_PAGE.replace("Realistic violence.", "Realistic or graphic violence."))}
        self.assertEqual([k for k in before if before[k] != after[k]], ["apple:1.1.2"])


class GooglePageTest(unittest.TestCase):
    def test_keeps_article_text_and_drops_feedback_widget(self):
        page = "<html><header>nav</header><article><h1>Subscriptions</h1><p>" + "Rule text. " * 30 + "</p>Was this helpful? Yes No</article></html>"
        text = fp.google_page("https://support.google.com/x", page)
        self.assertTrue(text.startswith("Subscriptions Rule text."))
        self.assertNotIn("helpful", text)


class CheckModeTest(unittest.TestCase):
    def run_check(self, old_items, new_items):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = Path(tmp) / "policy-catalog.json"
            catalog.write_text(json.dumps({"checked": "2026-11-18", "items": old_items}))
            out = io.StringIO()
            with mock.patch.object(fp, "CATALOG", catalog), mock.patch.object(fp, "CACHE", Path(tmp) / "cache"), \
                    mock.patch.object(fp, "build", return_value=new_items), redirect_stdout(out):
                code = fp.main(["--check"])
            return code, out.getvalue()

    def entry(self, item_id, text):
        return fp.item(item_id, "apple", item_id, "https://example.com/" + item_id, text)

    def test_no_change_exits_zero(self):
        a = self.entry("apple:1", "same")
        code, out = self.run_check(fp.public([a]), [a])
        self.assertEqual(code, 0)
        self.assertIn("no changes", out)

    def test_changed_added_and_removed_items_exit_one(self):
        old = fp.public([self.entry("apple:1", "old"), self.entry("apple:2", "gone")])
        new = [self.entry("apple:1", "new"), self.entry("apple:3", "fresh")]
        code, out = self.run_check(old, new)
        self.assertEqual(code, 1)
        self.assertIn("changed\tapple:1", out)
        self.assertIn("added\tapple:3", out)
        self.assertIn("removed\tapple:2", out)

    def test_unreachable_source_exits_two_and_leaves_catalogue_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = Path(tmp) / "policy-catalog.json"
            catalog.write_text("{}")
            with mock.patch.object(fp, "CATALOG", catalog), mock.patch.object(fp, "build", side_effect=fp.FetchError("429")), \
                    redirect_stdout(io.StringIO()), mock.patch("sys.stderr", io.StringIO()):
                self.assertEqual(fp.main(["--write"]), 2)
            self.assertEqual(catalog.read_text(), "{}")

    def test_get_prints_one_item_and_says_whether_it_matches(self):
        clause = fp.apple_guidelines(APPLE_PAGE)[2]
        with tempfile.TemporaryDirectory() as tmp:
            catalog = Path(tmp) / "policy-catalog.json"
            catalog.write_text(json.dumps({"checked": "2026-11-18", "items": fp.public([clause])}))
            out = io.StringIO()
            with mock.patch.object(fp, "CATALOG", catalog), mock.patch.object(fp, "fetch", return_value=APPLE_PAGE), redirect_stdout(out):
                self.assertEqual(fp.main(["--get", "apple:1.1.1"]), 0)
            self.assertIn("matches catalogue: yes", out.getvalue())
            self.assertIn("1.1.1 Defamatory content.", out.getvalue())

    def test_get_falls_back_to_a_current_digest_entry(self):
        page = fp.item("google:policy:1", "google", "Ads", "https://support.google.com/x?hl=en", "ads text")
        with tempfile.TemporaryDirectory() as tmp:
            catalog, digest = Path(tmp) / "c.json", Path(tmp) / "d.json"
            catalog.write_text(json.dumps({"checked": "2026-11-18", "items": fp.public([page])}))
            digest.write_text(json.dumps([{"id": "google:policy:1", "sha256": page["sha256"], "url": page["url"], "requirements": ["Ads must not imitate system UI."], "announced": []}]))
            out = io.StringIO()
            with mock.patch.object(fp, "CATALOG", catalog), mock.patch.object(fp, "DIGEST", digest), \
                    mock.patch.object(fp, "fetch", side_effect=fp.FetchError("429")), redirect_stdout(out):
                self.assertEqual(fp.main(["--get", "google:policy:1"]), 0)
            self.assertIn("source: digest", out.getvalue())
            self.assertIn("Ads must not imitate system UI.", out.getvalue())
            self.assertIn('catalog_id "google:policy:1"', out.getvalue())

    def test_get_star_takes_a_clause_and_its_subclauses(self):
        items = fp.apple_guidelines(APPLE_PAGE)
        with tempfile.TemporaryDirectory() as tmp:
            catalog = Path(tmp) / "c.json"
            catalog.write_text(json.dumps({"checked": "2026-11-18", "items": fp.public(items)}))
            out = io.StringIO()
            with mock.patch.object(fp, "CATALOG", catalog), mock.patch.object(fp, "fetch", return_value=APPLE_PAGE), redirect_stdout(out):
                fp.main(["--get", "apple:1.1*"])
            self.assertIn("=== apple:1.1.1", out.getvalue())
            self.assertIn("=== apple:1.1.2", out.getvalue())
            self.assertNotIn("=== apple:1\n", out.getvalue())

    def test_get_unknown_id_exits_two(self):
        with mock.patch("sys.stderr", io.StringIO()), redirect_stdout(io.StringIO()):
            self.assertEqual(fp.main(["--get", "apple:no-such-clause"]), 2)

    def test_captcha_redirect_fails_without_retrying(self):
        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def geturl(self): return "https://www.google.com/sorry/index?continue=x"
            def read(self): return b"captcha"
        with mock.patch("urllib.request.urlopen", return_value=Resp()) as opened, mock.patch("time.sleep") as slept:
            with self.assertRaises(fp.FetchError):
                fp.fetch_once("https://support.google.com/x")
        self.assertEqual(opened.call_count, 1)
        slept.assert_not_called()

    def test_catalogue_never_stores_policy_text(self):
        self.assertNotIn("_text", fp.public([self.entry("apple:1", "secret text")])[0])


if __name__ == "__main__":
    unittest.main()
