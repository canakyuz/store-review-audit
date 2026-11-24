#!/usr/bin/env python3
"""Scan an iOS, Android, Expo, React Native or Flutter project for store-review signals.

  scan_project.py <project folder> [--json]

Reads files only: nothing is installed, changed or sent anywhere. HIGH means the files
contain something a store rule restricts: fix it or record the exception that applies.
CHECK means something expected was not found, or the outcome depends on what a scan
cannot see. No finding is not a pass.
Exit 0: no HIGH finding. 1: at least one HIGH finding. 2: no mobile project found.
"""
from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "references" / "policy-catalog.json"
SKIP_DIRS = {"node_modules", "Pods", "build", "dist", "DerivedData", "vendor", "__pycache__", "Carthage"}  # and every dot folder
CONFIG_NAMES = {"package.json", "app.json", "Podfile", "Podfile.lock", "pubspec.yaml", "Package.swift",
                "Package.resolved", "AndroidManifest.xml", "libs.versions.toml", "project.pbxproj"}
CONFIG_SUFFIXES = (".gradle", ".kts", ".plist", ".xcprivacy", ".entitlements")
SOURCE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".swift", ".kt", ".java", ".dart", ".m", ".mm", ".cs")
MAX_BYTES = 512 * 1024  # generated bundles are larger than this and hand-written files are not
# strings are matched first, so "image/*" or a URL inside one never starts a comment
COMMENT = re.compile(r"(\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*')|/\*.*?\*/|(?<!:)//[^\n]*", re.S)
TRANSLATIONS = re.compile(r"(?i)(^|/)(locales?|i18n|translations?|lang|languages)/.*\.json$")
LISTING = re.compile(r"(?:^|/)metadata/(?:(android)/)?([^/]+)/"
                     r"(name|subtitle|keywords|promotional_text|description|title|short_description|full_description)\.txt$")
NOT_VISIBLE = ("console declarations (App Privacy, Data safety, age rating, EULA)", "the store listing in the console",
               "legal pages", "runtime behaviour", "the built binary", "publisher account state")
NOTE = ("Findings are leads to confirm, and no finding is not a pass: every audit control stays UNKNOWN "
        "until it has evidence.")

