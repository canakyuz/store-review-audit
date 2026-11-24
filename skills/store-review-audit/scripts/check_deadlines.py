#!/usr/bin/env python3
"""List dated store and legal deadlines that affect App Store and Google Play releases.

  check_deadlines.py [--platform apple|google] [--within DAYS] [--json]
  check_deadlines.py --verify

Every entry in references/deadlines.json carries its official source and a short quote from it.
The list is not complete and a date can move: open the source before relying on one.
--verify fetches each source and reports entries whose quote is no longer on the page.
Exit 0: listed, or every quote still found. 1: a quote is gone. 2: a source could not be fetched.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import time
from pathlib import Path

DEADLINES = Path(__file__).resolve().parents[1] / "references" / "deadlines.json"
STALE_DAYS = 30  # the weekly watch re-verifies; a copy older than this missed several runs
# typographic quotes and dashes on the page compared as their ASCII forms
ASCII = {0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"', 0x2013: "-", 0x2014: "-", 0x00A0: " "}


def normal(text: str) -> str:
    return re.sub(r"\s+", " ", text.translate(ASCII)).strip().lower()


def load() -> dict:
    return json.loads(DEADLINES.read_text(encoding="utf-8"))


def select(items: list, today: datetime.date, platform: str | None = None, within: int | None = None) -> list:
    """Entries for the platform, soonest first, each with days_left (negative once in force)."""
    out = []
    for item in items:
        days = (datetime.date.fromisoformat(item["date"]) - today).days
        if platform in (None, item["platform"]) or item["platform"] == "both":
            if within is None or 0 <= days <= within:
                out.append({**item, "days_left": days})
    return sorted(out, key=lambda i: i["date"])


def render(rows: list, verified: str, today: datetime.date) -> str:
    out = []
    for r in rows:
        when = f"in {r['days_left']} day{'s' * (r['days_left'] != 1)}" if r["days_left"] > 0 else "today" if r["days_left"] == 0 else "in force"
        note = f" ({r['date_note']})" if r["date_note"] else ""
        out += [f"{r['date']}  {when:<12} {r['platform']:<6} {r['jurisdiction']:<7} {r['title']}{note}",
                f"            who   {r['applies_to']}", f"            do    {r['action']}",
                f"            src   {r['source']}", ""]
    age = (today - datetime.date.fromisoformat(verified)).days
    out.append(f"{len(rows)} entries. Sources last verified {verified}. The list is not complete and dates can "
               "move: open the source before relying on one.")
    if age > STALE_DAYS:
        out.append(f"That is {age} days ago: update the skill or run check_deadlines.py --verify.")
    return "\n".join(out)


def verify(items: list, fetch_text) -> int:
    """Check each quote against its source. fetch_text(url) returns page text or raises."""
    gone = failed = 0
    for item in items:
        try:
            quote = normal(item["evidence"])
            found = bool(quote) and quote in normal(fetch_text(item["source"]))
        except Exception as exc:  # one unreachable source must not hide the others
            failed += 1
            print(f"unreachable\t{item['id']}\t{item['source']}\t{exc}")
            continue
        if not found:
            gone += 1
            print(f"changed\t{item['id']}\t{item['date']}\t{item['source']}")
    print(f"{len(items) - gone - failed} of {len(items)} quotes still on their source page")
    return 1 if gone else 2 if failed else 0


def page_text(url: str) -> str:
    import fetch_policies as fp  # network code stays out of the listing path
    time.sleep(fp.PAUSE)
    return fp.apple_doc_text(url) or fp.text_of(fp.fetch(url))


def main(argv=None, today: datetime.date | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--platform", choices=("apple", "google"), help="only entries for this store")
    parser.add_argument("--within", type=int, metavar="DAYS", help="only entries due in the next DAYS days")
    parser.add_argument("--json", action="store_true", help="print the entries as JSON")
    parser.add_argument("--verify", action="store_true", help="check every quote against its live source")
    args = parser.parse_args(argv)
    data = load()
    if args.verify:
        return verify(data["items"], page_text)
    today = today or datetime.date.today()
    rows = select(data["items"], today, args.platform, args.within)
    print(json.dumps({"verified": data["verified"], "items": rows}, indent=2) if args.json
          else render(rows, data["verified"], today))
    return 0


if __name__ == "__main__":
    sys.exit(main())
