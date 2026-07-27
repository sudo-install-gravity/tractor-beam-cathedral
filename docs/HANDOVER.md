# Handover — start here

Current as of **2026-07-27**, commit `eceb03b`. Working tree clean, CI green,
241 tests passing.

This file is the entry point for a session picking the project up cold. Read it,
then `../CLAUDE.md`, then get to work — everything else is referenced from those
two.

---

## 1. What to run first

```bash
cd "/home/thanatos/Documents/Software Dev/Tractor_Beam_Cathedral"
```

```bash
.venv/bin/python tools/schedule.py --next
```

That prints the next batch of tasks. Completion is tracked by ✅ markers in
`BACKLOG.md`, so the scheduler always reflects reality — you do not pass flags to
tell it what is done.

If the batch is too large for one session, take a deterministic prefix instead
of splitting by judgment:

```bash
.venv/bin/python tools/schedule.py --next --chunk 5
```

A prefix of a batch is always dependency-valid, so this cannot orphan anything.
Land those, mark them ✅, and re-run for the next chunk — nothing to carry
between sessions.

Full specs for every task it names are in [`BACKLOG.md`](BACKLOG.md). They are
written to the Definition of Ready: exact path, signature, formula, citation, and
test assertions with tolerances. You should not have to derive anything.

Use the venv for **everything**: `.venv/bin/python`, `.venv/bin/pytest`,
`.venv/bin/ruff`, `.venv/bin/mypy`. The system Python has no numpy.

---

## 2. Where the project stands

| | |
|---|---|
| Complete | **54 of 116 tasks** — Sprint 0 in full, Sprint 1 core, Sprint 2/3 partial, plus 24 of the 25-task Sonnet batch (T-4.1/4.2/4.6, T-5.5-5.8, T-6.1-6.4/6.7/6.9, T-9.1-9.4, T-3.8, T-11.1, T-8.5, T-7.4/7.5, T-2.10) |
| Next up | A **13-task Opus batch** (SPIKE-4.4, T-6.5, T-6.6, and other spin-2/heavy-lift tasks) — switch models for it (§4) |
| Blocked | **T-2.9** (branch protection) needs the repo public, stranding the Sprint 12 release tasks. **T-12.2** (Hulse–Taylor benchmark) is blocked separately: two `researcher` passes could not pin an exact equation number for the Peters (1964) eccentric-orbit decay formula (Caltech PDF connection refused; Blanchet arXiv:1310.1528 PDF unparseable in this environment) — see `BACKLOG.md:772`. Needs a session with normal network/library access, or a from-scratch derivation, before it can be implemented. |

Live modules: `core/{constants,units,validation,backend}`, `bodies/{multipole,sphere}`,
`propagate/{tt_projection,retarded}`, `source/{quadrupole,conservation,multipole_rad}`,
`kinematics/{profiles,oscillators}`, `array/{geometry,grating,beamform}`,
`target/coupling`, `viz/patterns`.

**`array/beamform.py` is deliberately the scalar (spin-1-style) baseline** — it treats
elements as isotropic point radiators combining complex scalar weights, exactly like an
ordinary EM phased array. It is the known-good reference the spin-2 tensor superposition
(`superpose_tt`, T-6.5, next up) must reduce to for co-oriented elements. Do not read
gravitational-radiation physics into it.

**Gate G1** closes at the end of Sprint 2 and needs `SPIKE-4.4` plus the
`opus`-tier Sprint 2 tasks. The dipole-cancellation benchmark — the one that
validates the project's central physics premise — **passes**, which closed OQ-1.

---

## 3. Run every task through the workflow

**RESEARCH → IMPLEMENT → REVIEW → INDEX**, described in `../CLAUDE.md`. The
Sprint 1–3 citations are already verified; later sprints still carry `[verify]`
markers that must be resolved before implementation, not after.

