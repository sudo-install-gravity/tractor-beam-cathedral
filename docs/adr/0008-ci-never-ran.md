# ADR 0008 — Why CI has never run: not determined; escalated to GitHub Support

- **Status:** Escalated (unresolved)
- **Date:** 2026-08-09
- **Sprint:** 13 (SPIKE-13.1)
- **Discharges:** the owner-only diagnostic step blocking T-13.2 and everything transitively
  behind it

## Context

The manuscript's Methods states that citation discipline is "enforced in continuous
integration." Verified 2026-08-06: `actions/runs` reports `total_count: 0` for the entire
history of `sudo-install-gravity/tractor-beam-cathedral` — the five gates have run on every
commit **locally**, never on the remote. The enforcement claim is true of a script and
false of a pipeline until this closes.

`docs/BACKLOG.md`'s diagnostic table had already eliminated everything checkable without
repository-admin access: the workflow file is present, well-formed, and registered as
`state: active` (id `325748978`); the repository is not a fork, not archived, not
disabled; the job matrix (`test (3.10)`, `test (3.11)`, `test (3.12)`) satisfies T-2.9's
acceptance criterion. One hypothesis remained untested — **Actions disabled in repository
or account settings** — because `actions/permissions` requires admin and the available
`gh` token (`Thanatos7777`) has `push: false`, read-only, on this repo.

## What the owner checked (2026-08-09), in the order the spike specifies

1. **Settings → Actions → General, repo level.** "Allow all actions and reusable
   workflows" is already selected. **Eliminated.**
2. **Account-level Actions policy, `github.com/settings/actions`.** Returns **404**. This
   is not evidence of a restriction — personal GitHub accounts have no account-wide
   Actions policy page at all; that page exists only for organizations. The spike's
   original hypothesis (a user-level policy disabling Actions across all repos) **does
   not apply to this account type** and is eliminated on that basis, not by inspection of
   a setting that doesn't exist.
3. **The Actions tab itself.** No banner (no "workflows aren't being run on this forked
   repository," no disabled-due-to-inactivity notice). **Eliminated**, with one adjacent
   finding: **Workflow permissions** (a separate control from Actions permissions, also
   under Settings → Actions → General) is set to "Read repository contents and packages
   permissions," not "Read and write." This governs what the auto-provisioned
   `GITHUB_TOKEN` may do **inside** an already-running job (e.g., push a commit back); it
   does not gate whether a run is triggered in the first place. If this were the cause,
   the symptom would be *failing* runs, not *zero* runs. **Ruled out as the explanation
   for `total_count: 0`**, though worth flipping to read+write as good practice
   independent of this spike.
4. **Billing / plan.** Free tier. The repository is `visibility: public`, which carries
   unlimited Actions minutes on free tier — not the constrained private-repo allowance.
   **Eliminated**, consistent with the spike's own prediction that exhausted minutes
   would produce failed runs, not absent ones.

**All four of the spike's listed hypotheses are now eliminated or inapplicable.**

## Live diagnostic test, performed the same session

Rather than continue inspecting settings pages, a real trigger test was run: a genuine
commit (`30efb77`, "SPIKE-13.1 diagnostic: trivial push to test whether Actions fires at
all") was pushed to `main` via the normal `git push newhome main` path — the same path
every one of the prior 64+ pushes used.

Confirmed immediately after, via the GitHub API:

- The commit **is** on GitHub's `main`: `GET /repos/.../commits/main` returns SHA
  `30efb77d58c2e2ef9f9b0d7c333907c98a5e16ba`, dated `2026-08-09T04:11:50Z`.
- The workflow **is** registered and active: `GET /repos/.../actions/workflows` returns
  `{"id": 325748978, "name": "CI", "path": ".github/workflows/ci.yml", "state": "active"}`.
- The workflow file **as GitHub sees it** (fetched via the Contents API, not from local
  disk) has the expected, unrestricted trigger: `on: push: branches: [main]` (plus
  `pull_request: branches: [main]`), no `paths:` filter, no other restriction.
- The repository **is** healthy: `default_branch: "main"`, `fork: false`,
  `archived: false`, `disabled: false`, `visibility: "public"`.
- `GET /repos/.../actions/runs` **immediately after the push** still returns
  `{"total_count": 0, "workflow_runs": []}`.

Every precondition GitHub documents for a push-triggered workflow run is satisfied, and
the run still did not fire.

## Confirmation under the repository owner's own credentials (2026-08-09, same day)

The diagnostics above were all read under the `Thanatos7777` `gh` token, which has only
read access to this repository — sufficient for everything except the one
admin-gated endpoint. The owner authenticated `gh` as `sudo-install-gravity` (device-code
flow, so no password or token ever passed through an agent) and the previously-403
endpoint was retried directly:

```
$ gh api repos/sudo-install-gravity/tractor-beam-cathedral/actions/permissions
{"enabled":true,"allowed_actions":"all","sha_pinning_required":false}
```

This is first-party confirmation from GitHub's own API, under the account that actually
owns the repository, that Actions are `enabled: true` with `allowed_actions: "all"` —
removing any remaining doubt that the repo-level Actions-permissions hypothesis (item 1
above) might have looked open in the UI but read differently to GitHub's backend. It
does not change the finding: Actions being enabled was never in question after the
owner's own UI check: this closes the last gap in the evidence trail with authoritative
data rather than a settings-page screenshot.

## Decision

**The cause is not determined. Per this spike's own acceptance criterion — "if none of
the four explains it, the ADR says so and the spike escalates rather than guessing" —
this is recorded as an open finding, not resolved with a plausible-sounding guess.**

A guessed cause recorded without evidence would be worse than the open question it
replaced (`CLAUDE.md` rule 1, applied to infrastructure rather than physics): a future
contributor trusting a wrong diagnosis here would stop looking in the one place — GitHub's
own backend state — that neither the repository settings UI nor the REST API exposes to
anyone without direct platform access.

**Escalation path: GitHub Support.** Every hypothesis checkable from the outside —
repository configuration, account-visible settings, workflow file content and
registration, live trigger behavior — has been checked and eliminated. What remains is
account- or repository-level state not exposed through the public UI or API: for example,
a spam/abuse-review flag silently suppressing Actions for an account, which GitHub is
known to apply without a corresponding settings-page indicator. Confirming or ruling this
out requires a support ticket from the account owner; no diagnostic available to this
project can reach further.

## Consequences

- T-13.2 (confirm a green CI run) remains blocked, now on a GitHub Support ticket rather
  than on repository configuration. **This is a genuine external dependency**, not a task
  that can be worked around by trying another setting.
- The manuscript's ⚠️ caveat added 2026-08-06 ("citation discipline is enforced locally,
  not yet in GitHub Actions") stays in place. T-13.3 must not remove it until T-13.2 is
  green — this ADR's finding does not change that gate.
- `tools/check_ci_status.py` (T-13.4) should treat `total_count: 0` after a fresh push as
  its own distinct, named failure mode ("CI has never triggered despite a fresh push"),
  not conflated with "CI ran and failed" or "no runs yet because nothing has been pushed."
- If the support ticket resolves the issue, close this ADR's Status to **Resolved** with
  the actual cause GitHub identifies, rather than leaving it silently fixed — an
  unexplained fix is exactly the kind of gap this project's own citation and provenance
  discipline exists to prevent in the physics; the same standard applies to its
  infrastructure.

## Claims classification

Infrastructure finding, not a physics claim — outside `docs/CLAIMS.md`'s A/B/C taxonomy.
Recorded here and cross-referenced from `docs/HANDOVER.md` and `docs/BACKLOG.md` instead.
