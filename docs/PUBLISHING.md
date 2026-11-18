# Publishing

The repository is installed with the [skills CLI](https://skills.sh/):

```sh
npx skills add canakyuz/store-review-audit
```

The CLI copies only `skills/store-review-audit/` (SKILL.md, references and scripts). Everything else in the repository (README, docs, examples, CI) stays out of the installed skill.

## Releasing a version

1. Run the tests: `python3 -m unittest discover -s skills/store-review-audit/scripts -p 'test_*.py' -v`.
2. If policies changed, run `python3 skills/store-review-audit/scripts/fetch_policies.py --write` and review the changed clauses against the checklist, rules and special cases.
3. Update `VERSION` and `CHANGELOG.md`, commit, and push to `main`.
4. Check that the Tests workflow passed, then tag the release (`git tag v0.2.0 && git push origin v0.2.0`) and create a GitHub release that states what the tests cover and what they do not.

Never commit a real audit ledger: `audits/` is ignored for that reason.
