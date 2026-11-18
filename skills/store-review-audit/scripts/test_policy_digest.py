#!/usr/bin/env python3
"""The digest must describe the pages as the catalogue last saw them."""
import json
import unittest
from pathlib import Path

REFS = Path(__file__).resolve().parents[1] / "references"


class DigestTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {i["id"]: i for i in json.loads((REFS / "policy-catalog.json").read_text())["items"]}
        self.digest = json.loads((REFS / "policy-digest.json").read_text())

    def test_every_digest_entry_matches_the_current_catalogue(self):
        stale = [d["id"] for d in self.digest if self.catalog.get(d["id"], {}).get("sha256") != d["sha256"]]
        self.assertEqual(stale, [], "rewrite these digest entries after the policy change")

    def test_every_google_page_has_a_digest_entry(self):
        google = {k for k, v in self.catalog.items() if v["platform"] == "google"}
        self.assertEqual(sorted(google - {d["id"] for d in self.digest}), [])

    def test_entries_point_at_the_catalogue_url(self):
        for d in self.digest:
            self.assertEqual(d["url"], self.catalog[d["id"]]["url"], d["id"])


if __name__ == "__main__":
    unittest.main()
