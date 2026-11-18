# Store Review Audit

**Evidence-based release reviews for the Apple App Store and Google Play.**

An agent skill and a small Python validator that make release audits explicit: which build was checked, which policy applies, what evidence supports each result, and what remains unresolved.

**27 control definitions · Python standard library · MIT licensed**

## Why this exists

A release can have working code and still have missing subscription terms, inaccurate privacy declarations, inconsistent age ratings or an incomplete reviewer login.

This project gives an agent a repeatable investigation workflow and checks the resulting evidence ledger. Missing evidence stays unknown. Failed checks stay blocked. One store's evidence cannot silently stand in for the other.

## Two parts, two responsibilities

| Component | Responsibility |
| --- | --- |
| [Agent skill](SKILL.md) | Inspect the app, build, console and documents; consult current official policies; assess applicability and write findings. |
| [Python validator](scripts/validate_audit.py) | Check report structure, required controls, evidence types, app/platform/build identifiers, locale coverage and unresolved rejection records. |

The validator does **not** run an app, fetch policies, authenticate screenshots or prove legal compliance. It can reject an incomplete report; it cannot guarantee store acceptance. A fabricated but structurally valid evidence record can still pass its mechanical checks, so agent/human verification remains essential.

## Quick start

Requires Python 3.10 or newer. No pip dependencies, API keys or credentials are required for the local tools.

From the repository root:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

Create an honest starting ledger:

```sh
python3 scripts/init_audit.py \
  --platform apple \
  --app-id com.example.app \
  --build 42 \
  --locales en-GB tr \
  --territories GB TR \
  --output audits/apple-42.json
```

Every control starts as UNKNOWN. No policy checks, app tests or publisher facts are invented.

```sh
python3 scripts/validate_audit.py audits/apple-42.json
```

Expect INCOMPLETE and exit code 1 until the audit has real supporting evidence. Create a separate ledger with `--platform google` for Android.

## Use with an agent

Load [SKILL.md](SKILL.md) and keep its sibling `references/` and `scripts/` directories available. If your agent supports installed skills, register this complete folder using that client's installation process. Installation and invocation syntax vary by client.

Example prompt:

> Use store-review-audit to review build 42 of com.example.app for Apple and Google. Inspect available source, build artifacts, console settings and runtime evidence. Verify current official policies. Produce a report and a separate audit.json for each platform. Do not call missing evidence a pass or make live changes.

The skill works in the user's language. Its public edition defaults to English.

Browsing and app/console access are supplied by the agent environment, not this repository. Without that access, the correct output is a scoped report with explicit unknowns.

## Controls

The catalogue has 20 common, 3 Apple and 4 Google controls. A single-platform report therefore covers 23 or 24 controls, including conditional checks recorded as UNKNOWN or justified N/A.

| Area | Examples |
| --- | --- |
| Submission | Publisher eligibility, signing, build compatibility, reviewer access |
| Store listing | Accurate claims and complete localisation coverage |
| Subscriptions | Terms, EULA, price disclosure, renewal, purchase and restore evidence |
| Privacy | SDK/backend inventory, App Privacy, Data safety, deletion |
| Games | Virtual currency, wagers, prizes, age ratings and entity requirements |
| Conditional content | Ads, children, UGC/chat, AI, health, sensitive APIs and regulated services |

See [rules.json](references/rules.json) for exact evidence gates and [strict-mode.md](references/strict-mode.md) for the ledger format.

The gates are this project's internal proof requirements. They are **not** an official Apple or Google checklist and are not exhaustive across every possible app category.

## Results

| Verdict | Meaning | Exit |
| --- | --- | --- |
| INVALID | The report violates the evidence/structure contract. | 1 |
| BLOCKED | A confirmed applicable failure remains. | 1 |
| INCOMPLETE | Required evidence, coverage, applicability or rejection resolution is missing. | 1 |
| EVIDENCE_CONTRACT_COMPLETE | Mechanical coverage checks passed; evidence and policy interpretation still require review. | 0 |

Control-level states are PASS, FAIL, UNKNOWN and N/A. A passed score cannot cancel a failed control. “No login” does not establish “no data collection”. “No cash-out” does not establish “no simulated gambling”.

## Evidence requirements

- Record the app, platform, submitted build, territories and all configured locales.
- Recheck sources and evidence during the audit; do not merely rewrite old timestamps.
- Bind runtime, source and artifact evidence to the submitted build.
- Record runtime environment, steps, expected/actual result and outcome.
- Keep every distinct rejection issue open until its correction is verified.
- Require an evidence-backed applicability decision before using N/A.
- Reopen affected checks after changes to builds, SDKs, permissions, pricing or declarations.

Both scripts operate locally. The validator does not send network requests. Store audit output outside the public repository; `audits/` is ignored. Redact account credentials, tokens, personal data and private reviewer correspondence.

## Examples

[Apple starter](examples/apple-unknown.json) and [Google starter](examples/google-unknown.json) are deliberately incomplete, fictional examples. Their dates are examples, not evidence of a current inspection.

The test fixtures are also synthetic. They exercise the validator, not real store submissions.

## Development

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

The included GitHub Actions workflow runs this command on Python 3.10, 3.12 and 3.14. Its first hosted run happens after you publish the repository; a local run is not evidence that hosted CI passed.

For policy updates, follow [CONTRIBUTING.md](CONTRIBUTING.md): verify an official source, distinguish policy requirements from internal checks, and add a regression test for validator changes.

## Official sources

- [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Apple agreements and terms](https://developer.apple.com/support/terms/)
- [Google Play Developer Policy Center](https://play.google/developer-content-policy/)
- [Google Play review preparation](https://support.google.com/googleplay/android-developer/answer/9859455)

The [source map](references/sources.md) links topic-specific documentation. Revisit applicable policies for each release; deadlines, regional exceptions and console requirements change.

## Licence and attribution

[MIT](LICENSE). Copyright 2026 Bekircan Akyuz.

Apple and Google documentation remains owned by its respective rights holders. This repository provides original workflow instructions and source links; it does not relicense their policies. It is an independent project, not affiliated with or endorsed by Apple or Google.
