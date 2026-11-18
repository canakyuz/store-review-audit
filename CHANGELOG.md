# Changelog

## 0.2.0 (2026-11-18)

- Policy catalogue: `scripts/fetch_policies.py` lists every Apple App Review Guidelines clause, every Google Play Developer Program Policy page and every topic page in `sources.md`, with a hash of its normalised text and no policy text.
- Weekly policy watch: `.github/workflows/policy-watch.yml` compares the live policies with the catalogue every Monday and opens an issue when a clause changes, appears or disappears.
- Coverage map: `docs/policy-coverage.json` maps each clause and requirement to the controls; the gaps it found were added to `checklist.md` and `special-cases.md`.
- Delegation guidance for agents with subagents or smaller models, and a fallback when an official page cannot be fetched.
- Ledger contract: `scope.commit`, commit-bound code evidence (with `repo` for other repositories), a required `finding` on every FAIL, `UNKNOWN` for unestablished locales and territories, a gap when no policy was recorded, feature definitions in `rules.json`, a `third_party_login` gate for A03, and C01 now needs console and artifact evidence.
- Guidance for automatically created accounts, hidden opponents, severity levels and agents that cannot write files.

## 0.1.0 (2026-11-17)

- Initial release: agent skill, 27 control definitions, ledger initializer and validator.
