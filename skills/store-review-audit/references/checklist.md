# Audit checklist

Use as evidence-gathering prompts. Confirm the current applicable rule before reporting a violation. Cover all baseline rows and applicable conditional rows; justify N/A.

## Baseline: both stores

| Area | Inspect |
| --- | --- |
| Scope | App ID, submitted build, store state, account type, legal publisher, countries and locales. |
| Account | Identity/membership verification, pending tasks, required agreements, monetization setup and regional trader/business disclosures. Do not accept agreements during an audit. |
| Reviewer access | Demo access, reproducible steps, OTP/MFA handling, gated features, live backend and attachments. Review notes explain the business model, steps for changed or non-obvious features and purchases, external services, regional differences, an expired-subscription account where relevant and a current contact. Keep secrets out of reports. |
| Quality | Launch/login/core task, errors/offline/denied permissions, purchase/deletion flows and supported layouts. No forced or incentivized ratings, no device-setting changes without consent, no imitation of system UI or alerts, no messages sent without the user confirming content and recipients, a prompt before large downloads, and the same behaviour during review as in production: no feature hidden for review and switched on later by a flag or OTA (record under C03). Record actual tests performed. Notifications serve only the app's own features and never advertise other apps; the app never urges users to restart the device, disable security features or Play Protect, remove other apps or believe the device is infected (Apple 2.4.4, Google system functionality, Deceptive Behavior, Mobile Unwanted Software). |
| Listing | Accurate claims/screenshots/icon/name/description/What's New/support URL; all locales and current dimensions. Items needing an extra purchase are marked; promoted purchases, in-app events, creative assets and pre-orders match the build; the listing is not a beta, demo or trial. |
| Documents | Privacy, applicable EULA/terms, subscription explanations, deletion instructions and contacts; public accessibility and correct identity. |
| Data inventory | Data type/source, recipient/SDK, purpose, collection/sharing, linkage/tracking, retention/deletion, security and consent. |
| Audience | Actual content, intended ages, ads/chat/UGC/web access, health, contests and currency mechanics. |
| Rights/originality | Asset/media/content rights and meaningful value/differences from sibling apps. Features that induce infringement or sell counterfeit goods. No Apple emoji images in the binary or on Android (Apple 4.5.6); a custom emoji font supports the current Unicode Emoji version on Android 12 or later. |
| Restricted content | App content, UGC, AI output and metadata against each store's prohibited categories (Apple 1.1 and 1.4, Google Restricted Content), independently of the age answers; fake official documents and personal data of people who did not consent. |

## Apple

| Area | Inspect |
| --- | --- |
| Core rules | Navigate current 2.1 completeness, 2.3 metadata, 3.1 payments, 4.2 functionality, 4.3 spam, 4.8 login, 5.1 privacy and 5.2 IP. Business rules outside 3.1: no irrationally high prices, no arbitrary restriction of users by location or carrier, no store-like catalogue of third-party apps, no rank manipulation on other services (3, 3.2.2). |
| Purchases | IDs, availability, groups/entitlements and submitted-build configuration; purchase/restore/expiry and cancellation information. No paid item that only unlocks built-in hardware, OS capabilities or Apple services (4.10). |
| EULA | Standard EULA link in every localized description for subscriptions, or configured custom EULA/territories. Check in-app privacy/terms access separately. |
| App Privacy | Compare labels to app/partner data flows, distinguishing on-device from transmitted processing. |
| Native privacy | PrivacyInfo.xcprivacy, required-reason APIs, relevant SDK manifests/signatures, permission descriptions and ATT applicability. Manifests do not replace labels. |
| Deletion | Applicable in-app deletion and associated-data removal. Distinguish deactivation and subscription cancellation. An account the app creates automatically (guest or device account) still needs an in-app way to start deletion (Apple account deletion FAQ). |
| Rating/entity | Current questionnaire, regional result, content and relevant publisher-entity restrictions/review message. |
| Submission | Build processing, signing, entitlements, export compliance, current SDK requirements and IAP/review attachments. Binary: no private or deprecated APIs, no downloaded executable code, no hidden or obfuscated features, WebKit for web browsing, works on IPv6-only networks (2.5). |
| Platform technologies | Each entitlement, extension and framework the build uses (App Clips, widgets, keyboards, Safari extensions, SiriKit, CallKit, Apple Pay, Wallet, Game Center, MusicKit, Matter, Face ID) against its clause in 2.5, 4.4, 4.5 and 4.9. |
| Runtime conduct | Core function does not require push; marketing push is opt-in with an opt-out and carries no sensitive data; recording shows an indicator; no excessive battery or heat, no on-device mining; system controls and home screen unchanged; only the system review prompt. |