AD_DATA = "advertising ID, device identifiers, ad interactions"
AI_DATA = "prompts and any personal data they contain"
HEALTH_DATA = "health and fitness data"
PAYMENT_DATA = "payment info, purchase history"
# name, roles, pattern, data the SDK commonly sends (None: nothing to declare for the SDK itself)
SDKS = [
    ("AdMob", "ads", r"react-native-google-mobile-ads|expo-ads-admob|Google-Mobile-Ads-SDK|GoogleMobileAds|play-services-ads|google_mobile_ads", AD_DATA + ", approximate location"),
    ("AppLovin", "ads", r"(?i)applovin", AD_DATA),
    ("Unity Ads", "ads", r"UnityAds|unity-ads|com\.unity3d\.ads|unity_ads", AD_DATA),
    ("ironSource", "ads", r"(?i)ironsource", AD_DATA),
    ("Meta Audience Network", "ads", r"FBAudienceNetwork|audience-network-sdk", AD_DATA),
    ("Google Sign-In", "login auth", r"@react-native-google-signin|\bGoogleSignIn\b|\bGIDSignIn\b|play-services-auth\b|google_sign_in", "name, email address, user ID"),
    ("Facebook Login", "login auth", r"react-native-fbsdk-next|FBSDKLoginKit|facebook-login|flutter_facebook_auth", "name, email address, user ID, device identifiers"),
    ("Sign in with Apple", "apple_login auth", r"expo-apple-authentication|react-native-apple-authentication|ASAuthorizationAppleID|sign_in_with_apple|com\.apple\.developer\.applesignin", None),
    ("Firebase Auth", "auth", r"@react-native-firebase/auth|firebase/auth|\bFirebaseAuth\b|firebase-auth|firebase_auth", "email address, user ID"),
    ("Auth0", "auth", r"react-native-auth0|\bAuth0\b|auth0_flutter", "email address, user ID"),
    ("RevenueCat", "purchases", r"react-native-purchases|\bRevenueCat\b|purchases_flutter|com\.revenuecat", "purchase history, app user ID"),
    ("In-app purchases", "purchases", r"react-native-iap|expo-in-app-purchases|expo-iap|in_app_purchase|SKPaymentQueue|SKProductsRequest|Product\.products\(|com\.android\.billingclient|billing-ktx|(?i:adapty|qonversion|superwall)", None),
    ("App Tracking Transparency", "att", r"expo-tracking-transparency|react-native-tracking-transparency|ATTrackingManager|app_tracking_transparency|NSUserTrackingUsageDescription", None),
    ("Firebase Analytics", "analytics", r"@react-native-firebase/analytics|\bFirebaseAnalytics\b|firebase-analytics|firebase_analytics", "app interactions, device identifiers"),
    ("Firebase Crashlytics", "", r"(?i)crashlytics", "crash logs, diagnostics"),
    ("Sentry", "", r"@sentry/|sentry_flutter|io\.sentry|sentry-cocoa|pod 'Sentry'", "crash logs, diagnostics"),
    ("AppsFlyer", "analytics", r"(?i)appsflyer", "advertising ID, device identifiers"),
    ("Adjust", "analytics", r"react-native-adjust|com\.adjust\.sdk|adjust_sdk", "advertising ID, device identifiers"),
    ("OneSignal", "", r"(?i)onesignal", "device identifiers, push token"),
    ("Amplitude", "analytics", r"@amplitude/|amplitude-react-native|Amplitude-iOS|AmplitudeSwift|amplitude_flutter|com\.amplitude", "app interactions, user ID"),
    ("Mixpanel", "analytics", r"(?i)mixpanel", "app interactions, user ID"),
    ("Stream Chat", "chat", r"(?<![\w-])stream-chat|\bStreamChat|stream_chat_flutter|io\.getstream", "messages, user ID"),
    ("Sendbird", "chat", r"(?i)sendbird", "messages, user ID"),
    ("CometChat", "chat", r"(?i)cometchat", "messages, user ID"),
    ("Gifted Chat", "chat", r"react-native-gifted-chat", None),
    ("OpenAI API", "ai", r"[\"']openai[\"']|api\.openai\.com|dart_openai|com\.openai", AI_DATA),
    ("Anthropic API", "ai", r"@anthropic-ai/|api\.anthropic\.com|com\.anthropic", AI_DATA),
    ("Google Gemini API", "ai", r"@google/generative-ai|@google/genai|google_generative_ai|generativelanguage\.googleapis"
     r"|firebase/ai|firebase/vertexai|FirebaseAI|FirebaseVertexAI|firebase-vertexai|firebase_vertexai", AI_DATA),
    ("HealthKit", "healthkit", r"react-native-health(?![\w-])|react-native-healthkit|HKHealthStore|com\.apple\.developer\.healthkit"
     r"|NSHealth(Share|Update)UsageDescription", HEALTH_DATA),
    ("Health Connect", "health_connect", r"react-native-health-connect|androidx\.health\.connect|android\.permission\.health\.",
     HEALTH_DATA),
    ("Stripe", "other_payment", r"@stripe/stripe-react-native|StripePaymentSheet|pod 'Stripe|com\.stripe:|flutter_stripe",
     PAYMENT_DATA),
    ("PayPal", "other_payment", r"react-native-paypal|PayPalCheckout|com\.paypal\.(checkout|android)|flutter_paypal", PAYMENT_DATA),
    ("Braintree", "other_payment", r"braintree-web|react-native-braintree|BraintreeDropIn|com\.braintreepayments|flutter_braintree"
     r"|pod 'Braintree", PAYMENT_DATA),
]

SMS_CALL = ("HIGH", "SMS and Call Log permissions are limited to default handlers or an approved exception and need the "
            "Permissions Declaration Form.", "Remove it unless the app is the default SMS or phone handler or has an "
            "approved exception. For one-time codes use the SMS Retriever or SMS User Consent API.")
DECLARE = "Play Console asks for a declaration and review before release."
MEDIA = ("CHECK", "Photo and video permissions are limited to apps whose core use needs broad access.",
         "Use the system photo picker for one-time or infrequent access.")
