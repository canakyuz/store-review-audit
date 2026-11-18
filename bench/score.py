#!/usr/bin/env python3
"""Score an audit of the Coin Quiz fixture against bench/expected.json.

  score.py <apple.json> <google.json>

Prints one line per check and exits 0 only when every seeded issue was caught,
no trap was failed, every feature answer matches and the validator found no
contract errors.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "skills" / "store-review-audit" / "scripts"))
from validate_audit import validate  # noqa: E402


def score(platform: str, ledger: dict, key: dict) -> list[tuple[bool, str]]:
    status = {c.get("id"): c.get("status") for c in ledger.get("controls", [])}
    features = {k: (v or {}).get("value") for k, v in ledger.get("features", {}).items()}
    lines = []
    verdict = validate(ledger)
    lines.append((not verdict["errors"], f"{platform} validator: {verdict['verdict']}, {len(verdict['errors'])} contract errors"))
    for s in key["seeded"]:
        hit = any(status.get(c) == "FAIL" for c in s["controls"])
        got = ", ".join(f"{c}={status.get(c)}" for c in s["controls"])
        lines.append((hit, f"{platform} seeded {s['id']}: {got}"))
    for t in key["traps"]:
        ok = status.get(t["control"]) != "FAIL"
        lines.append((ok, f"{platform} trap {t['control']}: {status.get(t['control'])}"))
    for name, want in key["features"].items():
        lines.append((features.get(name) == want, f"{platform} feature {name}: {features.get(name)} (expected {want})"))
    for r in key["rejections"]:
        found = [x for x in ledger.get("rejections", []) if x.get("control_id") == r["control"] and x.get("state") == r["state"]]
        lines.append((bool(found), f"{platform} rejection mapped to {r['control']} as {r['state']}"))
    return lines


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    key = json.loads((HERE / "expected.json").read_text())
    results = []
    for platform, path in zip(("apple", "google"), argv):
        results += score(platform, json.loads(Path(path).read_text()), key[platform])
    for ok, text in results:
        print(("ok   " if ok else "MISS ") + text)
    seeded = [r for r in results if " seeded " in r[1]]
    traps = [r for r in results if " trap " in r[1]]
    print(f"seeded caught {sum(ok for ok, _ in seeded)}/{len(seeded)}, traps clean {sum(ok for ok, _ in traps)}/{len(traps)}, "
          f"all checks {sum(ok for ok, _ in results)}/{len(results)}")
    return 0 if all(ok for ok, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
