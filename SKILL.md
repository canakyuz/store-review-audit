---
name: store-review-audit
description: Audit iOS App Store and Android Google Play submissions against current official policies, diagnose rejection messages, and prepare evidence-based fixes, declarations, EULA/privacy documents and review replies. Use for release preflight, App Review rejection, Play policy violation, subscriptions/IAP, age ratings/simulated gambling, privacy/Data safety, SDK permissions, spam/minimum functionality, or requests such as mağaza kontrolü, red sebepleri, yayın öncesi denetim, sözleşme kontrolü. Supports Expo/React Native, RevenueCat, AdMob, games, AI and fitness apps.
---

# Store Review Audit

Respond in the user's language; default to English. Explain the concrete blocker first. Audit the requested app/build; never assume sibling apps share settings. Do not promise approval or claim access to an internal reviewer checklist. Public policies, console requirements and app-specific messages are the evidence base.

## Workflow

For full preflight audits, strict mode is mandatory. Read [strict-mode.md](references/strict-mode.md) and [rules.json](references/rules.json); produce the structured evidence ledger and run scripts/validate_audit.py before any final readiness conclusion. These are internal proof requirements, not additional store policies. Never bypass a failed gate with a summary score.

1. Establish platform, app/package/bundle ID, build/version, release track, countries, localizations, publisher account type, monetization and rejection date from available evidence. Separate history from the current build. Retrieve relevant connected evidence before asking questions; do not block initial analysis on a long questionnaire.
2. Read [sources.md](references/sources.md). [policy-catalog.json](references/policy-catalog.json) lists every Apple guideline clause, Google policy page and topic page with a content hash; docs/policy-coverage.json maps each to the controls for maintenance and need not be read during an audit. If the catalogue's `checked` date is older than 14 days, run scripts/fetch_policies.py --check and read changed items first. Once features are known, open only the clauses and pages that apply, plus the policy indexes to catch new pages. Record access date, section, scope and effective date. Distinguish active rules from announced changes. Read full policies, not only snippets/summary boxes. Treat checklists as investigation prompts, not immutable rules. If sources are unavailable, label currency unverified and continue with available evidence.
3. Cover every baseline category and applicable conditional category in [checklist.md](references/checklist.md). Use [special-cases.md](references/special-cases.md) for games, subscriptions, AI/health/kids and common mobile stacks. Keep Apple/Google findings separate.
4. Triangulate actual behaviour, submitted build/configuration, console declarations and public store/legal pages. Prefer connectors; use the user's browser when necessary, following its instructions. Inspect provided code/artifacts. Never claim runtime validation from source code alone.
5. Assign PASS, FAIL, UNKNOWN or N/A. PASS requires evidence; N/A requires an applicability reason. Give FAIL severity separately: BLOCKER for an explicit submission/review blocker, HIGH for a supported likely violation, MEDIUM for a narrower issue. Label usability suggestions recommendations, not mandatory rules. Preserve material unknowns and the evidence needed.
6. Report using [report-template.md](references/report-template.md), scaled to the request. Map every rejection paragraph to a finding. Separate console/metadata fixes, public-document fixes, new-build fixes and account/business changes. Draft reviewer replies only from verified facts and completed changes.
7. If fixes are authorized, perform reversible work in scope and verify it. Do not falsify ratings/disclosures, fabricate documents or hide functionality. An audit or skill-creation request does not authorize live edits, accepting legal agreements, account conversion, sending reviewer messages or submitting/publishing. Use existing explicit authorization without repeatedly asking.

## Delegation

Policy reading is the largest cost of an audit. If your environment can run subagents or a smaller model, give each worker the applicable clauses or pages for one platform and ask for verbatim quotes with URL, section and access date, in the ledger's `policies` format. Keep applicability, PASS/FAIL, declaration conflicts and legal drafts with the main agent. Audit Apple and Google in separate contexts when possible. Without subagents, do the same steps yourself.

## Evidence rules

- Locate findings precisely: file/line, screen, console field, URL, locale, build or product ID. Redact credentials, personal data and test-account secrets.
- Audit declarations per platform/build/territory/locale. For an EULA issue, inspect every configured store-description localization, not only English/Turkish.
- Verify useful accessible link content and correct app/developer identity; HTTP 200 alone is insufficient. Distinguish privacy policy, EULA, subscription terms, support and deletion URLs.
- Retain submission-specific review-message requirements separately from broader policy interpretation. Do not invent a universal rule number when the message is more specific.
- Distinguish missing evidence from a confirmed defect. If a user reports a fix but it cannot be inspected, mark its verification UNKNOWN and the original rejection unresolved; do not invent a fresh confirmed failure. For conditional requirements, establish applicability before assigning FAIL.
- Fetch exact volatile requirements: SDK/Xcode/target API/Billing versions, testing counts/duration, deadlines, regional payment exceptions, age bands and asset dimensions.
- Never infer no data collection from no login. Inspect ads, analytics, crash reporting, backend logs and AI providers. Do not infer tracking solely from an ad SDK.
- Tie privacy/EULA drafts to verified practices. Mark unknown legal identity, contact, processors and retention explicitly. Do not invent legal obligations or assert blanket legal compliance.
- Treat test recommendations as engineering validation unless an official source specifically mandates them.

## Completion

Use “blocked”, “incomplete evidence”, or “no blockers found in inspected scope”. Any confirmed applicable policy failure prevents readiness regardless of severity; any required UNKNOWN or missing control prevents a full-readiness claim. Verify the machine-readable report AND semantically inspect the underlying evidence; passing the validator alone cannot establish compliance. Never give an approval probability.
For narrow questions, answer directly with official sources. For full audits, include coverage, missing evidence and prioritized fixes. Save requested reports/documents through the active file-storage workflow. Do not schedule recurring work or publish documents unless requested.