ANDROID_PERMISSIONS = {
    **{p: SMS_CALL for p in ("READ_SMS", "RECEIVE_SMS", "SEND_SMS", "RECEIVE_MMS", "RECEIVE_WAP_PUSH",
                             "READ_CALL_LOG", "WRITE_CALL_LOG", "PROCESS_OUTGOING_CALLS")},
    "ACCESS_BACKGROUND_LOCATION": ("CHECK", "Background location must be critical to a core feature. " + DECLARE,
                                   "Remove it, or complete the location declaration with a video of the feature."),
    "MANAGE_EXTERNAL_STORAGE": ("CHECK", "All files access is limited to permitted uses. " + DECLARE,
                                "Use the media store or the storage access framework, or complete the declaration."),
    "QUERY_ALL_PACKAGES": ("CHECK", "Broad package visibility is limited to permitted uses. " + DECLARE,
                           "Declare specific <queries> entries instead, or complete the declaration."),
    "REQUEST_INSTALL_PACKAGES": ("CHECK", "Installing packages is limited to apps where it is a core feature, "
                                 "such as browsers and file managers.",
                                 "Remove it unless sending or installing packages is a core feature."),
    "USE_FULL_SCREEN_INTENT": ("CHECK", "Full-screen intents are limited to calls and alarms. " + DECLARE,
                               "Remove it, or complete the full-screen intent declaration."),
    "BIND_ACCESSIBILITY_SERVICE": ("CHECK", "The Accessibility API needs a declaration and a prominent in-app disclosure.",
                                   "Complete the accessibility declaration, or remove the service."),
    "READ_MEDIA_IMAGES": MEDIA,
    "READ_MEDIA_VIDEO": MEDIA,
    "USE_EXACT_ALARM": ("CHECK", "USE_EXACT_ALARM is limited to apps whose core function needs precise timing, such "
                        "as alarm, timer and calendar apps.", "Remove it or use SCHEDULE_EXACT_ALARM if the use is not core; "
                        "otherwise complete the Play Console declaration."),
    "BIND_VPN_SERVICE": ("CHECK", "VpnService is limited to apps with VPN as core functionality and listed exceptions, "
                         "and its use must be documented in the store listing.",
                         "Document the VPN use in the listing, or remove the service."),
    # one entry for every FOREGROUND_SERVICE_<TYPE> permission
    "FOREGROUND_SERVICE_*": ("CHECK", "Apps that target Android 14 or newer declare each foreground service type on "
                            "the Play Console App content page.",
                            "Complete the foreground service declaration for each type, or remove unused types."),
}
FOREGROUND_SERVICE_REF = "topic:support.google.com/googleplay/android-developer/answer/13392821"

SIGN_IN = re.compile(r"\b(signIn|signUp|signInWith\w+|createUserWith\w+|logIn|login)\s*\(")
DELETION = re.compile(r"(?i)(delete|remove|erase)[\s_-]?(my[\s_-]?|your[\s_-]?)?(account|profile)"
                      r"|delete[\s_-]?user(?![a-z])|account[\s_/-]?delet|user\??\.delete\(")
# RevenueCatUI paywalls carry their own restore button
RESTORE = re.compile(r"(?i)restore[\s_-]?\w*(purchase|transaction)|AppStore\.sync\(|getAvailablePurchases"
                     r"|currentEntitlements|RevenueCatUI")
# event subscriptions (store.subscribe, EventSubscription) are not purchases, so only billing words count
SUBSCRIPTION = re.compile(r"(?i)auto-?renew|\b(weekly|monthly|annual|yearly)\b|subscription(Period|Group|Offer|Status)"
                          r"|(request|purchase|active)Subscriptions?|\bisSubscribed\b|ProductType\.SUBS")
PURCHASE_CALL = re.compile(r"purchasePackage|purchaseProduct|purchaseStoreProduct|requestSubscription|requestPurchase"
                           r"|launchBillingFlow|buyNonConsumable|\.purchase\(|SKPaymentQueue\.default\(\)\.add")
PURCHASE_FILE = re.compile("|".join([PURCHASE_CALL.pattern] + [rx for _, roles, rx, _ in SDKS if "purchases" in roles]))
TERMS = re.compile(r"(?i)\bterms\b|terms[\s_-]?of|termsUrl|eula")
# a bare "spin" or "wheel" is a spinner, an animation or a date picker far more often than a game of chance
CHANCE = re.compile(r"(?i)(lucky|prize|fortune) ?wheel|wheel ?of ?fortune|spin ?(the ?)?wheel|slot ?machine|roulette"
                    r"|jackpot|loot ?box|gacha|lottery|raffle|scratch ?card")
STAKE = re.compile(r"(?i)\b(stake|wager|bet|coins?|gems?|credits?|tokens?)\b")
PRIZE = re.compile(r"(?i)\b(prize|win|reward|lucky)\w*")
PLACEHOLDER = re.compile(r"(?i)^(|todo|tbd|test|lorem.*|placeholder|description|n/?a|\.+)$")
RANK_CLAIM = re.compile(r"(?i)#\s?1\b|\bno\.?\s?1\b|\b(free|sale|discount)\b")
SOFT_CLAIM = re.compile(r"(?i)\b(best|top)\b")  # also ordinary words: "Best Friends Quiz"
OTHER_PLATFORM = re.compile(r"(?i)\bandroid\b|google play")
REPORT = re.compile(r"(?i)\b(report|flag)[\s_-]?(this[\s_-]?)?(user|content|message|post|comment|abuse|response|answer)"
                    r"|\b(on|handle)(Report|Flag)\w*|reportReason")
