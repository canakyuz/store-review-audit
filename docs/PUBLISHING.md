# Publishing the repository

Suggested name: `store-review-audit`

Suggested description:
> Evidence-based App Store and Google Play audits: agent skill, 27 control definitions and a dependency-free Python report validator.

Suggested topics:
`agent-skills`, `app-store`, `google-play`, `mobile-development`, `release-engineering`, `python`

## Before publishing

- Review the MIT licence and copyright attribution.
- Run the tests from the repository root.
- Publish this source folder, not a real audit ledger.
- The included examples and fixtures are synthetic.
- No GitHub URL is embedded because the destination repository has not been created yet.

## Push from a terminal

Create an empty repository on GitHub without adding an initial README or licence. Then run these commands inside the extracted store-review-audit folder. Replace the final placeholder URL with the URL GitHub gives you.

```sh
git init
git branch -M main
git add .
git commit -m "Initial release of Store Review Audit"
git remote add origin <YOUR_REPOSITORY_URL>
git push -u origin main
```

The repository URL above is a placeholder, not a working command as written. GitHub will require your own authentication.

After the first push, inspect the Actions run. If successful, create a release tagged `v0.1.0`. Describe it as an initial release and state that its tests cover the validator rather than real-world store acceptance.

## Share

Use [LINKEDIN_POST.md](LINKEDIN_POST.md) after publishing. Replace [REPOSITORY_URL] with the real URL. Do not claim the repository is live before it is published.
