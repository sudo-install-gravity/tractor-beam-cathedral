# HANDOFF — Sonnet session: T-12.7, then T-12.8 (the project's last two tasks)

**Written 2026-08-10, supersedes the now-consumed Opus/T-12.5 handoff.**
**Assume zero conversational context.** Everything needed is in the files named here.

## Recommendation: switch THIS session's model to Sonnet, in place

**Switch in place. Do not start a new session.** Context here is free; re-deriving it cold costs
real tokens for no benefit — this project measured ~190k tokens lost to a single cold subagent
dispatch that never wrote a file (see `CLAUDE.md`, "Which model runs a task").

T-12.5 was the last `opus`-tier task in the backlog. Everything remaining is Sonnet:

```
── Session 1 · SONNET · 2 tasks · 4 pts · sprint 12 ────────
   T-12.7     [standard] 2pt  Contributor on-ramp
   T-12.8     [low     ] 2pt  v1.0 release  after T-12.7
```

Run `python tools/schedule.py --next` to confirm this is still current before starting.

T-12.7 is `sonnet` (not `sonnet-low`) because "a reader with no prior context can run it" is a
judgment call about prose aimed at humans, which is the middle tier's definition. T-12.8 is
`sonnet-low` — it is a checklist.

## State of the world

The entire backlog is done except T-12.7 and T-12.8. As of 2026-08-10:

- **T-12.5 closed** — `docs/PHYSICS.md` is complete: no `[UNVERIFIED]` markers, every Category B
  claim (B-1…B-9) carries a derivation and a reducing limit, indexed in its new §10.
- `tools/gates.py` green: **1193 passed, 3 skipped**.
- CI green and enforced; `main` is branch-protected (see "The PR workflow" below).

## T-12.7 · Contributor on-ramp · 2 pts · `sonnet` · deps T-12.5 (satisfied)

`docs/GETTING_STARTED.md` — **does not exist yet; you are creating it.** From clone to first
contribution.
*AC: a reader with no prior context can run the E2E scenario.*

The E2E scenario is **`examples/deflection_scenario.py`** (landed 2026-08-10, T-12.1) — geometry
to gap report in one script. Run it yourself before writing about it; the AC is about a real
reader succeeding, so a path you did not execute is a guess.

What the document has to carry, at minimum:

1. **Clone → working venv.** The host is Windows 11 and the venv is at `.venv`. Use
   `.venv\Scripts\python.exe` for everything; the system Python has no numpy. Name the
   application — "Windows PowerShell", not "a terminal" (machine-wide rule, `~/.claude/CLAUDE.md`).
2. **The five-command sanity check** — already written up in `docs/HANDOVER.md` §1. Do not
   reinvent it; point at it or lift it verbatim.
3. **Running the E2E scenario**, with what its output means. Its gap report is the project's
   whole point: it prints the quantitative distance to an actual deflection.
4. **How to make a change that will be accepted** — the RESEARCH → IMPLEMENT → REVIEW → INDEX
   workflow, the Definition of Ready/Done, citation discipline (rule 1), and the PR flow below.
   `CONTRIBUTING.md` already exists; **read it first and cross-link rather than duplicating it.**
5. **The traps a newcomer will actually hit**, all documented in `docs/HANDOVER.md` §6: cp1252
   breaking `schedule.py` (set `PYTHONIOENCODING=utf-8`), CRLF on checkout, and the broken
   Windows console shims — `mypy.exe`/`pytest.exe` exit 1 with no output, so always run
   `.venv\Scripts\python.exe tools\gates.py` rather than composing the gates by hand.

Do not restate the physics. `docs/PHYSICS.md` is the argument and it is now complete; this
document's job is to get someone to the point where they can read it.

## T-12.8 · v1.0 release · 2 pts · `sonnet-low` · deps T-12.1–T-12.7

Repo-level: tag, release notes, Zenodo DOI for citability.
*AC: all 8 benchmarks pass; CI green; ledger publishes all four walls quantitatively.*

⚠️ **The AC says "all 8 benchmarks" but `tests/benchmarks/` currently holds 12 test modules**
(`test_array_factor`, `test_binary`, `test_body_sensitivity`, `test_diffraction`,
`test_dipole_cancellation`, `test_energy_conservation`, `test_focusing`, `test_hulse_taylor`,
`test_memory`, `test_performance`, `test_smoke`, `test_spinning_rod`). The "8" was written at
Sprint 0 planning and the suite grew past it. **Do not delete four benchmarks to make the number
match** — that would be deleting a wall in the most literal way. Reconcile the count in the AC,
say so in the release notes, and note it in the backlog entry when you close the task.

The four walls the ledger must publish quantitatively: **diffraction, coupling, magnitude,
transducer** (`docs/PHYSICS.md` §8; `src/gwtb/ledger/`). Confirm the gap report actually prints
all four before claiming the AC — C-2's headline figure is **−6.75 to +29.25 decades**, not the
"~40 orders of magnitude" that predated the R5 campaign and was corrected on 2026-08-03. Do not
reintroduce the old number into release notes.

