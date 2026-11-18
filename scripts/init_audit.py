#!/usr/bin/env python3
"""Create an audit ledger with every check unknown; never invent evidence."""
import argparse
import json
from datetime import date
from pathlib import Path

RULES = Path(__file__).resolve().parents[1] / "references" / "rules.json"

def make_audit(platform, app_id, build, locales, territories):
    if platform not in {"apple", "google"}:
        raise ValueError("platform must be apple or google")
    if not app_id.strip() or not build.strip():
        raise ValueError("app_id and build must be nonempty")
    if not locales or not territories or any(not x.strip() for x in locales + territories):
        raise ValueError("at least one locale and territory is required")
    rules = [r for r in json.loads(RULES.read_text())["rules"] if r["platform"] in {"all", platform}]
    return {
        "scope": {"app_id": app_id, "platform": platform, "build": build,
                  "audit_date": date.today().isoformat(), "account_type": "unknown",
                  "locales": list(dict.fromkeys(locales)), "territories": list(dict.fromkeys(territories))},
        "features": {r["feature"]: {"value": None, "evidence": []} for r in rules if r["feature"]},
        "evidence": [], "policies": [],
        "controls": [{"id": r["id"], "status": "UNKNOWN",
                      "missing_evidence": "Current app, console and policy evidence for: " + r["title"],
                      "next_action": "Inspect applicability and collect evidence under strict-mode.md."} for r in rules],
        "rejections": [],
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--platform", required=True, choices=["apple", "google"])
    p.add_argument("--app-id", required=True)
    p.add_argument("--build", required=True)
    p.add_argument("--locales", required=True, nargs="+")
    p.add_argument("--territories", required=True, nargs="+")
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    try:
        data = make_audit(a.platform, a.app_id, a.build, a.locales, a.territories)
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with a.output.open("x", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
    except (OSError, ValueError) as exc:
        p.exit(1, str(exc) + "\n")
    print(f"Created {a.output}; every control is UNKNOWN.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
