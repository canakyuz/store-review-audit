#!/usr/bin/env python3
"""Synthetic regression tests for the evidence gate; no live app data."""
import copy
import json
import unittest
from datetime import date
from validate_audit import validate, RULES

def fixture(platform="apple"):
    today = date.today().isoformat()
    rules = [r for r in json.loads(RULES.read_text())["rules"] if r["platform"] in {"all", platform}]
    evidences = [
        {"id": k, "kind": k, "location": "synthetic fixture only", "observed": "synthetic observation",
         "checked_at": today, "app_id": "test.app", "platform": platform, "build": "42"}
        for k in ["runtime", "console", "code", "artifact", "document"]
    ]
    evidences[0].update(environment="Synthetic device/OS", steps="Synthetic steps",
                        expected="Synthetic expected outcome", actual="Synthetic actual outcome", outcome="PASS")
    return {
        "scope": {"app_id": "test.app", "platform": platform, "build": "42",
                  "audit_date": today, "account_type": "organization",
                  "locales": ["en-GB", "tr"], "territories": ["GB", "TR"]},
        "features": {r["feature"]: {"value": True, "evidence": ["runtime"]} for r in rules if r["feature"]},
        "evidence": evidences,
        "policies": [{"id": "policy", "url": "https://developer.apple.com/app-store/review/guidelines/" if platform == "apple" else "https://play.google/developer-content-policy/",
                      "section": "Synthetic test reference", "checked_at": today, "effective": "current"}],
        "controls": [{"id": r["id"], "status": "PASS", "evidence": [e["id"] for e in evidences],
                      "policies": ["policy"], "result": "Synthetic passed observation",
                      "locales_verified": ["en-GB", "tr"]} for r in rules],
        "rejections": [],
    }

def control(d, cid):
    return next(c for c in d["controls"] if c["id"] == cid)

class GateTests(unittest.TestCase):
    def setUp(self):
        self.d = fixture()
    def rejected(self, d=None):
        self.assertNotEqual(validate(d or self.d)["verdict"], "EVIDENCE_CONTRACT_COMPLETE")
    def test_complete_synthetic_apple(self):
        self.assertEqual(validate(self.d)["verdict"], "EVIDENCE_CONTRACT_COMPLETE")
    def test_complete_synthetic_google(self):
        self.assertEqual(validate(fixture("google"))["verdict"], "EVIDENCE_CONTRACT_COMPLETE")
    def test_missing_check_is_incomplete(self):
        self.d["controls"].pop()
        self.assertEqual(validate(self.d)["verdict"], "INCOMPLETE")
    def test_only_english_eula(self):
        control(self.d,"A01")["locales_verified"]=["en-GB"]
        self.rejected()
    def test_old_build_runtime(self):
        self.d["evidence"][0]["build"]="41"
        self.rejected()
    def test_other_app_evidence(self):
        self.d["evidence"][0]["app_id"]="other.app"
        self.rejected()
    def test_ios_evidence_for_android(self):
        d=fixture("google"); d["evidence"][0]["platform"]="apple"
        self.rejected(d)
    def test_missing_purchase_runtime(self):
        control(self.d,"C11")["evidence"]=["console","code"]
        self.rejected()
    def test_developer_assertion_is_not_verified(self):
        self.d["evidence"][0]["kind"]="user_assertion"
        self.rejected()
    def test_absent_feature_without_evidence(self):
        self.d["features"]["ads"]={"value":False,"evidence":[]}
        control(self.d,"C13").update(status="N/A",reason="No ads")
        self.rejected()
    def test_unknown_feature_cannot_pass(self):
        self.d["features"]["ads"]["value"]=None
        self.rejected()
    def test_unknown_is_incomplete_not_violation(self):
        control(self.d,"C11").update(status="UNKNOWN",missing_evidence="Runtime",next_action="Run purchase")
        r=validate(self.d)
        self.assertEqual(r["verdict"],"INCOMPLETE")
        self.assertFalse(r["failed_controls"])
    def test_verified_nonapplicability(self):
        self.d["features"]["ads"]["value"]=False
        control(self.d,"C13").update(status="N/A",reason="Inspected build has no ads")
        self.assertEqual(validate(self.d)["verdict"],"EVIDENCE_CONTRACT_COMPLETE")
    def test_medium_failure_still_blocks(self):
        control(self.d,"C04").update(status="FAIL",severity="MEDIUM",fix="Correct listing",retest="Reopen listing")
        self.assertEqual(validate(self.d)["verdict"],"BLOCKED")
    def test_unresolved_rejection(self):
        self.d["rejections"]=[{"id":"R1","text":"EULA missing","control_id":"A01","state":"unresolved"}]
        self.assertEqual(validate(self.d)["verdict"],"INCOMPLETE")
    def test_claimed_resolution_without_pass(self):
        self.d["rejections"]=[{"id":"R1","text":"EULA missing","control_id":"A01","state":"resolved"}]
        control(self.d,"A01").update(status="UNKNOWN",missing_evidence="Locales",next_action="Inspect")
        self.rejected()
    def test_duplicate_control(self):
        self.d["controls"].append(copy.deepcopy(self.d["controls"][0]))
        self.rejected()
    def test_unofficial_policy(self):
        self.d["policies"][0]["url"]="https://developer.apple.com.attacker.example/policy"
        self.rejected()
    def test_future_rule_not_current(self):
        self.d["policies"][0]["effective"]="future"
        self.rejected()
    def test_stale_policy(self):
        self.d["policies"][0]["checked_at"]="2020-01-01"
        self.rejected()
    def test_subscription_purchase_contradiction(self):
        self.d["features"]["purchases"]["value"]=False
        control(self.d,"C11").update(status="N/A",reason="No purchases")
        self.rejected()
    def test_google_deletion_without_runtime(self):
        d=fixture("google"); control(d,"G03")["evidence"]=["document","console"]
        self.rejected(d)
    def test_missing_rejection_inventory(self):
        del self.d["rejections"]
        self.rejected()
    def test_failed_runtime_cannot_support_pass(self):
        self.d["evidence"][0]["outcome"]="FAIL"
        self.rejected()
    def test_missing_runtime_steps(self):
        del self.d["evidence"][0]["steps"]
        self.rejected()
    def test_missing_runtime_actual_result(self):
        self.d["evidence"][0]["actual"]=" "
        self.rejected()
    def test_unknown_account(self):
        self.d["scope"]["account_type"]="unknown"
        self.assertEqual(validate(self.d)["verdict"],"INCOMPLETE")
    def test_baseline_cannot_be_na(self):
        control(self.d,"C06").update(status="N/A",reason="No login")
        self.rejected()
    def test_user_supplied_verdict_ignored(self):
        self.d["verdict"]="READY"
        self.d["controls"].pop()
        self.assertEqual(validate(self.d)["verdict"],"INCOMPLETE")
    def test_empty_observed_pass(self):
        control(self.d,"C11")["result"]=" "
        self.rejected()

if __name__ == "__main__":
    unittest.main(verbosity=2)
