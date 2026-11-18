#!/usr/bin/env python3
"""Validate an audit's coverage and evidence contract, never store compliance itself."""
import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

RULES = Path(__file__).resolve().parents[1] / "references" / "rules.json"
KINDS = {"runtime", "console", "code", "artifact", "document"}
OFFICIAL = {
    "apple": {"developer.apple.com", "apple.com", "www.apple.com", "support.apple.com"},
    "google": {"developer.android.com", "developers.google.com", "support.google.com", "play.google.com", "play.google"},
}

def validate(data):
    errors, gaps, failures = [], [], []
    if not isinstance(data, dict):
        return {"verdict": "INVALID", "errors": ["Audit must be an object."]}
    def error(message):
        errors.append(message)
    def index(items, label):
        result = {}
        if not isinstance(items, list):
            error(f"{label}: expected list")
            return result
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
                error(f"{label}: each record needs an ID")
                continue
            if item["id"] in result:
                error(f"{label}: duplicate ID {item['id']}")
            result[item["id"]] = item
        return result
    scope = data.get("scope", {})
    if not isinstance(scope, dict):
        scope = {}
    for key in ("app_id", "build", "platform", "audit_date", "account_type"):
        if not isinstance(scope.get(key), str) or not scope[key].strip():
            error(f"scope.{key}: required nonempty string")
    platform = scope.get("platform")
    if platform not in OFFICIAL:
        error("scope.platform: use apple or google; separate platform reports")
    try:
        if date.fromisoformat(scope["audit_date"]) > date.today():
            error("audit_date cannot be in the future")
    except (ValueError, KeyError, TypeError):
        error("audit_date: require YYYY-MM-DD")
    for key in ("locales", "territories"):
        value = scope.get(key)
        if not isinstance(value, list) or not value or any(not isinstance(x, str) or not x for x in value):
            error(f"scope.{key}: require nonempty string list")
        elif len(set(value)) != len(value):
            error(f"scope.{key}: duplicates")
        elif "UNKNOWN" in value:
            gaps.append(f"scope.{key}: not established")
    if scope.get("account_type") not in {"individual", "organization", "unknown"}:
        error("account_type: individual, organization or unknown")
    if scope.get("account_type") == "unknown":
        gaps.append("Publisher account type is unknown")
    evidence = index(data.get("evidence"), "evidence")
    policies = index(data.get("policies"), "policies")
    controls = index(data.get("controls"), "controls")
    def evidence_for(refs, where):
        found = []
        if not isinstance(refs, list) or not refs:
            error(f"{where}: evidence references required")
            return found
        for ref in refs:
            if not isinstance(ref, str) or ref not in evidence:
                error(f"{where}: unknown evidence reference")
                continue
            ev = evidence[ref]
            valid = True
            for key in ("kind", "location", "observed", "checked_at", "app_id", "platform"):
                if not isinstance(ev.get(key), str) or not ev[key].strip():
                    error(f"{where}/{ref}: missing {key}")
                    valid = False
            if ev.get("kind") not in KINDS:
                error(f"{where}/{ref}: self-report or unsupported evidence cannot establish PASS")
                valid = False
            if ev.get("app_id") != scope.get("app_id") or ev.get("platform") != platform:
                error(f"{where}/{ref}: wrong app/platform")
                valid = False
            if ev.get("checked_at") != scope.get("audit_date"):
                error(f"{where}/{ref}: evidence must be rechecked during this audit")
                valid = False
            if ev.get("kind") in {"runtime", "artifact"} and ev.get("build") != scope.get("build"):
                error(f"{where}/{ref}: wrong or absent build")
                valid = False
            # Code is bound to the build through its commit. Code from another
            # repository (a backend) names that repo and its own commit.
            if ev.get("kind") == "code":
                if not isinstance(ev.get("commit"), str) or not ev["commit"].strip():
                    error(f"{where}/{ref}: code evidence needs the commit it was read at")
                    valid = False
                elif not ev.get("repo") and ev["commit"] != scope.get("commit"):
                    error(f"{where}/{ref}: app code must be read at scope.commit, the commit of the audited build")
                    valid = False
            if ev.get("kind") == "runtime":
                for key in ("environment", "steps", "expected", "actual"):
                    if not isinstance(ev.get(key), str) or not ev[key].strip():
                        error(f"{where}/{ref}: runtime {key} required")
                        valid = False
                if ev.get("outcome") not in {"PASS", "FAIL"}:
                    error(f"{where}/{ref}: runtime outcome must be PASS or FAIL")
                    valid = False
            if valid:
                found.append(ev)
        return found
    def policy_for(refs, where):
        if not isinstance(refs, list) or not refs:
            error(f"{where}: current official policy references required")
            return
        for ref in refs:
            if not isinstance(ref, str) or ref not in policies:
                error(f"{where}: unknown policy reference")
                continue
            p = policies[ref]
            u = urlparse(p.get("url", "") if isinstance(p.get("url"), str) else "")
            if u.scheme != "https" or u.hostname not in OFFICIAL.get(platform, set()):
                error(f"{where}/{ref}: official platform source required")
            if p.get("checked_at") != scope.get("audit_date"):
                error(f"{where}/{ref}: policy must be checked during this audit")
            if p.get("effective") != "current" or not p.get("section"):
                error(f"{where}/{ref}: verify active rule and exact section")
    features = data.get("features", {})
    if not isinstance(features, dict):
        features = {}
        error("features: expected object")
    required = [r for r in json.loads(RULES.read_text())["rules"] if r["platform"] in {"all", platform}]
    known_ids = {r["id"] for r in required}
    for cid in set(controls) - known_ids:
        error(f"{cid}: unknown or wrong-platform control")
    for r in required:
        cid, feature = r["id"], r["feature"]
        applicable = True
        if feature:
            f = features.get(feature, {})
            if not isinstance(f, dict):
                f = {}
            value = f.get("value")
            if value is not True and value is not False:
                applicable = None
                gaps.append(f"{cid}: applicability of {feature} unknown")
            else:
                applicable = value
                evidence_for(f.get("evidence"), f"feature.{feature}")
        c = controls.get(cid)
        if not c:
            gaps.append(f"{cid}: omitted control")
            continue
        status = c.get("status")
        if status not in {"PASS", "FAIL", "UNKNOWN", "N/A"}:
            error(f"{cid}: invalid status")
            continue
        if applicable is None and status != "UNKNOWN":
            error(f"{cid}: unresolved applicability requires UNKNOWN")
        if applicable is False and status != "N/A":
            error(f"{cid}: confirmed absent feature requires N/A")
        if status == "UNKNOWN":
            gaps.append(f"{cid}: unverified")
            if not c.get("missing_evidence") or not c.get("next_action"):
                error(f"{cid}: identify missing evidence and next action")
            continue
        if status == "N/A":
            if applicable is not False or not c.get("reason"):
                error(f"{cid}: N/A requires verified absent feature and reason")
            continue
        evs = evidence_for(c.get("evidence"), cid)
        policy_for(c.get("policies"), cid)
        if status == "FAIL":
            failures.append(cid)
            if not isinstance(c.get("finding"), str) or not c["finding"].strip():
                error(f"{cid}: failing observation (finding) required")
            if c.get("severity") not in {"BLOCKER", "HIGH", "MEDIUM"}:
                error(f"{cid}: failure severity required")
            if not c.get("fix") or not c.get("retest"):
                error(f"{cid}: fix and retest required")
        if status == "PASS":
            if not isinstance(c.get("result"), str) or not c["result"].strip():
                error(f"{cid}: observed result required")
            if any(ev.get("kind") == "runtime" and ev.get("outcome") != "PASS" for ev in evs):
                error(f"{cid}: failed runtime evidence cannot support PASS")
            kinds = {ev["kind"] for ev in evs}
            for group in r["evidence_groups"]:
                if not kinds.intersection(group):
                    error(f"{cid}: missing evidence kind from {group}")
            if r["all_locales"]:
                locales = c.get("locales_verified", [])
                if not isinstance(locales, list) or set(locales) != set(scope.get("locales", [])):
                    error(f"{cid}: all configured locales must be verified")
    if not policies:
        gaps.append("No official policy was recorded as checked during this audit")
    subs = features.get("subscriptions", {})
    purchases = features.get("purchases", {})
    if isinstance(subs, dict) and isinstance(purchases, dict) and subs.get("value") is True and purchases.get("value") is not True:
        error("Subscriptions require purchases=true")
    incidents = data.get("rejections")
    if not isinstance(incidents, list):
        error("rejections: explicit list required, even when empty")
    else:
        for incident in incidents:
            if not isinstance(incident, dict) or not incident.get("id") or not incident.get("text"):
                error("Each rejection issue needs ID and text")
                continue
            cid = incident.get("control_id")
            if cid not in known_ids:
                error("Each rejection issue must map to a control")
            if incident.get("state") != "resolved":
                gaps.append(f"Rejection {incident['id']} remains unresolved")
            elif controls.get(cid, {}).get("status") != "PASS":
                error(f"Rejection {incident['id']}: resolution requires verified PASS")
    verdict = "INVALID" if errors else "BLOCKED" if failures else "INCOMPLETE" if gaps else "EVIDENCE_CONTRACT_COMPLETE"
    return {
        "verdict": verdict, "errors": errors, "gaps": gaps, "failed_controls": failures,
        "required_controls": len(required), "reported_controls": len(controls),
        "notice": "This validates report structure and claimed evidence coverage only. It cannot authenticate evidence, determine policy applicability, or guarantee store approval."
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path)
    args = parser.parse_args()
    try:
        result = validate(json.loads(args.audit.read_text()))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result = {"verdict": "INVALID", "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["verdict"] == "EVIDENCE_CONTRACT_COMPLETE" else 1

if __name__ == "__main__":
    raise SystemExit(main())
