# Changelog

## 0.4.0 (2026-11-19)

- The catalogue also watches the Apple Developer Program License Agreement, App Store Connect screenshot specifications, Google's target SDK requirements, the Data safety form and Play store listing graphics (214 items).
- Google digest accuracy: an independent check of 80 random requirements found 73 correct, 7 imprecise and none wrong; a full pass then corrected 30 more sentences where "should" had become "must" or a condition had been dropped.
- Coverage recheck of all 596 Google requirements and open Apple clauses against the skill: 30 that ordinary apps can break were not reached by any checklist line; ten added sentences now cover them.
- `fetch_policies.py --get ... --grep WORD` prints only the relevant sentences.
- The policy watch can rewrite the catalogue on demand and reports the branch through an issue.
- Clarified: code that shows a behaviour can support FAIL, G04 for organization accounts, review-message records, returning the report when files cannot be written.

## 0.3.1 (2026-11-18)

- `fetch_policies.py --list WORD` finds catalogue ids by title.
- A FAIL can hold several distinct problems in `issues`, each with its own severity, fix, retest and area (code, console, document, account); reports group fixes by area.
- `sources.md` points at the policy pages the catalogue keeps (three help-centre answers were duplicates).
- Features for review-only gates (hidden for review, switched on later), kids decided from the app's own terms without console access, generated native files as code evidence.
- README: how to check for and install updates.

## 0.3.0 (2026-11-18)

- Benchmark: `bench/coin-quiz` is a fictional app with 15 seeded store problems and 14 traps, `bench/expected.json` is its answer key and `bench/score.py` scores an audit against it.
- Google policy digest: `references/policy-digest.json` paraphrases every requirement of every Google Play policy page (528 requirements, 22 announced changes), verified against the page text and bound to the catalogue hash. Audits use it when support.google.com cannot be fetched; tests fail when a page changes and its entry is not rewritten.
- `fetch_policies.py --get ID [ID ...]` fetches the items an audit needs in one call, takes `apple:5.3*` for a clause and its sub-clauses, falls back to the digest and stops at once on captcha pages.
- Ledgers can cite a policy via the digest and a store review message as the authority for its submission.
- The weekly policy watch records the check date when nothing changed, which keeps the digest usable.
- Clearer rules: one observation can fail several controls, how to decide kids, UGC, regulated and sensitive permissions, loot-box odds, evidence kinds for repository configuration, where the report goes.

## 0.2.0 (2026-11-18)

- Policy catalogue: `scripts/fetch_policies.py` lists every Apple App Review Guidelines clause, every Google Play Developer Program Policy page and every topic page in `sources.md`, with a hash of its normalised text and no policy text.
- Weekly policy watch: `.github/workflows/policy-watch.yml` compares the live policies with the catalogue every Monday and opens an issue when a clause changes, appears or disappears.
- Coverage map: `docs/policy-coverage.json` maps each clause and requirement to the controls; the gaps it found were added to `checklist.md` and `special-cases.md`.
- Delegation guidance for agents with subagents or smaller models, and a fallback when an official page cannot be fetched.
- Ledger contract: `scope.commit`, commit-bound code evidence (with `repo` for other repositories), a required `finding` on every FAIL, `UNKNOWN` for unestablished locales and territories, a gap when no policy was recorded, feature definitions in `rules.json`, a `third_party_login` gate for A03, and C01 now needs console and artifact evidence.
- Guidance for automatically created accounts, hidden opponents, severity levels and agents that cannot write files.

## 0.1.0 (2026-11-17)

- Initial release: agent skill, 27 control definitions, ledger initializer and validator.
