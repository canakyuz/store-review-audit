# Audit checklist

Use as evidence-gathering prompts. Confirm the current applicable rule before reporting a violation. Cover all baseline rows and applicable conditional rows; justify N/A.

## Baseline: both stores

| Area | Inspect |
| --- | --- |
| Scope | App ID, submitted build, store state, account type, legal publisher, countries and locales. |
| Account | Identity/membership verification, pending tasks, required agreements, monetization setup and regional trader/business disclosures. Do not accept agreements during an audit. |
| Reviewer access | Demo access, reproducible steps, OTP/MFA handling, gated features, live backend and attachments. Review notes explain the business model, steps for changed or non-obvious features and purchases, external services, regional differences, an expired-subscription account where relevant and a current contact. Keep secrets out of reports. |
| Quality | Launch/login/core task, errors/offline/denied permissions, purchase/deletion flows and supported layouts. No forced or incentivized ratings, no device-setting changes without consent, no imitation of system UI or alerts, no messages sent without the user confirming content and recipients, a prompt before large downloads, and the same behaviour during review as in production. Record actual tests performed. |
| Listing | Accurate claims/screenshots/icon/name/description/What's New/support URL; all locales and current dimensions. Items needing an extra purchase are marked; promoted purchases, in-app events, creative assets and pre-orders match the build; the listing is not a beta, demo or trial. |
| Documents | Privacy, applicable EULA/terms, subscription explanations, deletion instructions and contacts; public accessibility and correct identity. |
| Data inventory | Data type/source, recipient/SDK, purpose, collection/sharing, linkage/tracking, retention/deletion, security and consent. |
| Audience | Actual content, intended ages, ads/chat/UGC/web access, health, contests and currency mechanics. |
| Rights/originality | Asset/media/content rights and meaningful value/differences from sibling apps. Features that induce infringement or sell counterfeit goods. |
| Restricted content | App content, UGC, AI output and metadata against each store's prohibited categories (Apple 1.1 and 1.4, Google Restricted Content), independently of the age answers; fake official documents and personal data of people who did not consent. |

## Apple

| Area | Inspect |
| --- | --- |
| Core rules | Navigate current 2.1 completeness, 2.3 metadata, 3.1 payments, 4.2 functionality, 4.3 spam, 4.8 login, 5.1 privacy and 5.2 IP. |
| Purchases | IDs, availability, groups/entitlements and submitted-build configuration; purchase/restore/expiry and cancellation information. No paid item that only unlocks built-in hardware, OS capabilities or Apple services (4.10). |
| EULA | Standard EULA link in every localized description for subscriptions, or configured custom EULA/territories. Check in-app privacy/terms access separately. |
| App Privacy | Compare labels to app/partner data flows, distinguishing on-device from transmitted processing. |
| Native privacy | PrivacyInfo.xcprivacy, required-reason APIs, relevant SDK manifests/signatures, permission descriptions and ATT applicability. Manifests do not replace labels. |
| Deletion | Applicable in-app deletion and associated-data removal. Distinguish deactivation and subscription cancellation. |
| Rating/entity | Current questionnaire, regional result, content and relevant publisher-entity restrictions/review message. |
| Submission | Build processing, signing, entitlements, export compliance, current SDK requirements and IAP/review attachments. Binary: no private or deprecated APIs, no downloaded executable code, no hidden or obfuscated features, WebKit for web browsing, works on IPv6-only networks (2.5). |
| Platform technologies | Each entitlement, extension and framework the build uses (App Clips, widgets, keyboards, Safari extensions, SiriKit, CallKit, Apple Pay, Wallet, Game Center, MusicKit, Matter, Face ID) against its clause in 2.5, 4.4, 4.5 and 4.9. |
| Runtime conduct | Core function does not require push; marketing push is opt-in with an opt-out and carries no sensitive data; recording shows an indicator; no excessive battery or heat, no on-device mining; system controls and home screen unchanged; only the system review prompt. |

## Google Play

| Area | Inspect |
| --- | --- |
| App content | Needs attention plus existing privacy/ads/access/audience/rating/Data safety/sensitive-feature declarations. Social, chat and dating apps: published child-safety standards and contact; minor-blocking where the policy requires it. |
| Data safety | Reconcile SDK/backend behaviour with collection/sharing/purpose/security/deletion answers. Do not copy Apple answers mechanically. Prominent disclosure and affirmative consent before collection outside user expectations; identifier rules (persistent IDs not linked to the advertising ID, App Set ID not for ads); no sale of personal data. |
| Privacy | Listing and in-app policy, truthful data practices, retention/deletion and contact identity. The policy URL is public, labelled as a privacy policy, served over valid TLS, not geofenced, not behind a login and not a PDF. |
| Deletion | Applicable in-app path AND external deletion-request URL; real account/data removal and disclosed retention exceptions. The external resource names the app or developer as on the listing, needs no reinstall and covers accounts created outside the app. |
| Billing | Current Billing requirements, products/base plans/offers/markets, purchase/entitlement processing and regional alternatives eligibility. Anti-steering rules, purchases that must not use Play Billing, loot box odds. |
| Subscription UI | Localized billed price, interval, auto-renewal, trial conversion, recurring value, optional access and cancellation route. Terms visible without extra action, accurate product names, no accidental-subscribe flow, eligibility-based discount disclosures (announced for 2027-01-27). |
| Permissions | Merged manifest/runtime behaviour/core purpose versus console declarations: background location, FGS (with a video per type), full-screen intent, media/accessibility and other sensitive APIs. Name each restricted permission found (SMS, Call Log, MANAGE_EXTERNAL_STORAGE, QUERY_ALL_PACKAGES, REQUEST_INSTALL_PACKAGES, exact alarms, battery-optimization exemption, VPN). Compare the build against announced permission deadlines. |
| Code integrity | No self-update or executable code download outside Play, no JavaScript interfaces exposed to untrusted WebView content, no features enabled after review, no undisclosed bundled software, no SDK that proxies traffic, exfiltrates data or evades review. |
| Listing | Title within the current length limit, no emoji or promotional claims in title or icon, no testimonials, all-ages graphics, no impersonation, non-promotional release notes. |
| Build/release | Upload/app-signing identity, versionCode/track, production configuration, target API and applicable native compatibility deadlines, and announced quality thresholds. |
| Production access | Account type/creation date and applicable testing/device verification; fetch current numbers and durations. Package name registration, organization-only categories with consistent D-U-N-S data, trader status declaration and regional payment authorizations. |

## Conditional modules

For ads/consent, kids, UGC/chat, AI, health/fitness, gambling/contests, financial services, location/VPN, monitoring or screen-capture features, news, licensed media and regulated activity, open applicable full policies via sources.md. Read special-cases.md for execution details. Mark uninspected applicable areas UNKNOWN rather than omitting them.
