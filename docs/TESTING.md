# Validation

## 0.2.0 (2026-11-18)

- 49 automated tests pass locally on Python 3.12: validator, initializer and policy catalogue (parsing, hashing, change detection, fetch failure).
- The policy catalogue was built from the live sources twice in a row with identical hashes for all items, so page chrome does not produce false changes.
- The skill was used for full two-store audits of three private Expo apps (a generative-AI business tool, a health and coaching app with a social feed, and an online board game with a virtual currency and ads), each by an agent following SKILL.md with source code, built artifacts where present and public pages, and no console or runtime access.
  - Two apps ended BLOCKED with confirmed findings (missing in-app privacy link, unconsented audio upload to an AI provider, missing in-app deletion for an automatic account, unfiltered user posts, opponents not disclosed as house players). One ended INCOMPLETE with no confirmed failure. Sampled findings were checked against the source.
  - The agents filed 32 problem reports about the skill itself, many overlapping; the ones about the ledger contract, scope, severity, guest accounts, fetch failures and file output were fixed in 0.2.0.
- Known limit: support.google.com rate-limits bursts of scripted requests (HTTP 429). The catalogue script backs off and exits with code 2 without touching the catalogue; agents fall back as described in SKILL.md.

These tests do not prove store acceptance. GitHub Actions runs have not been executed yet.

## 0.1.0 (2026-11-17)

- 34 automated tests passed locally on Python 3.12; both fictional starter ledgers return INCOMPLETE with exit code 1.
