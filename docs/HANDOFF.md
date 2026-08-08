# HANDOFF — Sprint 14 execution batch (written 2026-08-08, planning session)

**Assume zero conversational context.** Everything needed is in the files named here.

## The batch

Run Sprint 14, tasks **T-14.1 → T-14.9**, specified in full in `docs/BACKLOG.md` (last
sprint before "### Critical path"). All nine are Ready: exact paths, signatures, formulas,
citations, and test assertions with tolerances are supplied. **Zero open decisions — if you
find yourself deciding something, stop and re-read the sprint's D-14.1…D-14.7 decision
block; the answer is there or the task is defective (record it under the task, don't
improvise).**

Order (respects deps): T-14.1, T-14.2, T-14.4 in any order → T-14.3 → T-14.5 → T-14.6 →
T-14.7 → T-14.8 → T-14.9. Mark each task header ✅ in `docs/BACKLOG.md` when done — the
scheduler reads those markers.

## Tier

The batch is `sonnet` tier: T-14.1–T-14.6, T-14.9 are `sonnet-low`; T-14.7, T-14.8 are
`sonnet`. There are **no `opus` tasks** — the planning session absorbed the heavy lift
(all citations verified 2026-08-08; arithmetic in the ACs independently confirmed at plan
review). Switch back to Opus only if `code-reviewer` raises a Critical finding that needs
a derivation to resolve — none is expected.

## Workflow per task (CLAUDE.md is binding)

RESEARCH → IMPLEMENT → REVIEW → INDEX. The sprint's citations are already verified — the
per-task `researcher` pass only needs to confirm the docstring matches the Sprint 14
header's citation block, not re-verify sources. `code-reviewer` and `indexer` run on every
task as usual. Gates before any commit, using `.venv\Scripts\python.exe` for everything:
`ruff check`, `ruff format --check`, `python -m mypy src`, `tools/check_citations.py`,
`pytest -q` — each checked for its own exit code, never behind a pipe (see Sprint 13
T-13.8's two near-misses).

## Traps specific to this batch

1. **`secular_valid` is the contract, `nan` is just the poison.** Every consumer of the
   secular fields in `ledger/tradespace.py` filters on the flag. A bare `min()` over a
   `nan`-bearing sequence is order-dependent and silent — the exact failure the R8
   falsifier exists to catch. T-14.5's AC includes a test that `nan` cells are excluded
   by the flag, not by luck.
2. **Two guards mirror each other; don't "fix" either.** `miss_distance` raises when
   `lead_time > period` (impulsive limit breaks); the new `required_delta_v(...,
   "secular")` raises when `lead_time < period` (secular drift needs multiple orbits).
   Both are walls, not bugs.
3. **The T-14.5 spot cell (ρ = 2400 → 1.57e28 W) is deliberately NOT the minimum-gap
   cell (ρ = 1190 → gap 29.016 decades).** Don't reconcile them; they answer different
   questions.
4. **T-14.3's bracketing test uses `miss = R_EARTH_EQ`, not the focusing-corrected
   `required_miss_distance()`** — it must match Greenstreet et al. 2020's own 1 R⊕
   convention or the comparison is convention-mixing.
5. **Dimorphos mass is derived, not stated.** Docstrings say "derived from Daly et al.
   2023 diameter + density" — the paper contains no mass sentence to cite.
6. **The Izzo PDF's metadata title is stale** ("debris cloud" — template reuse). Content
   is correct: AAS 05-141, eqs. (1)–(3), confirmed by eye 2026-08-08. Don't re-open that
   verification.
7. **T-14.9 (docx rebuild) overwrites `docs/paper/nature-draft.docx`.** The build is
   one-way md → docx (`tools/build_paper_docx.py`). A LibreOffice lock file
   (`.~lock.nature-draft.docx#`) was present 2026-08-08 — confirm the document is closed
   (or the lock stale) first; direct docx edits are lost on rebuild.
8. **Backlog task-header grammar is rigid:** `· 1 pts ·` not `· 1 pt ·`. The parser
   raises loudly on deviation (by design). Run
   `.venv\Scripts\python.exe tools\schedule.py --plan` after editing task headers.
9. Windows generally: cp1252 and CRLF traps are documented in `docs/HANDOVER.md` §1/§6.

## Also runnable in the same Sonnet session (different workstream)

T-13.5, T-13.7, T-13.8 (Sprint 13, no deps). T-13.2/T-13.3/T-13.4 and T-2.9 stay blocked
behind SPIKE-13.1, which is **owner-only** (needs repo-admin access in a browser) and
cannot be done by any agent.

## When blocked

Record the blocker under the task in `docs/BACKLOG.md` with a date, leave the task
un-✅'d, and continue with the next unblocked task. Do not delete a wall (CLAUDE.md
rule 5), do not strip an `UNPHYSICAL` stamp (rule 2), do not lower a tolerance to make
a test pass (HANDOVER §5).
