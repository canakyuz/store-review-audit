# LinkedIn launch draft

Publish after the repository is public. Replace [REPOSITORY_URL].

---

App store reviews made me look more closely at what “ready to submit” actually means.

A working build is only part of it. Subscription terms, privacy declarations, age ratings, account deletion and reviewer access all need to match what the app really does.

I built Store Review Audit to make that process more explicit.

It combines an agent skill with a small Python validator:
• 27 control definitions across Apple and Google
• Evidence tied to the app, platform and submitted build
• Checks for missing locales and unresolved rejection issues
• Clear separation between a failed check and something we haven't verified

The agent investigates the app and current official policies. The validator checks whether the report contains the evidence it claims to rely on.

Missing evidence stays unknown. A failed test cannot be marked as passed.

It doesn't predict approval or replace a real device test. It helps make gaps visible before submission.

The source is available under MIT:
[REPOSITORY_URL]

I'd be interested to hear which review issues other mobile developers would add to the checklist.

#MobileDevelopment #OpenSource #AppStore #GooglePlay
