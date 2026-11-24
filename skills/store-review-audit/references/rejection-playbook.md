# Rejection playbook: fix, reply or appeal

Each statement in the Apple and Google Play sections paraphrases the official page named after it; the decision table and the reply section are this project's advice. Open the named page with scripts/fetch_policies.py --get <id> before acting, because channels and conditions change. scripts/diagnose_rejection.py lists the rules a notice cites.

## Choose per issue

| Situation | Path |
| --- | --- |
| The notice is right and the app or listing breaks the rule | Fix, then resubmit. Say what changed, in which build, and where the reviewer sees it. |
| The reviewer lacked a fact: a login, a hidden feature, a licence, why a permission is needed | Reply with the fact and its evidence. No new build unless the fact needs one. |
| You checked the rule's live text and the app complies | Appeal, with the specific reasons it complies. |
| The notice is unclear about what failed | Ask in the reply channel before changing anything. |

An appeal that argues with a correct notice costs a review cycle. A fix that hides the feature from review instead of changing it is a new violation (Apple 2.5.19, Google Deceptive Behavior).

## Apple

- Reply: use App Store Connect to communicate with App Review when you have questions or more information (`apple:after-you-submit`).
- Appeal: the App Review Board, when you believe the app's concept or functionality was misunderstood or you were treated unfairly. Give specific reasons the app complies, submit one appeal per submission that did not pass, and answer any request for more information before appealing (`topic:developer.apple.com/distribute/app-review`).
- Bug fix submission: for an app already on the store, a bug fix is not held back over guideline issues unless they are legal or safety issues. Reply to the offer message in App Store Connect to accept, and resolve the issue in the next submission (`apple:after-you-submit`, `topic:developer.apple.com/distribute/app-review`).
- Expedited review: for extenuating circumstances such as a critical bug fix or an event you are directly associated with. For a bug fix, include the steps to reproduce it on the current version. Abuse of the request may get later requests rejected (`apple:after-you-submit`, `topic:developer.apple.com/distribute/app-review`).
- Appointment: a meeting with App Review over video to discuss the guidelines (`topic:developer.apple.com/distribute/app-review`).
- Repeated rejection for the same guideline, or an attempt to manipulate review, makes later reviews take longer (`apple:after-you-submit`).

## Google Play

- Know the action: a rejection keeps the update off the store and does not affect account standing; a removal takes the app down and repeated removals can lead to suspension; a suspension counts as a strike; repeated or serious violations end in account termination (`google:policy:9899234`).
- A notice may not name every violation in the app, the account or the catalogue (`google:policy:9899234`).
- Appeal: follow the instructions in the enforcement email or the appeal form on the policy page. An action stays in effect unless the appeal is granted, and the app is reinstated when the decision was an error. Developers serving users in the European Economic Area may have further recourse (`google:policy:9899142`, `google:policy:9899234`).

## The reply

One numbered answer per cited issue, in the notice's order: the rule as cited, what was changed or what fact answers it, the build number, and the exact path a reviewer follows to see it. Past tense only for finished work. Attach evidence a reviewer can check without an account they do not have. Keep the tone factual; do not quote other apps as precedent.

Do not send a reply or appeal under audit-only authorization.
