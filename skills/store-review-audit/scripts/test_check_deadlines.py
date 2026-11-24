"""Tests for the deadline list and its source verification."""
import contextlib
import datetime
import io
import json
import re
import unittest
from urllib.parse import urlparse

from check_deadlines import DEADLINES, main, render, select, verify

TODAY = datetime.date(2026, 11, 24)
KEYS = {"id", "date", "date_note", "platform", "jurisdiction", "kind", "title", "applies_to", "action", "source",
        "evidence", "verified_on"}
OFFICIAL = re.compile(r"(^|\.)(apple\.com|google\.com|android\.com|googleblog\.com|play\.google|europa\.eu"
                      r"|gov|gov\.[a-z]{2}|[a-z]{2,3}\.us|go\.jp|go\.kr|gov\.br|gc\.ca|legislature\.[a-z.]+)$")


def entry(item_id, date, platform="both", **more):
    return {"id": item_id, "date": date, "date_note": "", "platform": platform, "jurisdiction": "global",
            "kind": "store", "title": item_id, "applies_to": "who", "action": "do", "source": "https://example.com/" + item_id,
            "evidence": "Starting April 28, 2027, apps must be built with the new SDK.", "verified_on": "2026-11-24", **more}


class SelectTests(unittest.TestCase):
    ITEMS = [entry("late", "2027-04-28", "apple"), entry("past", "2026-08-31", "google"), entry("soon", "2026-12-01")]

    def test_soonest_first_with_days_left(self):
        rows = select(self.ITEMS, TODAY)
        self.assertEqual([(r["id"], r["days_left"]) for r in rows], [("past", -85), ("soon", 7), ("late", 155)])

    def test_platform_keeps_entries_for_both_stores(self):
        self.assertEqual([r["id"] for r in select(self.ITEMS, TODAY, "apple")], ["soon", "late"])
        self.assertEqual([r["id"] for r in select(self.ITEMS, TODAY, "google")], ["past", "soon"])

    def test_within_drops_past_and_far_entries(self):
        self.assertEqual([r["id"] for r in select(self.ITEMS, TODAY, within=30)], ["soon"])

    def test_render_labels_and_stale_warning(self):
        text = render(select(self.ITEMS, TODAY), "2026-11-24", TODAY)
        self.assertIn("2026-08-31  in force", text)
        self.assertIn("2026-12-01  in 7 days", text)
        self.assertIn("in 1 day ", render(select([entry("x", "2026-11-25")], TODAY), "2026-11-24", TODAY))
        self.assertNotIn("days ago", text)
        self.assertIn("That is 61 days ago", render([], "2026-11-24", datetime.date(2027, 1, 24)))


class VerifyTests(unittest.TestCase):
    def run_verify(self, items, pages):
        def fetch_text(url):
            if pages[url] is None:
                raise OSError("timed out")
            return pages[url]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            return verify(items, fetch_text), out.getvalue()

    def test_quote_found_despite_typography_and_spacing(self):
        page = "Upcoming requirements. Starting April 28,\n 2027, apps must be built with the new SDK."
        code, text = self.run_verify([entry("a", "2027-04-28")], {"https://example.com/a": page})
        self.assertEqual((code, text.strip()), (0, "1 of 1 quotes still on their source page"))

    def test_moved_date_is_reported(self):
        page = "Starting June 1, 2027, apps must be built with the new SDK."
        code, text = self.run_verify([entry("a", "2027-04-28")], {"https://example.com/a": page})
        self.assertEqual(code, 1)
        self.assertIn("changed\ta\t2027-04-28\thttps://example.com/a", text)

    def test_empty_quote_is_never_found(self):
        code, text = self.run_verify([entry("a", "2027-04-28", evidence=" ")], {"https://example.com/a": "any page"})
        self.assertEqual(code, 1)

    def test_unreachable_source_does_not_hide_a_changed_one(self):
        items = [entry("a", "2027-04-28"), entry("b", "2027-04-28")]
        code, text = self.run_verify(items, {"https://example.com/a": None, "https://example.com/b": "nothing"})
        self.assertEqual(code, 1)
        self.assertIn("unreachable\ta", text)
        self.assertIn("changed\tb", text)
        self.assertEqual(self.run_verify(items[:1], {"https://example.com/a": None})[0], 2)


class DataTests(unittest.TestCase):
    """The shipped list: shape, official sources and the house rules for policy claims."""

    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DEADLINES.read_text(encoding="utf-8"))

    def test_entries_are_complete_and_unique(self):
        items = self.data["items"]
        self.assertTrue(items)
        self.assertEqual(len({i["id"] for i in items}), len(items))
        for i in items:
            self.assertEqual(set(i), KEYS, i["id"])
            datetime.date.fromisoformat(i["date"])
            datetime.date.fromisoformat(i["verified_on"])
            self.assertIn(i["platform"], ("apple", "google", "both"), i["id"])
            self.assertIn(i["kind"], ("store", "law"), i["id"])
            self.assertLessEqual(len(i["evidence"].split()), 25, i["id"])

    def test_every_source_is_an_official_site(self):
        for i in self.data["items"]:
            url = urlparse(i["source"])
            self.assertEqual(url.scheme, "https", i["id"])
            self.assertTrue(OFFICIAL.search(url.hostname), f"{i['id']}: {url.hostname}")

    def test_text_is_plain_ascii(self):
        self.assertTrue(DEADLINES.read_text(encoding="utf-8").isascii())

    def test_command_lists_every_entry(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(["--json"], today=TODAY), 0)
        self.assertEqual(len(json.loads(out.getvalue())["items"]), len(self.data["items"]))


if __name__ == "__main__":
    unittest.main()
