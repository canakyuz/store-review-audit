# Coin Quiz (benchmark fixture)

A fictional Expo trivia game used to measure the skill. It is not a real app and is never built. Some files contain deliberate policy problems; others are traps that look like problems but are not. The answer key lives in `bench/expected.json`, outside this folder: an auditor under test must not read it.

What an auditor may treat as evidence:

- Source and configuration in this folder, read at commit `bench0001`, which is the commit of build 12 (version 1.4.0).
- `store/console-export/`: exports from App Store Connect and Play Console taken on the audit date for this build. Treat them as console evidence.
- `site/`: the public legal pages, as served at https://coinquiz.example/privacy and https://coinquiz.example/terms.
- `store/review-message.txt`: the current App Review message for build 11.

There is no runtime access and no built artifact.

App: Coin Quiz, bundle ID and package `com.example.coinquiz`, publisher "Example Games Ltd" (organization account on both stores), territories GB and US, store locales en-GB, en-US and de-DE.
