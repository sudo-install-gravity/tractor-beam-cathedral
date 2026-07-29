# Handover — start here

Current as of **2026-07-29**, commit `3517b25`. Working tree clean, **384 tests
passing**, all five sanity checks green on the Windows host.

This file is the entry point for a session picking the project up cold. Read it,
then `../CLAUDE.md`, then get to work — everything else is referenced from those
two.

> **The host changed.** Development moved from Pop!_OS to **Windows 11** on
> 2026-07-28/29. Paths below are the Windows ones; the Linux equivalents are
> `.venv/bin/...` throughout and still work.

---

## 1. What to run first

```
cd "C:\Users\Thanatos\Documents\Software Dev\Tractor_Beam_Cathedral"
```

```
.venv\Scripts\python.exe tools\schedule.py --next
```

That prints the next batch of tasks. Completion is tracked by ✅ markers in
`BACKLOG.md`, so the scheduler always reflects reality — you do not pass flags to
tell it what is done.

If the batch is too large for one session, take a deterministic prefix instead
of splitting by judgment:

```
.venv\Scripts\python.exe tools\schedule.py --next --chunk 5
```

A prefix of a batch is always dependency-valid, so this cannot orphan anything.
Land those, mark them ✅, and re-run for the next chunk — nothing to carry
between sessions.

Full specs for every task it names are in [`BACKLOG.md`](BACKLOG.md). They are
written to the Definition of Ready: exact path, signature, formula, citation, and
test assertions with tolerances. You should not have to derive anything.

Use the venv for **everything**: `.venv\Scripts\python.exe`,
`.venv\Scripts\pytest.exe`, `.venv\Scripts\ruff.exe`, `.venv\Scripts\mypy.exe`.
The system Python has no numpy.

---

## 2. Where the project stands

| | |
|---|---|
| Complete | **58 of 116 tasks**; 300 points total |
| Tests | **384 passing**, 2 warnings, ~104 s |
| Next up | A **21-task, 55-point SONNET batch** spanning sprints 5–12. Run it at Sonnet — it contains no `opus` work (§4) |
| Blocked | **T-2.9** (branch protection) needs the repo public. **T-12.2** (Hulse–Taylor) needs an exact Peters (1964) equation number. Both are now machine-readable blocks, so the scheduler excludes them *and says so*. **T-12.8** is transitively stranded behind both. |

Live modules: `core/{constants,units,validation,backend}`, `bodies/{multipole,sphere}`,
`propagate/{tt_projection,retarded,polarization}`, `source/{quadrupole,conservation,multipole_rad}`,
`kinematics/{profiles,oscillators}`, `array/{geometry,grating,beamform}`,
`target/coupling`, `viz/patterns`.

**`array/beamform.py` is deliberately the scalar (spin-1-style) baseline** — it treats
elements as isotropic point radiators combining complex scalar weights, exactly like an
ordinary EM phased array. It is the known-good reference the spin-2 tensor superposition
(`superpose_tt`, T-6.5 — **now complete**) reduces to for co-oriented elements. Do not read
gravitational-radiation physics into it.

**Gate G1** closed with SPIKE-4.4 (ADR-0003) and the Sprint 2 opus tasks. The
dipole-cancellation benchmark — the one that validates the project's central
physics premise — **passes**, which closed OQ-1.

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

**Switch the session model instead** and run the batch in-context.

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

**Make absence loud.** Four bugs so far were all "something disappeared with no
signal": a task that failed to parse and vanished from the schedule, tasks
stranded behind a blocker and simply absent from the plan, completed tasks
misreported as unreachable, and — found 2026-07-29 — **T-12.2 declared blocked in
prose but scheduled anyway.** `schedule.py` derives blocks from the `deps` field
and cannot read a 🚫 marker or a `*Blocked:*` paragraph, so a task the backlog
called blocked went into a Sonnet batch. If a task is blocked, say so **in its
deps** — `deps T-1.8, exact Peters 1964 equation number` — exactly as T-2.9 does
with `deps repo made public`. Prose is for humans; the deps field is the contract.

---

## 6. Host notes — Windows 11, since 2026-07-29

**`schedule.py` used to die on Windows before printing anything.**
`UnicodeEncodeError`: its box-drawing and ✅ output cannot be encoded by the
console's cp1252 default. Fixed at the top of the script by reconfiguring
stdout/stderr to UTF-8. Nothing about the schedule was ever wrong — the tool
simply could not say it. If another tool shows that error, same cause, same fix.

**Line endings are pinned by `.gitattributes`** (added 2026-07-29). The first
Windows clone checked out 83 of 87 tracked files as CRLF, because this repo had
no line-ending policy. Content was unaffected and `git status` stayed clean,
which is precisely why it was worth pinning before it bit. If a whole-tree diff
ever appears, run `git diff --summary` first to separate mode/EOL changes from
real edits.

**T-12.2's blocker is half-resolved, and the halves differ** — see
[`BACKLOG.md`](BACKLOG.md). Retested 2026-07-29: the Caltech Peters PDF still
refuses the connection (same IP, not a host artefact — stop retrying it), but
arXiv:1310.1528 returns **HTTP 200**. That failure was *parsing*, not access, so
the Blanchet route is the one worth re-attempting here.

---

## 7. Reference map

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

## 8. Sanity check before you commit

```
.venv\Scripts\ruff.exe check src tests tools
.venv\Scripts\ruff.exe format --check src tests tools
.venv\Scripts\mypy.exe src
.venv\Scripts\python.exe tools\check_citations.py
.venv\Scripts\pytest.exe -q
```

All five must pass. All five are green as of 2026-07-29. Then mark finished tasks
✅ in `BACKLOG.md` so the scheduler stays truthful.