BLOCK = re.compile(r"(?i)\b(un)?block[\s_-]?(this[\s_-]?)?(user|member|contact|sender)|\b(on|handle)Block\w*|blocked[\s_-]?users")
PRIVACY = re.compile(r"(?i)privacy|gizlilik|datenschutz|privacidad|confidentialit|privacidade")
LOREM = re.compile(r"(?i)lorem ipsum")
NOT_SHIPPED = re.compile(r"(?i)(^|/)(__tests__|__mocks__|tests?|e2e|stories|storybook|fixtures?)/|\.(test|spec|stories)\.")
PRERELEASE = re.compile(r"(?i)\b(beta|demo|trial)\b")
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2300-\u23FF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u20E3]")
RESTRICTED_MODES = {"location", "audio", "voip"}  # the modes 2.5.4 names; fetch and remote-notification are routine


@dataclass
class File:
    rel: str
    text: str
    kind: str  # config, source or listing


@dataclass
class Finding:
    control: str
    platform: str  # apple, google or all
    severity: str  # HIGH or CHECK
    title: str
    where: str
    why: str
    fix: str
    refs: list


class Project:
    def __init__(self, files: list):
        self.files = files
        self.sdks = {}   # name -> (where, data)
        self.roles = {}  # role -> [(name, where)]
        for name, roles, pattern, data in SDKS:
            at = self.find(pattern)
            if at:
                self.sdks[name] = (at, data)
                for role in roles.split():
                    self.roles.setdefault(role, []).append((name, at))
        rels = [f.rel for f in files]
        cross = self.find(r'"(expo|react-native)"\s*:|sdk:\s*flutter', "config")
        ios = cross or any(re.search(r"(^|/)ios/|\.xcodeproj/|\.swift$|\.xcprivacy$|(^|/)Info\.plist$", r) for r in rels)
        android = cross or any(re.search(r"(^|/)android/|AndroidManifest\.xml$|\.gradle(\.kts)?$", r) for r in rels)
        self.platforms = [name for name, present in (("apple", ios), ("google", android)) if present]

    def matches(self, pattern, kind=None):
        """Every (file, match) for the pattern, in file order."""
        rx = re.compile(pattern) if isinstance(pattern, str) else pattern
        for f in self.files:
            if f.kind != "listing" and kind in (None, f.kind):
                for m in rx.finditer(f.text):
                    yield f, m

    def find(self, pattern, kind=None):
        """Location of the first match as path:line, or None."""
        for f, m in self.matches(pattern, kind):
            return where(f, m.start())
        return None


def where(f: File, pos: int) -> str:
    return f"{f.rel}:{f.text.count(chr(10), 0, pos) + 1}"


def classify(name: str, rel: str):
    if LISTING.search(rel):
        return "listing"
    if name in CONFIG_NAMES or name.endswith(CONFIG_SUFFIXES) or name.startswith("app.config."):
        return "config"
    # translation files hold the labels (Delete account, Privacy policy) the absence checks look for
    return "source" if name.endswith(SOURCE_SUFFIXES) or TRANSLATIONS.search(rel) else None


def load(root: Path) -> list:
    files = []
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for name in sorted(names):
            path = Path(folder, name)
            rel = path.relative_to(root).as_posix()
            kind = classify(name, rel)
            try:
                if not kind or path.stat().st_size > MAX_BYTES:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:  # a dangling link or unreadable file is skipped, not fatal
                continue
            if kind == "source":  # a commented-out call must not count as the feature; line numbers stay intact
                text = COMMENT.sub(lambda m: m.group(1) or "\n" * m.group().count("\n"), text)
            files.append(File(rel, text, kind))
    return files


def check_login(p):
    social = p.roles.get("login")
    if "apple" in p.platforms and social and not p.roles.get("apple_login"):
        name, at = social[0]
        yield Finding("A03", "apple", "HIGH", f"{name} without Sign in with Apple", at,
                      "A third-party or social login for the primary account needs an equivalent privacy-focused "
                      "login option. Exceptions: only your own account system, education or enterprise accounts, "
                      "government ID, or a client for that third-party service.",
                      "Add Sign in with Apple or another service that meets 4.8, or record which exception applies.",
                      ["apple:4.8"])