`CITATION.cff` exists at the repo root and will need its version and date updated.

**Zenodo requires a repository-settings-level action** (enabling the GitHub–Zenodo integration).
That is an outward-facing, hard-to-reverse change to the owner's account. **Ask the owner before
touching it** — the branch-protection approval from T-2.9 does not carry forward to a different
kind of change.

## Workflow (binding, from `CLAUDE.md`)

RESEARCH → IMPLEMENT → REVIEW → INDEX. Neither remaining task adds a physics formula, so RESEARCH
is light — but **invoke `code-reviewer` before considering either task done**, and `indexer` after
T-12.7 creates a new document. Those three support agents are not a tier and still run at every
tier; the caution in `CLAUDE.md` is about dispatching *batches of implementation work* to a cold
agent, which is a different thing.

## The PR workflow (mandatory — `main` is protected)

```
git checkout -b <short-descriptive-branch-name>
...edit, commit...
git push newhome <branch-name>
gh pr create --repo sudo-install-gravity/tractor-beam-cathedral --base main --head <branch-name> --title "..." --body "..."
# wait for the three checks (test 3.10/3.11/3.12) to go green, then:
gh pr merge <number> --repo sudo-install-gravity/tractor-beam-cathedral --squash --delete-branch
# then sync local main:
git checkout main && git fetch newhome && git reset --hard newhome/main
git branch -D <short-descriptive-branch-name>   # squash-merges never show as "fully merged" locally -- expected, safe to force-delete after confirming the PR merged
git remote prune newhome
```

**Before merging, always confirm the green check run is for the PR's actual current head**
(`gh pr view <n> --repo sudo-install-gravity/tractor-beam-cathedral --json headRefOid`) — a stale
check result from an earlier push in the same PR looks identical to a fresh one at a glance.

⚠️ **`gh pr create`/`checks`/`merge` without `--repo` resolve against `origin`**, which on this
checkout is a stale fork (`Thanatos7777/tractor_beam_cathedral`), not
`sudo-install-gravity/tractor-beam-cathedral` (`newhome`). Always pass `--repo` explicitly.

`jq` is **not installed** — use `gh pr checks <n>`'s plain-text output and string-match it, not
`--json` + `jq`.

## Traps

1. **`gh` identity:** active account is `sudo-install-gravity` (repo owner, admin).
   `Thanatos7777` is also stored but read-only. `gh auth status` confirms.
2. **Windows console shims are broken** — `mypy.exe`/`pytest.exe` exit 1 with no output. Always
   run `.venv\Scripts\python.exe tools\gates.py` (all five gates, honest reporting).
3. **cp1252** — `schedule.py` and any script printing the docs' unicode dies on Windows unless you
   set `PYTHONIOENCODING=utf-8`. This bites constantly; set it by reflex.
4. **`examples/` and `docs/` are covered by the gates**, not just `src/`/`tests/`/`tools/`. A new
   `docs/GETTING_STARTED.md` will not trip ruff/mypy, but anything you add under `examples/` will.
5. **Backlog task-header grammar is rigid** (`· 2 pts ·`, never `· 2 pt ·`); run
   `python tools/schedule.py --plan` after editing any header.
6. **Mark a task ✅ on its header when you finish it** — `tools/schedule.py` reads completion from
   those markers, so an unmarked finished task will keep being scheduled.

## When blocked

Record the blocker under the task in `docs/BACKLOG.md` with a date and leave it un-✅'d. Never
delete a wall (rule 5); never guess a citation and mark it verified (rule 1). An honest unresolved
marker beats a confident wrong one — the standard this project applied to EQ-040's near-miss, and
again to B-8's reduction gap in T-12.5.

## Known open items, deliberately not fixed by T-12.5

Both were found during T-12.5's review and are out of its scope. Neither blocks T-12.7 or T-12.8;
pick them up only if you have budget after both close.

1. **`docs/adr/0003-spin2-superposition.md` is stale** on the finite-`N` alignment-bias precedent:
   it still frames the citation question as open, while `CLAIMS.md`'s 2026-08-03 entry and
   `INDEX.md`'s EQ-054 both record the resolution (D'Addario 2008 eq. 5 is the precedent for the
   N-dependence skeleton; Ruze gives only the `N → ∞` limit). `PHYSICS.md` §5.1 is consistent with
   the *current* record, not the stale ADR.
2. **`docs/INDEX.md` §4 has no validation-status row** for the T-14.5/T-14.6 tradespace grid or
   B-9's `d²`-cancellation test (`tests/unit/test_tradespace.py`), although §2's module map and
   `CLAIMS.md` both reference it.

## After T-12.8

That is the last task in the backlog. The project ships v1.0 and the remaining open questions are
the ones it was built to state honestly rather than close: **C-1** (the transducer, out of scope
by charter), **C-2** (whether the gap is closable at all — quantified, not resolved), **C-3** (a
~6×10⁹-wavelength aperture), and **C-4** (any non-radiative coupling that scales).
