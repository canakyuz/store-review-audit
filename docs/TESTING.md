# Validation of the initial release

Date: 2026-11-17

- 34 automated tests passed locally on Python 3.12.
- Both fictional starter ledgers return INCOMPLETE with exit code 1, as intended.
- Relative Markdown links were checked.
- The source archive was extracted and its tests run again.
- GitHub Actions is configured for Python 3.10, 3.12 and 3.14. Hosted runs have not yet been executed.

These tests cover the report validator and initializer. They do not test an actual app, confirm a store declaration or measure real-world approval rates. Other Python versions are CI targets, not locally verified claims.
