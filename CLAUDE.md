# Tractor Beam Cathedral — Agent Operating Instructions

Theoretical M&S tool for gravitational-wave asteroid deflection. This is a **cathedral
project**: intended to outlive its founders. **Optimize for auditability over speed.** A
cathedral built on a sign error is a ruin.

## Read first

| File | What it tells you |
|---|---|
| `docs/HANDOVER.md` | **Start here if you are picking this up cold** — state, next steps, traps |
| `docs/INDEX.md` | Codebase map, equation registry, assumption ledger (maintained by `indexer`) |
| `docs/CLAIMS.md` | What is established physics vs. our extension vs. conjecture |
| `docs/PHYSICS.md` | First-principles derivation of the framework |
| `docs/BACKLOG.md` | Current sprint and task specifications |
| `docs/adr/` | Architecture decision records — why things are the way they are |

## Mandatory agent workflow

Every task follows **RESEARCH → IMPLEMENT → REVIEW → INDEX**.

1. **RESEARCH** — before writing any physics code, invoke the `researcher` agent to confirm
   the governing equation, its primary source, and its **exact equation number**. Never
   implement a physics formula from memory. Record the citation in the docstring.
   *If `researcher` returns `UNVERIFIED`, the task is blocked. Escalate it to a spike; do not
   proceed to IMPLEMENT.*
2. **IMPLEMENT** — write code and tests together. A physics function is not complete without
   a benchmark test.
3. **REVIEW** — invoke `code-reviewer` before considering any task done. Physics changes get
   the additional dimensional-analysis, index-convention, and spin-2 checks.
4. **INDEX** — invoke `indexer` after any new module, equation, or citation, to update
   `docs/INDEX.md`.

Planning sessions run RESEARCH → plan → REVIEW (of the plan) → INDEX.

At sprint planning, batch all of the sprint's citation verifications into a single
`researcher` pass. Web lookups dominate its latency, and a sprint's equations usually come
from adjacent sections of the same text.

## Non-negotiable rules

**1. Citation discipline.** Every public function in `source/`, `propagate/`, `bodies/`, or
`array/` carries a docstring line of the form `Source: <reference>, eq. <number>`. CI fails
without it. "Blanchet ch. 3" is not a citation; "Blanchet eq. 3" is.

Prefer sources whose equation numbers a stranger can check — open-access first:
**[B]** Blanchet, *Living Rev. Relativ.* 17:2 (2014), arXiv:1310.1528;
**[FH]** Flanagan & Hughes, *New J. Phys.* 7:204 (2005), arXiv:gr-qc/0501041.
Cite a textbook only when you can confirm the exact equation number. A contributor in 2075
will not necessarily own the books.

Published sources contain errors: see `docs/ERRATA.md` for two we verified numerically.
Never "fix" correct code to match a printed typo.

**2. Conservation auditing.** Any result computed from a non-momentum-conserving source is
stamped `UNPHYSICAL: violates d_mu T^mu-nu = 0`. **Never strip that stamp.** Mass-dipole
radiation exists only if the system's momentum is not conserved; if a hidden external agent
pushes the spheres, the resulting dipole term is roughly 10^10 times the true quadrupole
signal. Unstamped, that artifact looks like a breakthrough.

**3. FP64 everywhere** unless a task explicitly authorizes the split-phase FP32 scheme.
Absolute phase over 40 AU is ~10^10 wavelengths, beyond FP32's ~10^-7 relative precision.
Strain values ~1e-40 are *subnormal* in FP32. Use `gwtb.core.units` scaled representation.

**4. Spin-2, not spin-1.** GW polarization rotates as e^(2*i*psi), not e^(i*psi); h_plus and
h_cross are **45 degrees** apart, not 90. Superpose the tensor `h_ij` after TT projection
along the observation direction — never scalar amplitudes. **Any code borrowed from antenna,
radar, or acoustics references is spin-1 and will be silently wrong.** This is the project's
highest-risk bug class.

**5. Never delete a wall.** Diffraction, coupling, and magnitude limits are *findings*, not
bugs. They belong in the feasibility ledger. If a change makes one disappear, the change is
defective — not the wall.