def check_deletion(p):
    at = next((w for _, w in p.roles.get("auth", [])), None) or p.find(SIGN_IN, "source")
    if at and not p.find(DELETION, "source"):
        yield Finding("C10", "all", "CHECK", "Accounts without an account deletion path in source", at,
                      "Apps that create accounts must let users start deletion of the account and its data inside "
                      "the app. Deactivating or emailing support does not meet it. Google also asks for a web "
                      "deletion URL in the Data safety form.",
                      "Add an in-app delete account action that removes the account and associated data, and set "
                      "the Play Console deletion URL.",
                      ["apple:5.1.1", "topic:developer.apple.com/support/offering-account-deletion-in-your-app",
                       "topic:support.google.com/googleplay/android-developer/answer/13327111"])


def check_tracking(p):
    ads = p.roles.get("ads")
    if "apple" in p.platforms and ads and not p.roles.get("att"):
        name, at = ads[0]
        yield Finding("C13", "apple", "CHECK", f"{name} without an App Tracking Transparency prompt", at,
                      "Personalized ads use the advertising identifier, which needs the tracking permission prompt "
                      "and NSUserTrackingUsageDescription. An ad SDK alone does not prove tracking.",
                      "Request tracking permission before loading personalized ads, or serve non-personalized ads "
                      "only and declare that.", ["apple:5.1.2"])


def check_privacy_manifest(p):
    declared = [name for name, (_, data) in p.sdks.items() if data]
    manifests = [f for f in p.files if f.rel.endswith(".xcprivacy")]
    if "apple" not in p.platforms or not declared or not manifests:
        return
    for f in manifests:
        try:
            if plistlib.loads(f.text.encode()).get("NSPrivacyCollectedDataTypes"):
                return
        except Exception:  # an unreadable manifest cannot be judged
            return
    yield Finding("A02", "apple", "CHECK", "Privacy manifest lists no collected data", f"{manifests[0].rel}:1",
                  "The app's manifest declares no collected data while these SDKs commonly send data: "
                  + ", ".join(declared) + ". The App Privacy label must cover what the app and its SDKs collect.",
                  "Confirm the App Privacy label lists this data, and add what your own code collects to the manifest.",
                  ["topic:developer.apple.com/documentation/BundleResources/privacy-manifest-files",
                   "topic:developer.apple.com/app-store/app-privacy-details"])


def info_plists(p):
    """(file, dict) for every Info.plist and every app.json infoPlist block that parses."""
    for f in p.files:
        try:
            if f.rel.endswith("Info.plist"):
                plist = plistlib.loads(f.text.encode())
            elif f.rel.endswith("app.json"):
                plist = json.loads(f.text).get("expo", {}).get("ios", {}).get("infoPlist", {})
            else:
                continue
        except Exception:
            continue
        if isinstance(plist, dict):
            yield f, plist


def purpose_strings(p):
    """(key, value, location) for every iOS purpose string."""
    for f, plist in info_plists(p):
        for key, value in plist.items():
            if key.endswith("UsageDescription") and isinstance(value, str):
                yield key, value.strip(), where(f, max(f.text.find(key), 0))


def check_background_modes(p):
    if "apple" not in p.platforms:
        return
    found, at = set(), None  # app.json and the Info.plist generated from it declare the same modes: one finding
    for f, plist in info_plists(p):
        modes = plist.get("UIBackgroundModes")
        here = RESTRICTED_MODES & {m for m in modes if isinstance(m, str)} if isinstance(modes, list) else set()
        if here:
            found |= here
            at = at or where(f, max(f.text.find("UIBackgroundModes"), 0))
    if found:
        yield Finding("C19", "apple", "CHECK", "Background modes declared: " + ", ".join(sorted(found)), at,
                      "Background services may only be used for their intended purposes.",
                      "Remove each mode no shipped feature uses.",
                      ["apple:2.5.4"])


def check_purpose_strings(p):
    if "apple" not in p.platforms:
        return
    always = set()  # one finding per file: the Always and AlwaysAndWhenInUse keys are the same request
    for key, value, at in purpose_strings(p):
        if PLACEHOLDER.match(value):
            yield Finding("C19", "apple", "HIGH", f"{key} is empty or a placeholder", at,
                          "A purpose string must explain why the app needs the access, with an example of use.",
                          "Write the specific reason the feature needs this access.", ["apple:5.1.1"])
        elif "Always" in key and at.rsplit(":", 1)[0] not in always:
            always.add(at.rsplit(":", 1)[0])
            yield Finding("C19", "apple", "CHECK", "Always location purpose string declared", at,
                          "Always location needs a feature that uses location in the background.",
                          "Remove the key if the app only needs location while in use.", ["apple:5.1.1", "apple:2.5.4"])


