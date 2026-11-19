# Conditional checks and recurring failures

## Games, coins and gambling

Map currency acquisition (purchase/ad/free), stakes, possible losses, reward determination, player transfers, cash-out/redemption and real-world prizes. Inspect gameplay and backend rules. A board-game label proves nothing; no cash-out does not by itself rule out simulated gambling.

Apply each store independently. Google checks include real-money stakes/prizes, regions/eligibility, gambling ads and ratings separately from virtual-only play. Do not transfer Apple's organization rule mechanically to Google. Check loot boxes/contests where present. Do not equate store taxonomy with a legal gambling classification.

Paid randomized rewards (a spin, chest or draw bought with real money or with currency that can be bought) are loot boxes: both stores require the odds to be disclosed before purchase (Apple 3.1.1, Google Payments).

Sweepstakes and contests (Apple 5.3): the developer is the sponsor and the in-app official rules state that Apple is not a sponsor. Google real-money gambling: free download, no Play Billing for wagers, responsible-gambling information; loyalty programs follow their own rules.

Illustrative rejection pattern: a review message may block an app that declares simulated gambling while its publisher is an individual. Preserve the exact current message as submission-specific evidence. If the content exists, investigate the stated organization/transfer remedy; if absent, correct the declaration truthfully. Never simply switch the answer to No.

## Subscriptions and documents

Align product configuration, UI, entitlements and locale-specific disclosures. Exercise purchase/cancel/restore/expiry and relevant revocation/error cases as engineering verification; do not label every test a verbatim policy requirement.

For a subscription rejection concerning EULA metadata, inspect every localized description or the configured custom EULA as applicable. A privacy-policy link alone does not address a missing EULA. If standard-EULA use is confirmed, preserve existing descriptions and append the appropriate label:

English: Terms of Use (EULA): https://www.apple.com/legal/internet-services/itunes/dev/stdeula/

Turkish: Kullanım Koşulları (EULA): https://www.apple.com/legal/internet-services/itunes/dev/stdeula/

Do not automatically use Apple's EULA for Android. Verify the developer's applicable terms; do not invent legal obligations or claim GDPR compliance.

## Expo / React Native / RevenueCat / AdMob

Inspect package/lockfiles, app.json/app.config.*, eas.json, Info.plist, entitlements, merged AndroidManifest.xml, privacy manifests, production environment references and actual artifacts when available. Native dependencies/plugins can add permissions. Declared config is not proof of uploaded-build contents.

For RevenueCat, independently verify iOS/Android apps, product/offering/package mappings, entitlements, project association and production keys by presence without exposing values. Check store integration and purchase evidence. A working iOS offering does not prove Android works.

For ads, inspect SDK versions, formats/placement/reward flow, age settings, data sharing and consent configuration. Ads live in the main binary and within the content rating, never imitate system UI, never appear outside the app or on the lock screen, and interstitials follow the stores' timing and close-button rules. Apple: a way to see why an ad was shown and to report it, no targeting on health or children's data. No ad is hidden, off screen or placed for accidental taps, no ad click or personal data is required before the app can be used, and the app is not built mainly to show ads (Apple 3.2.2, Google Ads and Ad Fraud). Verify applicable Google consent requirements and Apple ATT separately; UMP and ATT are not interchangeable. Do not label SDK traffic anonymous without evidence.

## AI, health, kids and UGC

- AI: inspect generated content types, abuse controls/reporting and model-provider data flows. Verify Google's current AI rules (including AppFunctions once effective; check the policy deadlines page) and Apple's privacy/consent rules for third-party AI sharing. Features that alter or generate realistic media of public figures or news add a clear watermark or disclaimer, and the listing does not use public figures or sensitive events to advertise them (Google Deceptive Behavior).
- Health/fitness: distinguish wellness from diagnosis/treatment; inspect HealthKit/Health Connect, declarations, sensitive-data use and evidence for claims. Google expects a not-a-medical-device disclaimer where relevant and Health Connect limited use. Do not invent regulatory clearance.
- Kids: inspect intended audience and actual age flows, SDK/ad eligibility, parental gates, external links and data practices against each platform, including Google Families identifier, location and ad-format limits.
- UGC/chat: inspect reporting, blocking, moderation and contact paths against current policies; terms accepted before posting, sexual content filtered by default, child-safety standards for chat and dating.
- Mini apps, plug-ins, chatbots and emulators hosted in the app (Apple 4.7): inventory them and apply privacy, payment and moderation rules to each; per-instance consent before sharing data.
- Spam/template apps: compare meaningful workflows/content/value across sibling apps. Icon/name/colour changes alone do not establish that functionality/spam concerns were resolved.

## Regulated services

Record entity, licence and territory evidence for medical claims and dosage tools, crypto (no on-device mining), insurance, charity, trading, loans (APR and term disclosure), binary options (banned) and device management (Apple 1.4, 1.7, 3.1.5, 5.5; Google Financial Services). Absence of a licence is UNKNOWN until checked, not FAIL.

## Monitoring and screen capture (Google)

Monitoring tools set the monitoring-tool flag, show a persistent notification and a distinct icon, and disclose the function in the listing. Apps respect FLAG_SECURE content of other apps.

## Guest and automatic accounts

A server-side account created silently at first launch is an account for Apple: 5.1.1(v) deletion applies (Apple account deletion FAQ). Google defines an app account differently; decide G03 and C10 for Google from its own text and record the reasoning. Never let one platform's answer stand in for the other.

## Hidden opponents and house players

If the app seats bots or house players against users, especially where purchasable currency is staked, check that nothing misleads users about who they play (Apple 5.6 and 2.3, Google Deceptive Behavior), and record how the app labels them.

## Rejection response

A notice may not list every issue: recheck the whole app before resubmitting. Split metadata, binary, account and policy issues. Give the smallest truthful fix, whether a new build appears necessary, and verify resubmission options. Draft a factual reply with build, each issue, completed changes, navigation and evidence. Use future tense for incomplete work. One fixed link does not resolve every issue. Do not send under audit-only authorization.
