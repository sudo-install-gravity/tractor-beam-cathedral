# Handoff — T-4.7, T-4.8, T-4.9 (Sprint 4 tail), for a **Sonnet** session

Generated 2026-08-02, replacing the SPIKE-4.5 handoff that this batch's
predecessor consumed. Repo state: commit `d9ebcef`, tree clean, pushed to
`origin/main`. **850 tests passing**, 3 skipped, all five checks green.

## Run this at Sonnet — switch the session model, do not start a new session

All three tasks are `sonnet`/`sonnet-low`: fully specified, zero open design
decisions. **Switch the current session's model to Sonnet in place.** A cold
start re-reads `CLAUDE.md`, the ADRs, the 700-line backlog and several modules
just to learn house style — measured at 190k tokens for five 2-point tasks
(`CLAUDE.md` §"How to run a batch at the right tier"). Keep the context.

Confirm the batch is still current before starting:

```bash
.venv\Scripts\python.exe tools\schedule.py --next
```

## The batch, in dependency order

| Task | Pts | Tier | File |
|---|---|---|---|
| **T-4.7** | 2 | `sonnet-low` | `src/gwtb/bodies/multipole.py` |
| **T-4.8** | 3 | `sonnet` | `tests/benchmarks/test_body_sensitivity.py` |
| **T-4.9** | 3 | `sonnet-low` | `src/gwtb/ledger/gap_report.py` — **after T-4.8** |

Full specs with exact signatures and acceptance criteria are in `BACKLOG.md`;
they are Definition-of-Ready and are not repeated here. What follows is only
what the backlog does **not** tell you.

## Traps — read before writing code

**1. T-4.8 must not apply `finite_size_correction` to the elastic or oblateness
paths.** This is the important one. `finite_size_correction` (T-4.5, landed
2026-08-02) assumes a **volume-filling** `l=2` radial profile and returns
`1 − 5(kR)²/98`. A body that gets its quadrupole by deforming its *surface* —
which is exactly `elastic.py:induced_quadrupole` and
`sphere.py:oblateness_quadrupole`, both incompressible deformations — has
`1 − (kR)²/14` instead, **40% larger**. Multiplying the elastic quadrupole by
the volume-filling factor is wrong and will look entirely plausible. See
[ADR-0007](adr/0007-uniform-sphere-quadrupole-form-factor.md) §"The radial
profile is load-bearing" and the assumption-ledger rows in `INDEX.md`.

**2. T-4.7's threshold is `R/λ > 0.1`, and the departure there is 2.0142%, not
1%.** The backlog's original ">1%" was written against a wrong form factor and
has been corrected. Do not reintroduce it. The 1% point is `R/λ = 0.070460897`.

**3. `finite_size_correction` goes negative past `R/λ = 0.7046`.** That is a
wall, not a bug (rule 5) — T-4.7's warning exists precisely because the
function has no business being called out there. Do not clamp it, and do not
"fix" the sign.

**4. T-4.8 asserts the rigid model is *invariant* under (R, ρ) at fixed M.**
That invariance is the surprising result of T-4.2 and claim B-2, not an
oversight. The elastic model is what must vary. If your sweep makes the rigid
variation nonzero, suspect the sweep.

## The gate that closes each task

```bash
.venv\Scripts\ruff.exe check src tests tools
.venv\Scripts\ruff.exe format --check src tests tools
.venv\Scripts\mypy.exe src
.venv\Scripts\python.exe tools\check_citations.py
.venv\Scripts\pytest.exe -q
```

All five green. Then mark the task ✅ in `BACKLOG.md` (the ✅ markers are what
`schedule.py` reads — this is how completion is tracked), and invoke
`code-reviewer`. `indexer`/`INDEX.md` needs updating only if you add an
equation or citation; T-4.9 adds a ledger row, so update the ledger section.

## If you get blocked

Anything requiring a design decision means the task was not actually Ready —
**stop and escalate to a spike at `opus`**, producing an ADR, not production
code. Do not decide it inline. Physics formulas are never implemented from
memory: invoke `researcher` first, and if it returns `UNVERIFIED` the task is
blocked, not a judgement call. That is exactly how T-4.5 became SPIKE-4.5.

## Delete this file when the batch lands

One-shot handoff. A stale one in the repo is worse than none.