def requested_permissions(f: File):
    """(permission, position) for permissions a manifest or app.json asks for; removed or blocked ones are not."""
    if f.rel.endswith("AndroidManifest.xml"):
        live = re.sub(r"<!--.*?-->", lambda c: re.sub(r"[^\n]", " ", c.group()), f.text, flags=re.S)
        for tag in re.finditer(r"<[^>]*android\.permission\.([A-Z_]+)[^>]*>", live):
            if 'tools:node="remove"' not in tag.group():
                yield tag.group(1), tag.start()
    elif f.rel.endswith("app.json"):
        try:
            names = json.loads(f.text)["expo"]["android"]["permissions"]
        except (ValueError, KeyError, TypeError):
            return
        for name in names if isinstance(names, list) else ():
            if isinstance(name, str):
                yield name.rsplit(".", 1)[-1], max(f.text.find('"permissions"'), 0)


def android_permissions(p):
    """(permission, rule key, location) once per restricted permission."""
    seen = set()
    for f in p.files:
        for name, pos in requested_permissions(f):
            rule = "FOREGROUND_SERVICE_*" if re.match(r"FOREGROUND_SERVICE_\w", name) else name
            if rule in ANDROID_PERMISSIONS and name not in seen:
                seen.add(name)
                yield name, rule, where(f, pos)


def check_android_permissions(p):
    if "google" not in p.platforms:
        return
    for name, rule, at in android_permissions(p):
        severity, why, fix = ANDROID_PERMISSIONS[rule]
        refs = ["google:policy:12579724"] + ([FOREGROUND_SERVICE_REF] if rule == "FOREGROUND_SERVICE_*" else [])
        yield Finding("C19", "google", severity, f"Restricted permission {name}", at, why, fix, refs)


def check_purchases(p):
    purchases = p.roles.get("purchases")
    if not purchases:
        return
    # "monthly" in a calendar view is not a subscription: the word counts only in a file that touches purchases
    subscription = next((where(f, m.start()) for f in p.files if f.kind == "source" and PURCHASE_FILE.search(f.text)
                         for m in [SUBSCRIPTION.search(f.text)] if m), None)
    if "apple" in p.platforms and not p.find(RESTORE, "source"):
        yield Finding("C11", "apple", "CHECK", "Purchases without a restore mechanism",
                      purchases[0][1], "Apps with restorable in-app purchases (subscriptions, non-consumables) "
                      "should have a restore mechanism. Consumables alone do not need it.",
                      "Add a Restore purchases action that calls the store's restore API.", ["apple:3.1.1"])
    if not subscription:
        return
    refs = ["apple:3.1.2", "google:policy:9900533"]
    for f in p.files:
        call = PURCHASE_CALL.search(f.text) if f.kind == "source" else None
        if call and not re.search(r"(?i)price", f.text):
            yield Finding("C12", "all", "CHECK", "Purchase started in a file that never reads a price", where(f, call.start()),
                          "A subscription screen must show the price, billing period and renewal terms before "
                          "purchase. If the paywall text lives in another file, confirm it there.",
                          "Show the localized price, period and auto-renewal terms next to the purchase button.", refs)
    if "apple" in p.platforms and not p.find(TERMS, "source"):
        yield Finding("C12", "apple", "CHECK", "Subscription without a terms link in source", purchases[0][1],
                      "Subscription apps need working links to the terms of use and privacy policy in the app.",
                      "Link the terms of use (EULA) and privacy policy from the paywall or settings.", ["apple:3.1.2"])


def check_chance(p):
    for f in p.files:
        if f.kind != "source":
            continue
        chance = CHANCE.search(f.text)
        if chance and STAKE.search(f.text) and PRIZE.search(f.text):
            yield Finding("C14", "all", "CHECK", "Chance mechanic with stakes and prizes", where(f, chance.start()),
                          "Staking in-app value on a random outcome is simulated gambling for the age and content "
                          "rating. Purchasable random items must disclose odds. Prizes with real-world value bring "
                          "gambling or contest rules.",
                          "Declare simulated gambling in the rating, disclose odds for purchasable random items, "
                          "and confirm prizes cannot leave the app.",
                          ["apple:3.1.1", "google:policy:9877032", "google:policy:9898843",
                           "topic:developer.apple.com/help/app-store-connect/reference/app-information/age-ratings-values-and-definitions"])
            return


def check_ugc(p):
    chat = p.roles.get("chat")
    missing = [name for name, rx in (("report", REPORT), ("block", BLOCK)) if not p.find(rx, "source")]
    if chat and missing:
        yield Finding("C16", "all", "CHECK", f"{chat[0][0]} without a {' or '.join(missing)} action in source", chat[0][1],
                      "Apple: filtering of objectionable material, a report mechanism, blocking of abusive users "
                      "and published contact information. Google: terms of use accepted before posting, and in-app "
                      "reporting and blocking of content and users.",
                      "Add report and block actions to messages and profiles, and a moderation path behind them.",
                      ["apple:1.2", "google:policy:9876937"])


