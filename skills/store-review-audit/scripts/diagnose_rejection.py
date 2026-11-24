#!/usr/bin/env python3
"""List the store rules a rejection or policy notice cites, with their official links.

  diagnose_rejection.py [message file] [--json]     (reads standard input without a file)

Reads the message and the bundled policy catalogue only: nothing is sent anywhere. It finds
the Apple guideline numbers and Google Play policy names the notice names; it does not judge
whether the notice is right. A notice may not list every issue.
Exit 0: at least one rule recognised. 1: none recognised.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REFERENCES = Path(__file__).resolve().parents[1] / "references"
# App Review always cites a dotted number ("Guideline 4.0 - Design"), so "guidelines 3 times" is not a citation
NUMBER = r"[1-5]\.\d{1,2}(?:\.\d{1,2})?(?:\s?\([a-z]{1,4}\))*"
GUIDELINE = re.compile(rf"(?i)\bguidelines?\s+({NUMBER}(?:\s*(?:,|and|&)\s*{NUMBER})*)"
                       rf"|\b(?:section|clause)\s+({NUMBER})\s+of\s+the\s+(?:app\s+store\s+|app\s+)?review\s+guidelines")
CLAUSE = re.compile(r"([1-5]\.\d{1,2}(?:\.\d{1,2})?)((?:\s?\([a-z]{1,4}\))*)")
PLAY_SUFFIX = " - Play Console Help"
# every Play notice names the Developer Program Policies as a whole, which says nothing about the issue
GENERIC = {"google:policy:17190352"}
# names notices use that differ from the page title
ALIASES = {
    "Permissions": "google:policy:12579724",
    "Families": "google:policy:9893335",
    "Target API Level": "google:policy:11917020",
    "Gambling": "google:policy:9877032",
}
# console sections a notice names without the word policy
SECTIONS = {"Data safety": "topic:support.google.com/googleplay/android-developer/answer/10787469"}
MAX_REQUIREMENTS = 5
NEXT_STEPS = (
    "Treat each rule above as its own issue, and recheck the whole app: a notice may not list every issue.",
    "Read the live text before acting: scripts/fetch_policies.py --get <id>.",
    "Choose per issue: fix it, reply with facts the reviewer lacked, or appeal. references/rejection-playbook.md "
    "lists when each applies and the official channel for it.",
)


def line_of(message: str, pos: int) -> str:
    start, end = message.rfind("\n", 0, pos) + 1, message.find("\n", pos)
    return " ".join(message[start:end if end != -1 else len(message)].split())[:200]


def apple_rules(message: str, catalog: dict):
    """(catalogue id, cited form, position) for each guideline number, at the deepest clause the catalogue has."""
    for m in GUIDELINE.finditer(message):
        for clause in CLAUSE.finditer(m.group(1) or m.group(2)):
            number = clause.group(1).removesuffix(".0")
            while number and f"apple:{number}" not in catalog:
                number = number.rpartition(".")[0]
            if number:
                yield f"apple:{number}", clause.group(1) + re.sub(r"\s", "", clause.group(2)), m.start()


def google_rules(message: str, catalog: dict):
    """(catalogue id, cited form, position) for each Play policy named as "<name> policy"."""
    names = {re.sub(r"(?i)\s+polic(y|ies)$", "", item["title"].removesuffix(PLAY_SUFFIX)): item_id
             for item_id, item in catalog.items() if item_id.startswith("google:policy:") and item_id not in GENERIC}
    names.update({name: item_id for name, item_id in ALIASES.items() if item_id in catalog})
    found = [(name, item_id, r"polic(y|ies)") for name, item_id in names.items()]
    found += [(name, item_id, r"(section|form)") for name, item_id in SECTIONS.items() if item_id in catalog]
    for name, item_id, kind in found:
        words = r"\s+".join(re.escape(w) for w in name.split())  # a notice may wrap a policy name across lines
        m = re.search(rf"(?i)\b{words}\s+{kind}\b", message)
        if m:
            yield item_id, " ".join(m.group().split()), m.start()


def diagnose(message: str) -> list:
    catalog = {i["id"]: i for i in json.loads((REFERENCES / "policy-catalog.json").read_text(encoding="utf-8"))["items"]}
    digest = {d["id"]: d for d in json.loads((REFERENCES / "policy-digest.json").read_text(encoding="utf-8"))}
    cited = {}
    for item_id, form, pos in sorted([*apple_rules(message, catalog), *google_rules(message, catalog)], key=lambda r: r[2]):
        entry = cited.setdefault(item_id, {
            "id": item_id, "cited_as": [], "title": catalog[item_id]["title"].removesuffix(PLAY_SUFFIX)[:70],
            "url": catalog[item_id]["url"], "quote": line_of(message, pos),
            # the digest is only valid while its hash matches the catalogue
            "requirements": digest[item_id]["requirements"]
            if item_id in digest and digest[item_id]["sha256"] == catalog[item_id]["sha256"] else []})
        if form not in entry["cited_as"]:
            entry["cited_as"].append(form)
    return list(cited.values())


def render(cited: list) -> str:
    if not cited:
        return ("No Apple guideline number or Google Play policy name was recognised. Paste the full message, "
                "including the lines that name the guideline or policy.")
    out = []
    for c in cited:
        out += [f"{c['id']}  (cited as {', '.join(c['cited_as'])})", f"  title  {c['title']}", f"  url    {c['url']}",
                f"  notice {c['quote']}"]
        shown = c["requirements"][:MAX_REQUIREMENTS]
        out += [f"  rule   {r}" for r in shown]
        if len(c["requirements"]) > len(shown):
            out.append(f"  rule   ... {len(c['requirements']) - len(shown)} more on the page")
        out.append("")
    out += ["Next steps:"] + [f"  {n}. {step}" for n, step in enumerate(NEXT_STEPS, 1)]
    return "\n".join(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("message", nargs="?", type=Path, help="file with the notice text; standard input when omitted")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args(argv)
    try:
        raw = args.message.read_bytes() if args.message else sys.stdin.buffer.read()
        message = raw.decode("utf-8", errors="ignore")
    except OSError as exc:
        print(f"Cannot read the message: {exc}", file=sys.stderr)
        return 1
    cited = diagnose(message)
    print(json.dumps({"cited": cited, "next_steps": list(NEXT_STEPS)}, indent=2) if args.json else render(cited))
    return 0 if cited else 1


if __name__ == "__main__":
    sys.exit(main())
