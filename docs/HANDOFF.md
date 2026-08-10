# HANDOFF — endgame Sonnet batch (written 2026-08-10; supersedes the consumed Sprint 14 handoff)

**Assume zero conversational context.** Everything needed is in the files named here.

## State of the world

Sprint 14 is fully landed. CI went green for the first time on 2026-08-10 — run
31350735475, all three matrix jobs (`test (3.10)`, `test (3.11)`, `test (3.12)`) — after
SPIKE-13.1 resolved (a UI-only "Enable GitHub Actions" control; ADR-0008 has the story,
including the GitHub API misreporting `enabled: true` the whole time). T-13.2 and T-13.3
are closed. **13 points remain in the entire backlog.**

## The batch

Five Sonnet-tier tasks, specs in `docs/BACKLOG.md` (search each ID), runnable in this
order:

1. **T-13.4** · `tools/check_ci_status.py` · 2 pts · `sonnet-low`. Queries `actions/runs`
   for `main`, reports newest run's conclusion and age. Exit 0 only when newest run is
   `success`; exit 1 with a **named** reason for zero runs, non-success, or a run older
   than current HEAD. Per ADR-0008's consequences: `total_count: 0` after a fresh push is
   its own named failure mode ("CI has never triggered despite a fresh push"), distinct
   from "ran and failed". Deliberately NOT a pytest test and NOT a sixth gate (needs
   network + credentials). Document in `HANDOVER.md` §8 as on-demand.
2. **T-2.9** · branch protection · 1 pt · `sonnet-low` · **needs the owner's explicit
   go-ahead before executing** (it changes repository settings), then
   `gh api -X PUT .../branches/main/protection` under the `sudo-install-gravity` account
   (active in `gh` since 2026-08-09). AC: the protection API returns
   `required_status_checks` naming the three matrix jobs. The old "checks have never
   reported" blocker note in the task body predates CI going green — the checks HAVE now
   reported, so it is stale; update it when closing.
3. **T-12.1** · `examples/deflection_scenario.py` · 3 pts · `sonnet`. 1 km asteroid at
   40 AU, N-element array, prime-band drive. AC: runs to completion; emits field viz,
   beam pattern, Δv, miss distance, gap report.
4. **T-12.4** · `tests/unit/test_properties.py` · 2 pts · `sonnet-low`. Dimensional
   consistency, TT idempotency, superposition linearity across the public API. AC: all
   public physics functions covered.
5. **T-12.6** · final `indexer` pass on `docs/INDEX.md` · 2 pts · `sonnet-low`. AC: every
   implemented equation has a registry row; no row points at a missing function.

Mark each ✅ in `docs/BACKLOG.md` when done; run
`.venv\Scripts\python.exe tools\gates.py` before every commit (all five gates, honest
reporting — never compose the commands by hand). CI now also runs them remotely on push.

## After this batch: one tier switch up, then one down

- **T-12.5 · Complete PHYSICS.md · 3 pts · `opus` — the only heavy task left.** Replace
  every `[UNVERIFIED]` marker with a confirmed citation; add derivations for claims
  B-1…B-5 (see `docs/CLAIMS.md`), each with a reducing limit to a Category A result.
  **Switch THIS session's model up in place (Opus; Fable also qualifies)** — do not start
  a new session; the context is the cheap part. Do not attempt this at Sonnet
  (CLAUDE.md: opus-tier work never drops a tier).
- Then back down to Sonnet for **T-12.7** (`docs/GETTING_STARTED.md`, deps T-12.5) and
  **T-12.8** (v1.0: tag, release notes, Zenodo DOI; AC includes CI green and all
  benchmarks passing).

## Traps

1. **`gh` identity:** the active account is `sudo-install-gravity` (repo owner, has
   admin). `Thanatos7777` is also stored but read-only on this repo. `gh auth status`
   confirms.
2. **Windows console shims are broken** — `mypy.exe`/`pytest.exe` exit 1 with no output.
   `tools/gates.py` already avoids them (`sys.executable -m`); if running gates manually,
   use `python -m` forms (HANDOVER §8).
3. **The docx files are one-way build artifacts.** After any edit to
   `docs/paper/nature-draft.md` run `tools/build_paper_docx.py`; after
   `docs/paper/threat-population-survey.md`, `tools/build_survey_docx.py`. Never edit a
   .docx directly; check for a LibreOffice lock file before rebuilding.
4. **Numpy stub generations differ across Python versions in CI** (3.10 resolves an older
   numpy). If CI's mypy fails on 3.10 only with dtype-inference errors, the fix is
   explicit `float64` typing at the call site (matches the FP64-everywhere rule), never
   version-pinning or weakening the gate — see commit `91fe97c` for six worked examples.
5. **Backlog task-header grammar is rigid** (`· 1 pts ·`, never `· 1 pt ·`); run
   `tools/schedule.py --plan` after editing headers — the parser raises loudly by design.

## When blocked

Record the blocker under the task in `docs/BACKLOG.md` with a date, leave it un-✅'d,
continue with the next unblocked task. Never delete a wall (rule 5); never lower a
tolerance to make a test pass (HANDOVER §5).