def check_ai(p):
    for name, at in p.roles.get("ai", [])[:1]:
        why = ("Personal data sent to a third-party AI needs clear disclosure and explicit permission first (Apple). "
               "Apps that generate content with AI need in-app reporting or flagging of offensive output (Google).")
        if not p.find(REPORT, "source"):
            why += " No report or flag action was found in source."
        yield Finding("C17", "all", "CHECK", f"{name}: data sharing consent and output reporting", at, why,
                      "Ask before the first request that carries personal data, name the provider, and add a report "
                      "action on generated content.", ["apple:5.1.2", "google:policy:13985936"])


def check_health(p):
    ads = ", ".join(name for name, _ in p.roles.get("ads", []))
    for name, at in p.roles.get("healthkit", [])[:1]:
        yield Finding("C18", "apple", "CHECK", "HealthKit access" + (f" in an app with {ads}" if ads else ""), at,
                      "Health and fitness data may not be used or disclosed to third parties for advertising, "
                      "marketing or use-based data mining, other than to improve health management or for health "
                      "research, and then only with permission.",
                      "Confirm no health data reaches an ad or analytics SDK, and state the use in the privacy policy.",
                      ["apple:5.1.3"])
    for name, at in p.roles.get("health_connect", [])[:1]:
        yield Finding("C18", "google", "CHECK", "Health Connect access", at,
                      "Apps with health features or health data access complete the Health apps declaration in Play "
                      "Console, and Health Connect data is personal and sensitive user data.",
                      "Complete the Health apps declaration and cover health data in the privacy policy.",
                      ["google:policy:9878878"])


def check_other_payment(p):
    for name, at in p.roles.get("other_payment", [])[:1]:
        yield Finding("C11", "all", "CHECK", f"{name}: payment outside the store billing system", at,
                      "Digital content and features unlocked in the app go through in-app purchase or Play billing. "
                      "Other payment methods are for physical goods, services used outside the app and the listed "
                      "exceptions, which differ by storefront and program.",
                      "Confirm everything sold through this SDK is a physical good, an outside service or a listed "
                      "exception, and record which.", ["apple:3.1.1", "apple:3.1.3", "google:policy:9858738"])


def check_privacy_link(p):
    declared = next(((name, at) for name, (at, data) in p.sdks.items() if data), None)
    if declared and not p.find(PRIVACY, "source"):
        yield Finding("C05", "all", "CHECK", "No privacy policy link in source", declared[1],
                      f"The app includes {declared[0]}, which sends data, and no source file mentions a privacy "
                      "policy. Both stores ask for the policy in the console and inside the app.",
                      "Link the privacy policy from settings or sign-up.", ["apple:5.1.1", "google:policy:9888076"])


def check_placeholder(p):
    if "apple" not in p.platforms:
        return
    seen = set()  # one finding for app source and one for the listing
    for f in p.files:
        m = LOREM.search(f.text) if f.kind in ("source", "listing") and not NOT_SHIPPED.search(f.rel) else None
        # 2.1 is Apple's rule, so a Play listing file is left alone
        if not m or f.kind in seen or (f.kind == "listing" and LISTING.search(f.rel).group(1)):
            continue
        seen.add(f.kind)
        listing = f.kind == "listing"
        yield Finding("C04" if listing else "C03", "apple", "HIGH" if listing else "CHECK",
                      "Placeholder text (lorem ipsum)", where(f, m.start()),
                      "Submissions should be final: placeholder text and temporary content are removed before review.",
                      "Replace the placeholder with final text.", ["apple:2.1"])