Definition of Done is in `../CLAUDE.md`. The parts people skip: the benchmark
test, and updating [`INDEX.md`](INDEX.md).

---

## 4. Do not spawn subagents for batch work

This was tried four times and failed four times. The last attempt, handed five
fully-specified 2-point tasks, burned **190k tokens in 27 minutes and wrote
nothing** — the whole budget went on re-reading context to learn house style.
An earlier one delivered work but lost its report, leaving two tasks
half-written.

**Switch the session model instead** and run the batch in-context. When you reach
the Opus batch, switch to Opus rather than dispatching to it.

---

## 5. Traps that have already cost time

Each of these bit us once; all are now guarded, but the reasoning is worth
carrying.

**Spin-2, not spin-1 — the highest-risk bug class.** Gravitational radiation is
spin-2: polarization rotates as e^(2iψ), h₊ and h× are 45° apart, and
superposition acts on the TT-projected tensor `h_ij`, never on scalar
amplitudes. Anything adapted from antenna, radar or acoustics code implements
spin-1 and will produce plausible, wrong numbers. T-6.1–T-6.4 are deliberately
the *scalar* baseline — they must say so in their docstrings.

**Published sources contain errors.** [`ERRATA.md`](ERRATA.md) records two
verified typos in Flanagan & Hughes (2005), one of which yields a non-symmetric
tensor — impossible for a quadrupole. Never "fix" correct code to match a printed
mistake.

**Fix the measurement, never the tolerance.** Twice a test failed and the *test*
was wrong, not the code: third-derivative finite differences are
roundoff-dominated (1.1e-1 error at h=1e-5 vs 8.0e-7 at h=1e-3), and adaptive
quadrature loses precision across kinks in piecewise-smooth functions. See the
comment in `tests/unit/test_profiles.py::test_position_matches_integral_of_velocity`.

**Absolute tolerances hide scale dependence.** An acceptance criterion of
"atol 1e-9" was unachievable by 32 orders of magnitude at astronomical scale, and
passed only because the canonical case was equal-mass and cancelled exactly.
Prefer relative criteria, and when something passes, check *why*.

**Ask what every task assumes that no task provides.** This cross-cutting gap was
missed twice — first array conventions (fixed by ADR-0002), then a shared binary
fixture (fixed by T-1.0). Per-task review does not catch it.

**Make absence loud.** Three bugs so far were all "something disappeared with no
signal": a task that failed to parse and vanished from the schedule, tasks
stranded behind a blocker and simply absent from the plan, and completed tasks
misreported as unreachable. If a parser cannot read something, raise. If
something is unreachable, say why.

---

## 6. Reference map

| File | What it holds |
|---|---|
| [`../CLAUDE.md`](../CLAUDE.md) | Operating rules, workflow, Definition of Ready/Done |
| [`BACKLOG.md`](BACKLOG.md) | All 116 task specs, tiers, dependencies, ✅ status |
| [`adr/0002-array-conventions.md`](adr/0002-array-conventions.md) | **Binding**: shapes, dtypes, SI units, float64 |
| [`PHYSICS.md`](PHYSICS.md) | Derivations; §2.1 has the measured finite-difference error curve |
| [`CLAIMS.md`](CLAIMS.md) | Established / derived / conjecture, plus the HFGW firewall |
| [`ERRATA.md`](ERRATA.md) | Verified errors in cited literature |
| [`INDEX.md`](INDEX.md) | Equation registry, module map, assumption ledger |
| [`adr/0001-linearized-gr.md`](adr/0001-linearized-gr.md) | Why linearized GR, not numerical relativity |

---

## 7. Sanity check before you commit

```bash
.venv/bin/ruff check src tests tools && .venv/bin/ruff format --check src tests tools && .venv/bin/mypy src && .venv/bin/python tools/check_citations.py && .venv/bin/pytest -q
```

All five must pass. Then mark finished tasks ✅ in `BACKLOG.md` so the scheduler
stays truthful.
