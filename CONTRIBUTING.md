# Contributing

Keep the project strict about evidence and careful about policy claims.

## Changes to policy guidance

1. Link the current official Apple or Google source and the relevant section.
2. Record effective dates and regional/platform limits.
3. Say whether the change is a store requirement or an internal evidence gate.
4. Do not copy long policy passages or hard-code volatile thresholds without a refresh workflow.
5. Update the source map and applicable instructions together.

## Changes to the validator

Add a regression test that reproduces the failure, then run:

```sh
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

Include a valid case when tightening validation so legitimate reports are not silently blocked. Keep the scripts dependency-free and preserve the distinction between UNKNOWN and FAIL.

Use synthetic app IDs and data. Never include live receipts, credentials, user data, account screenshots or private rejection correspondence in a pull request.

## Pull requests

Explain the concrete before/after behaviour, what evidence supports the change and which tests ran. Do not label a structural validator improvement as a guarantee of store approval.