def check_listing(p):
    for f in p.files:
        m = LISTING.search(f.rel) if f.kind == "listing" else None
        if not m:
            continue
        store, locale, name = ("google" if m.group(1) else "apple"), m.group(2), m.group(3)
        is_title = name in ("name", "subtitle", "title")
        hard = RANK_CLAIM.search(f.text) if is_title else None
        claim = hard or (SOFT_CLAIM.search(f.text) if is_title else None)
        if claim and store == "google":
            yield Finding("C04", "google", "HIGH" if hard else "CHECK", f'{name} contains "{claim.group().strip()}" ({locale})',
                          where(f, claim.start()), "Play titles must not carry words that imply store performance, "
                          "ranking, price or promotion.", "Remove the claim from the title.", ["google:policy:9898842"])
        elif claim:
            yield Finding("C04", "apple", "CHECK", f'{name} contains "{claim.group().strip()}" ({locale})',
                          where(f, claim.start()), "App names and subtitles should not include prices or terms that "
                          "are not the name of the app.", "Remove the claim from the name.", ["apple:2.3.7"])
        if is_title and store == "google":
            emoji = EMOJI.search(f.text)
            if emoji:
                yield Finding("C04", "google", "HIGH", f"{name} contains an emoji ({locale})", where(f, emoji.start()),
                              "Play titles must not use emojis, emoticons or repeated special characters.",
                              "Remove the emoji from the title.", ["google:policy:9898842"])
            words = re.findall(r"[^\W\d_]{2,}", f.text)
            if len(words) > 1 and all(w.isupper() for w in words) and any(len(w) > 3 for w in words):  # QR NFC is acronyms
                yield Finding("C04", "google", "CHECK", f"{name} is all capitals ({locale})", f"{f.rel}:1",
                              "Play asks to avoid all capitals unless they are part of the brand name.",
                              "Use normal capitalisation unless the capitals are the brand name.", ["google:policy:9898842"])
        pre = PRERELEASE.search(f.text) if is_title and store == "apple" else None
        if pre:
            yield Finding("C04", "apple", "CHECK", f'{name} contains "{pre.group()}" ({locale})', where(f, pre.start()),
                          "Demos, betas and trial versions do not belong on the App Store.",
                          "Remove the word unless it is part of the product's name, and ship the final version.",
                          ["apple:2.2"])
        other = OTHER_PLATFORM.search(f.text) if store == "apple" else None
        if other:
            yield Finding("C04", "apple", "CHECK", f'{name} mentions "{other.group()}" ({locale})', where(f, other.start()),
                          "App Store metadata should not mention other mobile platforms unless there is specific, "
                          "approved interactive functionality.", "Remove the reference unless that applies.",
                          ["apple:2.3.10"])


CHECKS = (check_login, check_deletion, check_tracking, check_privacy_manifest, check_privacy_link, check_purpose_strings,
          check_background_modes, check_android_permissions, check_purchases, check_other_payment, check_chance,
          check_ugc, check_ai, check_health, check_placeholder, check_listing)


def scan(root: Path):
    """Scan a project folder. Returns None when it holds no iOS or Android project."""
    project = Project(load(root))
    if not project.platforms:
        return None
    findings = [f for check in CHECKS for f in check(project) if f.platform in ("all", *project.platforms)]
    findings.sort(key=lambda f: f.severity != "HIGH")
    return {"root": str(root), "platforms": project.platforms, "files": len(project.files),
            "findings": [asdict(f) for f in findings],
            "sdks": [{"name": n, "where": w, "data": d} for n, (w, d) in project.sdks.items() if d],
            "not_visible": list(NOT_VISIBLE), "note": NOTE}


def render(report: dict) -> str:
    urls = {item["id"]: item["url"] for item in json.loads(CATALOG.read_text())["items"]}
    out = [f"Store review scan: {report['root']} ({', '.join(report['platforms'])}), "
           f"{report['files']} files in {report['seconds']}s", ""]
    for f in report["findings"]:
        out += [f"{f['severity']:<5} {f['control']} {f['platform']:<6} {f['title']}", f"      at   {f['where']}",
                f"      why  {f['why']}", f"      fix  {f['fix']}"]
        out += [f"      ref  {ref} {urls[ref]}" for ref in f["refs"]]
        out.append("")
    if report["sdks"]:
        out.append("Declare in App Privacy and Data safety (check each vendor's own disclosure):")
        out += [f"  {s['name']} ({s['where']}): {s['data']}" for s in report["sdks"]]
        out.append("")
    high = sum(f["severity"] == "HIGH" for f in report["findings"])
    out += ["Not visible to a scan: " + "; ".join(report["not_visible"]) + ".",
            f"{high} HIGH, {len(report['findings']) - high} CHECK. {report['note']}"]
    return "\n".join(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", type=Path, help="folder that holds the app")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"Not a folder: {args.project}", file=sys.stderr)
        return 2
    started = time.perf_counter()
    report = scan(args.project)
    if report is None:
        print(f"No iOS or Android project found in {args.project}. Nothing was checked.", file=sys.stderr)
        return 2
    report["seconds"] = round(time.perf_counter() - started, 3)
    print(json.dumps(report, indent=2) if args.json else render(report))
    return 1 if any(f["severity"] == "HIGH" for f in report["findings"]) else 0


if __name__ == "__main__":
    sys.exit(main())
