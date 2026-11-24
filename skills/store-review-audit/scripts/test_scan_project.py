"""Tests for the file-only project scanner."""
import contextlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path

from scan_project import CATALOG, main, scan

REPO = Path(__file__).resolve().parents[3]
BENCH = REPO / "bench"
EXPO = {"package.json": '{"dependencies": {"expo": "56.0.0", "react-native": "0.86.3"}}'}


def scan_files(files: dict):
    """Scan a throwaway project made of {relative path: content}."""
    with tempfile.TemporaryDirectory() as folder:
        for rel, content in files.items():
            path = Path(folder, rel)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        return scan(Path(folder))


def controls(report, platform=None, severity=None):
    return {f["control"] for f in report["findings"]
            if (platform is None or f["platform"] in ("all", platform)) and severity in (None, f["severity"])}


class BenchTests(unittest.TestCase):
    """Coin Quiz: what a scan of the files alone finds, and what it must leave alone."""

    @classmethod
    def setUpClass(cls):
        cls.report = scan(BENCH / "coin-quiz")
        cls.key = json.loads((BENCH / "expected.json").read_text())

    def flagged(self, platform):
        found = controls(self.report, platform)
        return [s["id"] for s in self.key[platform]["seeded"] if found & set(s["controls"])]

    def test_seeded_issues_visible_in_files(self):
        self.assertEqual(self.flagged("apple"), ["A-LOGIN", "A-DELETE", "A-PRIVACY", "A-GAMBLING", "A-PAYWALL"])
        self.assertEqual(self.flagged("google"), ["G-DELETE-APP", "G-PERMISSIONS", "G-GAMBLING", "G-PAYWALL"])

    def test_no_trap_is_flagged(self):
        for platform in ("apple", "google"):
            traps = {t["control"] for t in self.key[platform]["traps"]}
            self.assertFalse(traps & controls(self.report, platform))

    def test_every_reference_is_in_the_policy_catalogue(self):
        ids = {item["id"] for item in json.loads(CATALOG.read_text())["items"]}
        refs = {ref for f in self.report["findings"] for ref in f["refs"]}
        self.assertTrue(refs)
        self.assertFalse(refs - ids)

    def test_every_reference_in_the_source_is_in_the_policy_catalogue(self):
        ids = {item["id"] for item in json.loads(CATALOG.read_text())["items"]}
        source = Path(__file__).with_name("scan_project.py").read_text()
        refs = set(re.findall(r'"((?:apple|google|topic):[^"]+)"', source))
        self.assertGreater(len(refs), 10)
        self.assertFalse(refs - ids)

    def test_sdks_to_declare(self):
        self.assertEqual([s["name"] for s in self.report["sdks"]], ["AdMob", "Google Sign-In", "RevenueCat"])


