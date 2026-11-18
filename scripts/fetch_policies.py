#!/usr/bin/env python3
"""Build and check the official policy catalogue.

The catalogue (references/policy-catalog.json) lists every clause of the Apple
App Review Guidelines, every page of the Google Play Developer Program Policy
and every topic page in references/sources.md, each with a hash of its
normalised text. It stores no policy text: Apple and Google own that text.

  fetch_policies.py --write   fetch everything and rewrite the catalogue
  fetch_policies.py --check   fetch everything and report changes; exit 1 if any
  exit 2: a source could not be fetched (nothing compared, catalogue untouched)

Full texts go to .policy-cache/ (git-ignored) so a change can be diffed locally.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "references" / "policy-catalog.json"
SOURCES_MD = ROOT / "references" / "sources.md"
CACHE = ROOT / ".policy-cache"

APPLE_GUIDELINES = "https://developer.apple.com/app-store/review/guidelines/"
GOOGLE_POLICY_INDEX = "https://play.google/developer-content-policy/"
GOOGLE_ANSWER = re.compile(r"https://support\.google\.com/googleplay/android-developer/answer/(\d+)")
APPLE_SECTIONS = ("introduction", "before-you-submit", "after-you-submit")
TIMEOUT = 30
RETRIES = 4
PAUSE = 1.0  # between requests to one host; Google answers 429 to a burst of ~60
USER_AGENT = "store-review-audit-policy-check/1.0"


class FetchError(RuntimeError):
    pass


def fetch_once(url: str) -> str:
    last: Exception | None = None
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code not in (429, 500, 502, 503, 504):
                break
            retry_after = exc.headers.get("Retry-After", "")
            time.sleep(int(retry_after) if retry_after.isdigit() else 15 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            time.sleep(5 * (attempt + 1))
    raise FetchError(f"fetch failed after {RETRIES} attempts: {url}: {last}")


META_REFRESH = re.compile(r'(?i)<meta[^>]+http-equiv=["\']?refresh["\']?[^>]+url=([^"\'>]+)')
APPLE_DOC = re.compile(r"^https://developer\.apple\.com/documentation/(.+?)/?$")


def fetch(url: str) -> str:
    """HTTP redirects are followed by urllib; HTML meta refreshes (moved Apple pages) here."""
    for _ in range(3):
        page = fetch_once(url)
        m = META_REFRESH.search(page) if len(page) < 2000 else None
        if not m:
            return page
        url = urllib.parse.urljoin(url, m.group(1).strip())
    return page


def apple_doc_text(url: str) -> str | None:
    """Apple documentation pages render in JavaScript; their content is served as JSON."""
    m = APPLE_DOC.match(url.split("#")[0])
    if not m:
        return None
    data = json.loads(fetch("https://developer.apple.com/tutorials/data/documentation/" + m.group(1).lower() + ".json"))
    words: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key in ("text", "code"):
                if isinstance(node.get(key), str):
                    words.append(node[key])
            for value in node.values():
                if isinstance(value, (dict, list)):
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk([data.get("abstract"), data.get("primaryContentSections")])
    return re.sub(r"\s+", " ", " ".join(words)).strip()


def text_of(fragment: str) -> str:
    fragment = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", " ", fragment)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip()


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def item(item_id: str, platform: str, title: str, url: str, text: str) -> dict:
    return {"id": item_id, "platform": platform, "title": title, "url": url,
            "sha256": digest(text), "words": len(text.split()), "_text": text}


def main_content(page: str) -> str:
    """The first non-empty article or main element; page chrome changes too often to hash.
    A word-count threshold here would let one clause edit move the boundary for all clauses."""
    for start, end in (("<article", "</article>"), ("<main", "</main>")):
        i, j = page.find(start), page.rfind(end)
        if i != -1 and j > i and text_of(page[i:j]):
            return page[i:j]
    return page


def apple_guidelines(page: str) -> list[dict]:
    """One item per numbered clause, plus the unnumbered framing sections."""
    body = main_content(page)
    marks = [(m.start(), m.group(1)) for m in re.finditer(r'id="([0-9]+(?:\.[0-9]+)*|' + "|".join(APPLE_SECTIONS) + r')"', body)]
    items = []
    for n, (pos, anchor) in enumerate(marks):
        # Cut at the start of the tag carrying each id, so a clause keeps its own
        # number and never picks up the next clause's opening tag.
        start = body.rfind("<", 0, pos)
        end = body.rfind("<", 0, marks[n + 1][0]) if n + 1 < len(marks) else len(body)
        text = text_of(body[start:end])
        title = text[:90]
        items.append(item("apple:" + anchor, "apple", title, APPLE_GUIDELINES + "#" + anchor, text))
    return items


def google_page(url: str, page: str) -> str:
    text = text_of(main_content(page))
    # Feedback widget at the end of every help article.
    return re.sub(r"\s*Was this helpful\?.*$", "", text)


def title_of(page: str) -> str:
    m = re.search(r"(?is)<title>(.*?)</title>", page)
    return text_of(m.group(1)) if m else ""


def google_policies(index: str) -> list[dict]:
    items = []
    for answer in sorted(set(GOOGLE_ANSWER.findall(index)), key=int):
        url = f"https://support.google.com/googleplay/android-developer/answer/{answer}?hl=en"
        time.sleep(PAUSE)
        page = fetch(url)
        items.append(item("google:policy:" + answer, "google", title_of(page), url, google_page(url, page)))
    return items


def topic_pages(known_urls: set[str]) -> list[dict]:
    """Every official URL in sources.md not already covered above."""
    urls = sorted(set(re.findall(r"https://[^\s|)]+", SOURCES_MD.read_text(encoding="utf-8"))))
    items = []
    for url in urls:
        base = url.split("#")[0].rstrip("/")
        if base in known_urls:
            continue
        platform = "apple" if "apple.com" in url else "google"
        time.sleep(PAUSE)
        doc = apple_doc_text(url)
        if doc is not None:
            title, text = doc[:90], doc
        else:
            page = fetch(url)
            title, text = title_of(page), google_page(url, page)
        items.append(item("topic:" + re.sub(r"^https://", "", base), platform, title, url, text))
    return items


def build() -> list[dict]:
    items = apple_guidelines(fetch(APPLE_GUIDELINES))
    index = fetch(GOOGLE_POLICY_INDEX)
    items += google_policies(index)
    covered = {APPLE_GUIDELINES.rstrip("/"), GOOGLE_POLICY_INDEX.rstrip("/")}
    covered |= {f"https://support.google.com/googleplay/android-developer/answer/{a}" for a in GOOGLE_ANSWER.findall(index)}
    # Some help-centre answers serve the same article under a second id; keep one.
    seen = {i["sha256"] for i in items}
    items += [t for t in topic_pages(covered) if t["sha256"] not in seen]
    return items


def compare(old: list[dict], new: list[dict]) -> dict:
    before = {i["id"]: i for i in old}
    after = {i["id"]: i for i in new}
    return {
        "added": sorted(after.keys() - before.keys()),
        "removed": sorted(before.keys() - after.keys()),
        "changed": sorted(k for k in before.keys() & after.keys() if before[k]["sha256"] != after[k]["sha256"]),
    }


def save_cache(items: list[dict]) -> None:
    CACHE.mkdir(exist_ok=True)
    for i in items:
        (CACHE / (re.sub(r"[^A-Za-z0-9._-]", "_", i["id"]) + ".txt")).write_text(i["_text"] + "\n", encoding="utf-8")


def public(items: list[dict]) -> list[dict]:
    return [{k: v for k, v in i.items() if not k.startswith("_")} for i in items]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="rewrite the catalogue")
    mode.add_argument("--check", action="store_true", help="report changes against the catalogue")
    parser.add_argument("--date", help="catalogue date, YYYY-MM-DD (default: keep or today)")
    args = parser.parse_args(argv)

    try:
        items = build()
    except FetchError as exc:
        print(f"error\t{exc}", file=sys.stderr)
        return 2
    save_cache(items)
    if args.write:
        date = args.date or time.strftime("%Y-%m-%d")
        CATALOG.write_text(json.dumps({"checked": date, "items": public(items)}, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
        print(f"wrote {len(items)} items to {CATALOG.relative_to(ROOT)}")
        return 0

    old = json.loads(CATALOG.read_text(encoding="utf-8"))["items"]
    diff = compare(old, public(items))
    titles = {i["id"]: i["title"] for i in old + public(items)}
    if not any(diff.values()):
        print(f"no changes in {len(items)} items")
        return 0
    for kind in ("changed", "added", "removed"):
        for key in diff[kind]:
            print(f"{kind}\t{key}\t{titles.get(key, '')[:80]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
