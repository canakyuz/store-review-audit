# Audit checklist

Use as evidence-gathering prompts. Confirm the current applicable rule before reporting a violation. Cover all baseline rows and applicable conditional rows; justify N/A.

## Baseline: both stores

| Area | Inspect |
| --- | --- |
| Scope | App ID, submitted build, store state, account type, legal publisher, countries and locales. |
| Account | Identity/membership verification, pending tasks, required agreements, monetization setup and regional trader/business disclosures. Do not accept agreements during an audit. |
| Reviewer access | Demo access, reproducible steps, OTP/MFA handling, gated features, live backend and attachments. Keep secrets out of reports. |
| Quality | Launch/login/core task, errors/offline/denied permissions, purchase/deletion flows and supported layouts. Record actual tests performed. |
| Listing | Accurate claims/screenshots/icon/name/description/What's New/support URL; all locales and current dimensions. |
| Documents | Privacy, applicable EULA/terms, subscription explanations, deletion instructions and contacts; public accessibility and correct identity. |
| Data inventory | Data type/source, recipient/SDK, purpose, collection/sharing, linkage/tracking, retention/deletion, security and consent. |
| Audience | Actual content, intended ages, ads/chat/UGC/web access, health, contests and currency mechanics. |
| Rights/originality | Asset/media/content rights and meaningful value/differences from sibling apps. |

## Apple

| Area | Inspect |
| --- | --- |
| Core rules | Navigate current 2.1 completeness, 2.3 metadata, 3.1 payments, 4.2 functionality, 4.3 spam, 4.8 login, 5.1 privacy and 5.2 IP. |
| Purchases | IDs, availability, groups/entitlements and submitted-build configuration; purchase/restore/expiry and cancellation information. |
| EULA | Standard EULA link in every localized description for subscriptions, or configured custom EULA/territories. Check in-app privacy/terms access separately. |
| App Privacy | Compare labels to app/partner data flows, distinguishing on-device from transmitted processing. |
| Native privacy | PrivacyInfo.xcprivacy, required-reason APIs, relevant SDK manifests/signatures, permission descriptions and ATT applicability. Manifests do not replace labels. |
| Deletion | Applicable in-app deletion and associated-data removal. Distinguish deactivation and subscription cancellation. |
| Rating/entity | Current questionnaire, regional result, content and relevant publisher-entity restrictions/review message. |
| Submission | Build processing, signing, entitlements, export compliance, current SDK requirements and IAP/review attachments. |

## Google Play

| Area | Inspect |
| --- | --- |
| App content | Needs attention plus existing privacy/ads/access/audience/rating/Data safety/sensitive-feature declarations. |
| Data safety | Reconcile SDK/backend behaviour with collection/sharing/purpose/security/deletion answers. Do not copy Apple answers mechanically. |
| Privacy | Listing and in-app policy, truthful data practices, retention/deletion and contact identity. |
| Deletion | Applicable in-app path AND external deletion-request URL; real account/data removal and disclosed retention exceptions. |
| Billing | Current Billing requirements, products/base plans/offers/markets, purchase/entitlement processing and regional alternatives eligibility. |
| Subscription UI | Localized billed price, interval, auto-renewal, trial conversion, recurring value, optional access and cancellation route. |
| Permissions | Merged manifest/runtime behaviour/core purpose versus console declarations: background location, FGS, full-screen intent, media/accessibility and other sensitive APIs. |
| Build/release | Upload/app-signing identity, versionCode/track, production configuration, target API and applicable native compatibility deadlines. |
| Production access | Account type/creation date and applicable testing/device verification; fetch current numbers and durations. |

## Conditional modules

For ads/consent, kids, UGC/chat, AI, health/fitness, gambling/contests, financial services, location/VPN, licensed media and regulated activity, open applicable full policies via sources.md. Read special-cases.md for execution details. Mark uninspected applicable areas UNKNOWN rather than omitting them.