class CheckTests(unittest.TestCase):
    def test_sign_in_with_apple_clears_login_finding(self):
        login = {"src/Login.tsx": "import { GoogleSignin } from '@react-native-google-signin/google-signin';\n"}
        self.assertIn("A03", controls(scan_files({**EXPO, **login})))
        apple = {"src/Apple.tsx": "import * as AppleAuthentication from 'expo-apple-authentication';\n"}
        self.assertNotIn("A03", controls(scan_files({**EXPO, **login, **apple})))

    def test_deletion_path_clears_account_finding(self):
        auth = "import auth from '@react-native-firebase/auth';\nawait auth().signIn(email, password);\n"
        self.assertIn("C10", controls(scan_files({**EXPO, "src/a.ts": auth}), severity="CHECK"))
        firebase = auth + "const user = auth().currentUser;\nawait user.delete();\n"
        self.assertNotIn("C10", controls(scan_files({**EXPO, "src/a.ts": firebase})))
        unrelated = auth + "removeUserFromBlockList(id);\n"
        self.assertIn("C10", controls(scan_files({**EXPO, "src/a.ts": unrelated})))
        self.assertNotIn("C10", controls(scan_files({**EXPO, "src/a.ts": auth + "await api.deleteAccount();\n"})))

    def test_commented_out_deletion_does_not_count(self):
        code = "await auth.signIn(email, password);\n// await api.deleteAccount();\n/* deleteAccount() */\n"
        self.assertIn("C10", controls(scan_files({**EXPO, "src/a.ts": code})))

    def test_url_is_not_treated_as_a_comment(self):
        code = "await auth.signIn(email);\nfetch('https://api.example/delete-account');\n"
        self.assertNotIn("C10", controls(scan_files({**EXPO, "src/a.ts": code})))

    def test_missing_restore_is_a_check(self):
        buy = "import Purchases from 'react-native-purchases';\nPurchases.purchasePackage(pkg);\n"
        self.assertIn("C11", controls(scan_files({**EXPO, "src/buy.ts": buy}), "apple", "CHECK"))
        self.assertNotIn("C11", controls(scan_files({**EXPO, "src/buy.ts": buy + "Purchases.restorePurchases();\n"})))
        self.assertNotIn("C11", controls(scan_files({**EXPO, "src/buy.ts": buy + "RevenueCatUI.presentPaywall();\n"})))

    def test_absence_is_never_high(self):
        code = ("import auth from '@react-native-firebase/auth';\nimport Purchases from 'react-native-purchases';\n"
                "import 'react-native-google-mobile-ads';\nPurchases.purchasePackage(offerings.current.monthly);\n")
        report = scan_files({**EXPO, "src/a.ts": code})
        self.assertEqual(controls(report, severity="CHECK"), {"C10", "C11", "C12", "C13"})
        self.assertEqual(controls(report, severity="HIGH"), set())

    def test_search_terms_is_not_a_terms_link(self):
        code = ("import Purchases from 'react-native-purchases';\nPurchases.purchasePackage(offerings.current.monthly);\n"
                "const price = pkg.priceString;\nconst searchTerms = [];\n")
        titles = [f["title"] for f in scan_files({**EXPO, "src/a.ts": code})["findings"]]
        self.assertIn("Subscription without a terms link in source", titles)

    def test_event_subscription_is_not_a_billing_subscription(self):
        code = ("import Purchases from 'react-native-purchases';\nPurchases.purchasePackage(pkg);\n"
                "Purchases.restorePurchases();\nconst subscription = store.subscribe(listener);\n")
        self.assertNotIn("C12", controls(scan_files({**EXPO, "src/buy.ts": code})))

    def test_sign_in_call_without_an_sdk_is_only_a_check(self):
        report = scan_files({**EXPO, "src/a.ts": "await purchases.logIn(subjectId);\n"})
        self.assertEqual(controls(report, severity="CHECK"), {"C10"})
        self.assertEqual(controls(report, severity="HIGH"), set())

    def test_hidden_folders_are_skipped(self):
        report = scan_files({**EXPO, ".cache/x/src/a.ts": "import 'react-native-google-mobile-ads';\n"})
        self.assertEqual(report["findings"], [])

    def test_paywall_with_price_and_terms_is_quiet(self):
        paywall = ("import Purchases from 'react-native-purchases';\nPurchases.restorePurchases();\n"
                   "<Text>{pkg.product.priceString} per month, renews automatically</Text>;\n"
                   "Purchases.purchasePackage(pkg);\nLinking.openURL('https://example.com/terms');\n")
        self.assertNotIn("C12", controls(scan_files({**EXPO, "src/Paywall.tsx": paywall})))

    def test_tracking_prompt_clears_ads_finding(self):
        ads = {"src/ads.ts": "import { InterstitialAd } from 'react-native-google-mobile-ads';\n"}
        self.assertIn("C13", controls(scan_files({**EXPO, **ads})))
        att = {"src/att.ts": "import { requestTrackingPermissionsAsync } from 'expo-tracking-transparency';\n"}
        self.assertNotIn("C13", controls(scan_files({**EXPO, **ads, **att})))

    def test_placeholder_purpose_string_is_high(self):
        app = {"expo": {"ios": {"infoPlist": {"NSCameraUsageDescription": "TODO",
                                              "NSMicrophoneUsageDescription": "Record voice notes you send."}}}}
        report = scan_files({**EXPO, "app.json": json.dumps(app)})
        titles = [f["title"] for f in report["findings"] if f["severity"] == "HIGH"]
        self.assertEqual(titles, ["NSCameraUsageDescription is empty or a placeholder"])

    def test_expo_permission_list_is_read(self):
        app = {"expo": {"android": {"permissions": ["CAMERA", "READ_CALL_LOG"]}}}
        report = scan_files({**EXPO, "app.json": json.dumps(app)})
        self.assertEqual([f["title"] for f in report["findings"]], ["Restricted permission READ_CALL_LOG"])

    def test_spinner_and_date_wheel_are_not_gambling(self):
        code = ("const Spinner = () => <ActivityIndicator />;\n<WheelPicker items={days} />;\n"
                "const confetti = { spin: Math.random() * 900 };\nconst coins = 3;\nconst win = true;\n")
        self.assertNotIn("C14", controls(scan_files({**EXPO, "src/ui.tsx": code})))

    def test_listing_claims(self):
        report = scan_files({**EXPO,
                             "fastlane/metadata/android/en-US/title.txt": "Quiz\n#1 Best Trivia Game, Win Prizes!",
                             "fastlane/metadata/android/de-DE/title.txt": "Best Friends Quiz",
                             "fastlane/metadata/android/en-US/short_description.txt": "Trivia with coins.",
                             "fastlane/metadata/en-US/name.txt": "Quiz",
                             "fastlane/metadata/en-US/description.txt": "Also available on Android."})
        found = [(f["severity"], f["title"], f["where"]) for f in report["findings"]]
        self.assertEqual(found, [
            ("HIGH", 'title contains "#1" (en-US)', "fastlane/metadata/android/en-US/title.txt:2"),
            ("CHECK", 'title contains "Best" (de-DE)', "fastlane/metadata/android/de-DE/title.txt:1"),
            ("CHECK", 'description mentions "Android" (en-US)', "fastlane/metadata/en-US/description.txt:1")])
        self.assertEqual(controls(report), {"C04"})

    def test_android_only_project_gets_no_apple_findings(self):
        manifest = '<manifest><uses-permission android:name="android.permission.READ_SMS" /></manifest>'
        report = scan_files({"app/src/main/AndroidManifest.xml": manifest,
                             "app/build.gradle": "implementation 'com.google.android.gms:play-services-ads:23.0.0'\n"})
        self.assertEqual(report["platforms"], ["google"])
        self.assertEqual({f["platform"] for f in report["findings"]}, {"google"})

    def test_comment_marker_inside_a_string_keeps_the_code_after_it(self):
        code = ("import auth from '@react-native-firebase/auth';\npick({ type: 'image/*' });\n"
                "await auth().currentUser.delete();\n/** helper */\n")
        self.assertNotIn("C10", controls(scan_files({**EXPO, "src/a.ts": code})))

    def test_removed_and_blocked_permissions_are_not_reported(self):
        manifest = ('<manifest><uses-permission android:name="android.permission.READ_SMS" tools:node="remove" />'
                    '<!-- <uses-permission android:name="android.permission.READ_CALL_LOG" /> -->'
                    '<uses-permission android:name="android.permission.CAMERA" /></manifest>')
        app = {"expo": {"android": {"blockedPermissions": ["android.permission.READ_SMS"]}}}
        report = scan_files({**EXPO, "android/app/src/main/AndroidManifest.xml": manifest, "app.json": json.dumps(app)})
        self.assertEqual(report["findings"], [])

    def test_period_word_outside_purchase_code_is_not_a_subscription(self):
        buy = "import Purchases from 'react-native-purchases';\nPurchases.purchasePackage(pkg);\n"
        report = scan_files({**EXPO, "src/buy.ts": buy, "src/calendar.ts": "export const view = 'monthly';\n"})
        self.assertNotIn("C12", controls(report))

    def test_malformed_config_and_dangling_link_do_not_crash(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "package.json").write_text(EXPO["package.json"])
            Path(folder, "app.json").write_text('{"expo": {"ios": {"infoPlist": ["x"]}, "android": {"permissions": "x"}}}')
            Path(folder, "Info.plist").symlink_to(Path(folder, "missing"))
            self.assertEqual(scan(Path(folder))["findings"], [])

    def test_dependencies_folder_is_skipped(self):
        report = scan_files({**EXPO, "node_modules/x/index.js": "import 'react-native-google-mobile-ads';\n"})
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["sdks"], [])


class CommandTests(unittest.TestCase):
    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_high_finding_exits_1_with_json(self):
        code, out, _ = self.run_main(str(BENCH / "coin-quiz"), "--json")
        self.assertEqual(code, 1)
        report = json.loads(out)
        self.assertEqual(report["platforms"], ["apple", "google"])
        self.assertIn("no finding is not a pass", report["note"])

    def test_text_report_never_says_pass(self):
        code, out, _ = self.run_main(str(BENCH / "coin-quiz"))
        self.assertIn("2 HIGH, 7 CHECK", out)
        self.assertIn("no finding is not a pass", out)

    def test_clean_project_exits_0(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "package.json").write_text(EXPO["package.json"])
            code, out, _ = self.run_main(folder)
        self.assertEqual(code, 0)
        self.assertIn("0 HIGH, 0 CHECK", out)

    def test_folder_without_a_mobile_project_exits_2(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "notes.txt").write_text("nothing here")
            code, out, err = self.run_main(folder)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("Nothing was checked", err)


if __name__ == "__main__":
    unittest.main()