## Google Play

| Area | Inspect |
| --- | --- |
| App content | Needs attention plus existing privacy/ads/access/audience/rating/Data safety/sensitive-feature declarations. Social, chat and dating apps: published child-safety standards and contact; minor-blocking where the policy requires it. |
| Data safety | Reconcile SDK/backend behaviour with collection/sharing/purpose/security/deletion answers. Do not copy Apple answers mechanically. Prominent disclosure and affirmative consent before collection outside user expectations; identifier rules (persistent IDs not linked to the advertising ID, App Set ID not for ads); no sale of personal data. Age Signals API results serve only legal age obligations, never ads, analytics, personalization, profiling or transfer. |
| Privacy | Listing and in-app policy, truthful data practices, retention/deletion and contact identity. The policy URL is public, labelled as a privacy policy, served over valid TLS, not geofenced, not behind a login and not a PDF. |
| Deletion | Applicable in-app path AND external deletion-request URL; real account/data removal and disclosed retention exceptions. The external resource names the app or developer as on the listing, needs no reinstall and covers accounts created outside the app. |
| Billing | Current Billing requirements, products/base plans/offers/markets, purchase/entitlement processing and regional alternatives eligibility. Anti-steering rules, purchases that must not use Play Billing, loot box odds. |
| Subscription UI | Localized billed price, interval, auto-renewal, trial conversion, recurring value, optional access and cancellation route. Terms visible without extra action, accurate product names, no accidental-subscribe flow, eligibility-based discount disclosures where announced as effective. |
| Permissions | Merged manifest/runtime behaviour/core purpose versus console declarations: background location, FGS (with a video per type), full-screen intent, media/accessibility and other sensitive APIs. Name each restricted permission found (SMS, Call Log, MANAGE_EXTERNAL_STORAGE, QUERY_ALL_PACKAGES, REQUEST_INSTALL_PACKAGES, exact alarms, battery-optimization exemption, VPN). Compare the build against permission changes announced on the policy deadlines page. Each runtime permission is requested in context when its feature is used; data already granted gets fresh consent before a new use. |
| Code integrity | No self-update or executable code download outside Play, no JavaScript interfaces exposed to untrusted WebView content, no features enabled after review, no undisclosed bundled software, no SDK that proxies traffic, exfiltrates data or evades review. No code or SDK version that introduces or exploits a security vulnerability, including any Play Console reports for the app. |
| Listing | Title within the current length limit, no emoji or promotional claims in title or icon, no testimonials, all-ages graphics, no impersonation, non-promotional release notes. No keyword stuffing, word lists or comparisons with other apps; no ALL CAPS outside the brand or repeated special characters; no fake notification dot or download symbol on the icon; region or device differences and significant changes are stated. Ask how the app is promoted, including ad networks and affiliates: no ads resembling system alerts, no sexually explicit ads, no unsolicited SMS, no redirect to Google Play without user action (App Promotion). |
| Build/release | Upload/app-signing identity, versionCode/track, production configuration, target API and applicable native compatibility deadlines, and announced quality thresholds. |
| Production access | Account type/creation date and applicable testing/device verification; fetch current numbers and durations. Package name registration, organization-only categories with consistent D-U-N-S data, trader status declaration and regional payment authorizations. |

## Conditional modules

For ads/consent, kids, UGC/chat, AI, health/fitness, gambling/contests, financial services, location/VPN, monitoring or screen-capture features, news, licensed media and regulated activity, open applicable full policies via sources.md. Read special-cases.md for execution details. Mark uninspected applicable areas UNKNOWN rather than omitting them.