**6. Epistemic firewall.** This work sits adjacent to the discredited HFGW literature (see
`docs/CLAIMS.md`). Cite Grishchuk & Sazhin 1974, never Baker. If a source traces to
gravwave.com, drrobertbaker.com, or HFGW patent literature, flag it and stop.

## Which model runs a task

Every task in `docs/BACKLOG.md` carries a tier: `sonnet-low` (fully specified,
zero open decisions), `sonnet` (moderate judgment), or `opus` (**heavy lift** —
spikes, physics derivations, cross-cutting interfaces, anything with no reference
implementation to check against).

**Do not walk the backlog in task order.** Model switches cost a session boundary,
paid per switch rather than per task. Ask the scheduler what to run next:

```bash
python tools/schedule.py --next
```

It batches every reachable heavy task into one Opus session, then hands the bulk
back to Sonnet. `--plan` shows the whole run order. It also reports externally
blocked tasks and anything transitively stranded behind them.

Completion is read from ✅ markers on the task headers in `docs/BACKLOG.md`, so
the plan always matches reality — **mark a task ✅ when you finish it.** (`--done`
exists only for what-if queries, not for tracking.)

The three support agents (`researcher`, `code-reviewer`, `indexer`) are **not** a
tier — they run on every task regardless of which model implements it. They are
short, single-purpose passes and remain worth invoking; the caution below is
about handing a *batch of implementation work* to a fresh agent, which is a
different thing.

### How to run a batch at the right tier

**Switch the session's model to match the batch. Do not spawn subagents for
this.**

| Batch tier | Run it in |
|---|---|
| `sonnet-low` | a Sonnet session (low reasoning effort) |
| `sonnet` | a Sonnet session |
| `opus` | an Opus session |

⚠️ **Subagent dispatch was tried and abandoned — measured 2026-07-26.** Four
consecutive dispatches failed. The last one, given five fully-specified 2-point
tasks, spent **190,175 tokens across 37 tool calls in 27 minutes and wrote zero
files** — the entire session budget went on re-reading `CLAUDE.md`, ADR-0002,
the 700-line backlog, and several source modules just to learn house style. An
earlier dispatch delivered work but lost its report to a harness error, leaving
two of twelve tasks half-written and needing reverse-engineering from the file
system.

The Definition of Ready makes a cold handoff *possible*. It does not make it
*cheap*: the task spec is small, but this project's surrounding context is not,
and that cost recurs in full on every dispatch.

So: **switch models, keep the context.** No cold start, no boundary at which
work or reports can vanish, and correct billing.

**What still must not drop a tier:** the `code-reviewer` pass, resolving
Critical findings, and any `opus`-tier task — notably `SPIKE-4.4`, T-6.5 and
T-6.6, where the spin-2 risk lives. Switch back to Opus for those rather than
attempting them at Sonnet.

## Definition of Ready

A task may only be started if it has: an exact file path, an exact function signature, the
formula and citation pre-supplied, exact test assertions with tolerances, and **zero open
design decisions**. If a task says "decide", "choose", or "figure out", it is not Ready — it
needs a spike first, and spikes produce an ADR in `docs/adr/`, not production code.

## Definition of Done

- [ ] Citation present in docstring and verified by `researcher`
- [ ] Unit tests pass; benchmark test added if the change is physics
- [ ] Dimensional-consistency test passes
- [ ] `code-reviewer` invoked; all Critical findings resolved
- [ ] `indexer` invoked; `docs/INDEX.md` current
- [ ] Feasibility ledger updated if the change affects a gap metric

## Project layout

```
src/gwtb/
  core/       constants, unit scaling, backend shim
  bodies/     mass distributions and multipole moments
  kinematics/ acceleration profiles, oscillator drive synthesis
  source/     radiation: quadrupole, multipoles, memory, conservation audit
  propagate/  retarded fields, TT projection, spin-2 polarization
  array/      geometry, beamforming, grating lobes, focusing
  target/     geodesic deviation, coupling channels, deflection
  ledger/     feasibility gap report
  viz/        field slices, beam patterns, volumetric rendering
```

## Environment note

This machine's system Python has **no pip and no ensurepip**. Installing dependencies requires
`sudo apt install python3-pip python3-venv` first. Until then, tests that need numpy cannot
run locally — CI is the source of truth.
