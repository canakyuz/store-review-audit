# Validation

## 0.4.0 (2026-11-19)

- 65 automated tests pass locally and on GitHub Actions.
- Benchmark run 3 with the 0.4.0 candidate, from a clean install: 15 of 15 seeded problems caught, 0 of 14 traps failed, 54 of 54 checks (156k agent tokens).
- Google digest: 80 random requirements checked against the page text by an independent agent, 73 correct, 7 imprecise, 0 wrong; all 550 sentences were then rechecked for the two error types found and 30 were corrected.
- Coverage: 596 requirements checked against the skill text; 425 reached by a specific line, 141 routed to the full policy (niche categories), 30 missed and now covered.

## 0.3.0 (2026-11-18)

- 62 automated tests pass locally on Python 3.12.
- Benchmark (`bench/score.py`), each run by a fresh agent from a clean install of the skill, with no access to the answer key, on a machine where support.google.com returned HTTP 429 to every request:

| Skill version | Seeded problems caught | Traps failed | All checks | Agent tokens |
| --- | --- | --- | --- | --- |
| 0.2.0 | 7 of 15 (Apple 7 of 7, Google 0 of 8) | 0 of 14 | 43 of 54 | 139k |
| 0.3.0 candidate, run 1 | 15 of 15 | 0 of 14 | 54 of 54 | 149k |
| 0.3.0 candidate, run 2 | 15 of 15 | 0 of 14 | 53 of 54 (Apple kids feature undecided: the fixture lacked the category, now added) | 154k |

  With 0.2.0 the agent could read no Google policy and correctly kept every Google finding UNKNOWN; the digest fixed that. The benchmark is one small fictional app: it shows the skill finds what it is meant to find there, not that it finds everything in a real app.

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
