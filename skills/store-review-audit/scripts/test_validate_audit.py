#!/usr/bin/env python3
"""Synthetic regression tests for the evidence gate; no live app data."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import validate_audit
from datetime import date
from validate_audit import validate, RULES

def fixture(platform="apple"):
    today = date.today().isoformat()
    rules = [r for r in json.loads(RULES.read_text())["rules"] if r["platform"] in {"all", platform}]
    evidences = [
        {"id": k, "kind": k, "location": "synthetic fixture only", "observed": "synthetic observation",
         "checked_at": today, "app_id": "test.app", "platform": platform, "build": "42", "commit": "abc123"}
        for k in ["runtime", "console", "code", "artifact", "document"]
    ]
    evidences[0].update(environment="Synthetic device/OS", steps="Synthetic steps",
                        expected="Synthetic expected outcome", actual="Synthetic actual outcome", outcome="PASS")
    return {
        "scope": {"app_id": "test.app", "platform": platform, "build": "42", "commit": "abc123",
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
        control(self.d,"C04").update(status="FAIL",severity="MEDIUM",finding="Listing claims a feature the build lacks",fix="Correct listing",retest="Reopen listing")
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
    def test_failure_without_observation(self):
        control(self.d,"C04").update(status="FAIL",severity="MEDIUM",fix="Correct listing",retest="Reopen listing")
        self.assertEqual(validate(self.d)["verdict"],"INVALID")
    def test_code_read_at_another_commit(self):
        self.d["evidence"][2]["commit"]="def456"
        self.rejected()
    def test_code_without_commit(self):
        del self.d["evidence"][2]["commit"]
        self.rejected()
    def test_backend_code_names_its_repo(self):
        self.d["evidence"][2].update(repo="example/backend", commit="999fff")
        self.assertEqual(validate(self.d)["verdict"],"EVIDENCE_CONTRACT_COMPLETE")
    def test_unknown_territories_are_a_gap(self):
        self.d["scope"]["territories"]=["UNKNOWN"]
        r=validate(self.d)
        self.assertEqual(r["verdict"],"INCOMPLETE")
        self.assertIn("scope.territories: not established", r["gaps"])
    def test_no_policy_records_is_a_gap(self):
        for c in self.d["controls"]:
            c.update(status="UNKNOWN",missing_evidence="x",next_action="y")
        self.d["policies"]=[]
        self.assertIn("No official policy was recorded as checked during this audit", validate(self.d)["gaps"])
    def test_verified_no_third_party_login_is_na(self):
        self.d["features"]["third_party_login"]={"value":False,"evidence":["code"]}
        control(self.d,"A03").update(status="N/A",reason="Only email sign-in in the inspected build")
        self.assertEqual(validate(self.d)["verdict"],"EVIDENCE_CONTRACT_COMPLETE")
    def test_empty_observed_pass(self):
        control(self.d,"C11")["result"]=" "
        self.rejected()

class PolicySourceTests(unittest.TestCase):
    """Policy records that rest on the digest or on a store review message."""
    URL = "https://support.google.com/googleplay/android-developer/answer/9857753?hl=en"

    def setUp(self):
        self.d = fixture("google")
        self.tmp = tempfile.TemporaryDirectory()
        tmp = Path(self.tmp.name)
        self.catalog, self.digest = tmp / "catalog.json", tmp / "digest.json"
        self.write(checked=date.today().isoformat(), catalog_sha="aaa", digest_sha="aaa")
        self.patches = [mock.patch.object(validate_audit, "CATALOG", self.catalog), mock.patch.object(validate_audit, "DIGEST", self.digest)]
        for p in self.patches: p.start()
        self.d["policies"] = [{"id": "policy", "url": self.URL, "section": "Ads: interstitial timing", "checked_at": date.today().isoformat(),
                               "effective": "current", "via": "digest", "catalog_id": "google:policy:9857753"}]

    def tearDown(self):
        for p in self.patches: p.stop()
        self.tmp.cleanup()

    def write(self, checked, catalog_sha, digest_sha):
        self.catalog.write_text(json.dumps({"checked": checked, "items": [{"id": "google:policy:9857753", "sha256": catalog_sha, "url": self.URL}]}))
        self.digest.write_text(json.dumps([{"id": "google:policy:9857753", "sha256": digest_sha, "url": self.URL, "requirements": ["x"]}]))

    def test_current_digest_supports_a_policy_record(self):
        self.assertEqual(validate(self.d)["verdict"], "EVIDENCE_CONTRACT_COMPLETE")

    def test_digest_written_for_an_older_page_is_rejected(self):
        self.write(checked=date.today().isoformat(), catalog_sha="bbb", digest_sha="aaa")
        self.assertEqual(validate(self.d)["verdict"], "INVALID")

    def test_stale_catalogue_is_rejected(self):
        self.write(checked="2020-01-01", catalog_sha="aaa", digest_sha="aaa")
        self.assertEqual(validate(self.d)["verdict"], "INVALID")

    def test_review_message_can_back_a_failure(self):
        d = fixture("apple")
        d["evidence"].append({"id": "msg", "kind": "message", "location": "review-message.txt", "observed": "3.1.2 EULA missing",
                              "checked_at": date.today().isoformat(), "app_id": "test.app", "platform": "apple"})
        d["policies"].append({"id": "review", "message_evidence": "msg", "section": "Guideline 3.1.2 as cited in the message",
                              "checked_at": date.today().isoformat(), "effective": "current"})
        control(d, "A01").update(status="FAIL", severity="BLOCKER", finding="de-DE description has no EULA link", policies=["review"], fix="Add link", retest="Reopen")
        self.assertEqual(validate(d)["verdict"], "BLOCKED")

    def test_message_policy_must_point_at_a_message(self):
        d = fixture("apple")
        d["policies"].append({"id": "review", "message_evidence": "document", "section": "3.1.2", "checked_at": date.today().isoformat(), "effective": "current"})
        control(d, "A01").update(policies=["review"])
        self.assertEqual(validate(d)["verdict"], "INVALID")


if __name__ == "__main__":
    unittest.main(verbosity=2)
