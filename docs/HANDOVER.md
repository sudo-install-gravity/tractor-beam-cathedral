# Handover — start here

> **2026-08-08, SPIKE-13.1 in progress.** All four of the spike's listed
> hypotheses (Actions disabled at repo or account level; free-tier minute
> exhaustion) are eliminated or don't apply — "Allow all actions" is already
> selected at the repo level, and personal GitHub accounts have no
> account-wide Actions toggle to check (unlike organizations). None explains
> `actions/runs` reporting `total_count: 0` across 64 prior pushes. This
> commit is a live diagnostic push: if a run appears in
> `https://github.com/sudo-install-gravity/tractor-beam-cathedral/actions`
> after this lands, the trigger mechanism works and any failure narrows the
> problem sharply; if the run count is still zero, none of the diagnosed
> hypotheses hold and the spike escalates per its own AC rather than guessing.

Current as of **2026-08-02**. **835 tests passing** (3 skipped — CuPy and
PyVista are optional dependencies, absent on this host), all five sanity
checks green. Committed and pushed.

> **2026-08-02, later the same day: T-12.2 landed. `schedule.py --next` now
> reports "nothing to schedule" for real** — 106 of 117 tasks complete, and
> unlike the batch-completion milestone below, this is not "one blocker away
> from more work," it is genuinely **everything reachable is done.**
> Everything left is T-2.9, T-4.5, and the tasks transitively stranded behind
> them.
>
> **T-12.2's block was resolved, but not the way it looked like it would be.**
> The prior session's plan was "re-attempt Blanchet arXiv:1310.1528, it's
> reachable now." That paper turned out **not to contain the eccentric-orbit
> decay formula at all** — it covers only quasi-circular inspiral, so that
> avenue was never going to work regardless of PDF-parsing tooling. The
> citation that actually resolved it: **Kowalska, Bulik, Belczyński, Dominik &
> Gondek-Rósińska, A&A 527:A70 (2011), arXiv:1010.0511**, eq. (1) for `<da/dt>`
> and eq. (3) for `<de/dt>` — open-access, peer-reviewed, confirmed
> algebraically against the already-verified 73/24, 37/96, 121/304-coefficient
> form (`-(19/12)*(64/5) = -304/15` exactly). **This is not the original Peters
> (1964) paper** — that one stays paywalled with no checkable equation number,
> and the codebase must cite Kowalska et al., not "Peters 1964 eq. 5.6/5.7."
> `tests/benchmarks/test_hulse_taylor.py` reproduces the real PSR B1913+16
> decay rate to 0.21% (predicted −2.4031e-12 vs. observed −2.398e-12) — the
> actual celebrated agreement, not a loosely-passing tolerance check.
>
> **Landing T-12.2 exposed a fifth instance of the "test coupled to live
> backlog state" failure class** (see §5 below, "Tests that hard-code batch
> sizes expire"): five `test_schedule.py` tests read `plan(tasks)[0]` against
> the *real* backlog to test `take_chunk` — a pure function that never needed
> live data at all. Once the real backlog reached empty, `plan(tasks)` returned
> `[]` and `[0]` raised `IndexError` in all five. Fixed permanently this time,
> not resized again: a synthetic 8-task batch (`_synthetic_batch()`, reusing
> the `_mk()` helper already used for the lookahead tests) replaces the live
> backlog dependency in all five, plus a new test asserting an empty plan is a
> legitimate, non-crashing outcome.
>
> **Prior milestone note, retained for its own content below.**

This file is the entry point for a session picking the project up cold. Read it,
then `../CLAUDE.md`, then get to work — everything else is referenced from those
two.

> **The host changed.** Development moved from Pop!_OS to **Windows 11** on
> 2026-07-28/29. Paths below are the Windows ones; the Linux equivalents are
> `.venv/bin/...` throughout and still work.

---

## 0a. Repository is public — 2026-08-06 — and CI has never run

**T-2.9's blocker cleared.** The repository is public: verified without credentials
(`private: false`, `visibility: public`, unauthenticated `git ls-remote` returns HEAD).

Two things follow, and the second is the important one.

**The scheduler could not see the unblocking until the `deps` field was changed.** T-2.9 read
`deps repo made public` — prose, which `schedule.py` cannot evaluate, so it excluded the task
even after the condition was met. Changed to `deps none`; the scheduler now offers **4 tasks,
8 points** (T-2.9, T-12.1, T-12.4, T-12.6, unlocking 2 more). This is §5's "make absence
loud" rule biting again: **a condition expressed in prose is invisible to the tool.**

⚠️ **CI HAS NEVER RUN — `total_count: 0` for the entire history of this repository.**
`.github/workflows/ci.yml` is present on the remote, correct, and was committed 63 commits
ago; job id `test`, `on: push: branches:[main]`, matrix `["3.10","3.11","3.12"]`, which
would produce exactly the check names T-2.9's acceptance criterion requires. So the workflow
is not the defect. The cause could not be determined from here — reading
`actions/permissions` returns 403 for the available token. **Check Settings → Actions.**

**Clearing the blocker broke three tests — the SIXTH instance of §5's "tests coupled to
live backlog state".** They asserted the project's *current* state rather than the
scheduler's behaviour: that T-2.9's `external_block` reads "repo made public", that T-2.9 is
excluded from the plan, and that heavy tasks get batched. All three were correct until the
blocker cleared, and all three then failed while nothing was wrong. The batching one had
already expired twice before on the same principle. **Fixed permanently, not resized:**
parser notation is now tested through `_parse_deps` directly, exclusion and batching through
synthetic graphs, and the one property that genuinely needs the live backlog — that the
planner drops nothing reachable — is written as a *set comparison* rather than a count, so
it holds no matter how much work remains, including none.

**Sprint 13 now exists for this** — 9 points, 7 tasks, `docs/BACKLOG.md`. It opens with the
table of hypotheses already **eliminated** (workflow present, registered, `state: active`,
correct trigger, not a fork, not archived, job names correct), so the spike starts from the
one hypothesis that survived rather than re-deriving the rest.

⚠️ **SPIKE-13.1 is owner-only and cannot be delegated to an agent.** Every remaining
hypothesis needs repository-**admin** access, and `actions/permissions` returns 403 because
the `gh` CLI is signed in as `Thanatos7777`, which holds `push: false` on this repository.
Check **Settings → Actions → General** first.

**Do not "fix" git while fixing this — git is already right.** The two authenticate through
different paths, and only one is wrong:

| | Identity | State |
|---|---|---|
| `git push` (Git Credential Manager) | `sudo-install-gravity` | ✅ correct — GitHub reports `committer_login: sudo-install-gravity`, and commits attribute to that account |
| `gh` CLI (API calls) | `Thanatos7777` | ❌ wrong — read-only here, hence every 403 |
| commit metadata (`user.name`/`user.email`) | `sudo-install-gravity` / `dpaulday@protonmail.com` | ✅ correct, set in `.git/config` |

Signing `gh` in as the owner is worth doing — it may close SPIKE-13.1 outright by making
`actions/permissions` readable — but **clearing the stored git credential would break working
pushes to fix a problem that is not in git.**

Order matters for T-2.9: **make CI run, confirm a green run, then set branch protection.**
You cannot require a status check that has never reported, so doing it the other way round
either fails or silently protects nothing.

**This reaches the manuscript.** Methods claimed citation discipline is "enforced in
continuous integration". The check *script* is real — gate 4 of the five, run on every commit
this session — but it has only ever run **locally**. The paper now says so explicitly rather
than carrying the stronger claim; correct the wording or make CI run before submission.

---

## 0. Where the last session stopped — 2026-08-02

> **Update, later the same day (Sonnet session) — T-4.7, T-4.8, T-4.9 have
> landed, and a reproducibility gap in ADR-0006 was found and closed. Sprint 4
> is now fully complete. 867 tests passing**, 3 skipped, all five §8 checks
> green, committed and pushed.
>
> **`scratchpad/spike_9_6.py` now exists and is committed.** ADR-0006 had cited
> `spike_9_6.py`/`spike_9_6b.py` as its prototypes, but `scratchpad/` was
> untracked until SPIKE-4.5, so neither file was ever committed — every figure
> in ADR-0006 was unreproducible from this repo. A fresh `spike_9_6.py`
> regenerates all of them from current production code (12374.4 m aperture,
> 1.034e-9 rad spread, 2.4e7× margin, the `D/λ` table, the sign-convention
> table, the 8.75 peak-to-background ratio) and all reproduce. Recorded in
> `docs/INDEX.md`'s assumption ledger per rule 8, not silently patched.
>
> **T-4.7**: `LongWavelengthAssumptionWarning`, raised by
> `finite_size_correction` at `R/λ ≥ 0.1` (inclusive), naming the "Long
> wavelength" row of `docs/INDEX.md` §3 in its message text.
>
> **T-4.8**: `tests/benchmarks/test_body_sensitivity.py` sweeps 5 radii across
> two orders of magnitude at fixed `M`. Rigid-model radiation stays at the
> machine-zero floor; elastic-model radiation (steel/tungsten/osmium) varies by
> ~7.6e4–1.0e5×, eight orders above the AC's threshold.
>
> **T-4.9**: `body_quadrupole_gap` in `ledger/gap_report.py`, a thin wrapper
> (`focusing_gap`'s style) — fixed `name`/`units`, caller supplies both values,
> since neither "which body model" nor "required for what scenario" was
> specified by the backlog entry and none should be invented here.
>
> **Every task in the backlog is now complete except externally-blocked ones.**
> `schedule.py --next` reports "nothing to schedule — all tasks complete or
> externally blocked." Remaining: `T-2.9` (needs the repo public) and the six
> Sprint 12 closeout tasks that depend on "all" and are therefore blocked
> transitively behind it. **No session-startable work remains** until T-2.9's
> external dependency clears.

### The 2026-07-31 entry

> **Update, later the same day.** SPIKE-9.6, **T-9.6 and T-10.1 have since
> landed**, and with them **every `opus` task in the backlog is complete** except
> the blocked T-4.5. **588 tests passing**, all five checks green, committed and
> pushed.
>
> **The next batch is Sonnet: 36 tasks, 92 points, sprints 2–12.** Recommendation
> is to **switch this session's model to Sonnet** rather than start a new session
> — the context is already loaded and a cold start is the expensive path (§4).
> Run `schedule.py --next --chunk N` if it is too large for one sitting; a prefix
> of a topologically-ordered batch is always dependency-valid.
>
> Nothing in that batch needs Opus. Switch **back** to Opus only for SPIKE-4.5
> (see §9), which is the sole remaining heavy item and is externally blocked
> until a citable form-factor equation is found.

### The original 2026-07-31 entry

Work is **committed and pushed**; the tree is clean and all five checks in §8
are green at **553 tests**. The session ended on a weekly usage limit, not on a
problem. Eight tasks landed: T-2.2, T-2.6, T-3.7, T-4.3, T-9.5, T-11.3 at Opus,
and T-6.8, T-11.2 at Sonnet in a concurrent session.

**Pick up at T-9.6, and read §9 first.** SPIKE-9.6 has since closed the design
decision that blocked it (ADR-0006), so T-9.6 is now Definition-of-Ready — but
its backlog entry carries **four measured traps, each of which yields a test that
passes while asserting nothing.** Read them before writing tests, not after. That
is the single most important thing on this page.

Nothing is half-finished. No task was left partially implemented, no test is
skipped or xfailed, and every module added is fully covered.

---

## 1. What to run first

```
cd <path to your local clone of tractor-beam-cathedral>
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
`.venv\Scripts\python.exe -m pytest`, `.venv\Scripts\ruff.exe`,
`.venv\Scripts\python.exe -m mypy`. The system Python has no numpy.

⚠️ **Invoke mypy and pytest as `python -m`, not through their `.exe` shims** — both shims
are broken on this host and fail *silently* (exit 1, no output). See §8.

---

## 2. Where the project stands

| | |
|---|---|
| Complete | **111 of 118 tasks** (`schedule.py --status` is authoritative; do not trust a number typed into this file) |
| Tests | **867 passing**, 3 skipped (CuPy/PyVista absent), ~76 s |
| Next up | **Nothing schedulable.** `schedule.py --next` reports "nothing to schedule — all tasks complete or externally blocked" directly. |
| Blocked | **T-2.9** needs the repo made public. Six Sprint 12 closeout tasks (T-12.1, T-12.4–T-12.8) depend on "all" and are therefore transitively blocked behind it — see `schedule.py --plan`. Everything else that was ever blocked is now resolved: T-12.2 (Kowalska et al. citation) and T-4.5 (SPIKE-4.5 → ADR-0007) on 2026-08-02, plus T-4.7/4.8/4.9 which T-4.5 freed, landed the same day — see §0. |

**Landed 2026-07-31.** T-2.2 (`UNPHYSICAL` stamp propagation, ADR-0005), T-2.6
(frozen ledger schema), T-3.7 (linear memory), T-4.3 (Love-number deformation),
T-9.5 (focal phase solution), T-11.3 (split-phase) at Opus; T-6.8 (propagation)
and T-11.2 (Numba field kernel) at Sonnet, in parallel.

`code-reviewer` raised one **Critical** finding against this batch and it is
**resolved**: the frozen ledger schema had no field able to carry an
`UNPHYSICAL` stamp, so a caller feeding it a `StampedResult` was forced to
unwrap to `.value` and discard the provenance — turning a ~10^10× mass-dipole
artifact into a row that clears its requirement by ten orders of magnitude.
Closed by a sixth field, `provenance`, plus `GapMetric.from_stamped()`, while
the freeze still had no dependents. **When writing ledger rows (T-2.7, T-4.9,
T-5.9, T-8.9, T-10.8), use `from_stamped()` for anything that came from a
`StampedResult`** — the plain constructor will accept an unwrapped float
without complaint.

**Gate G1 remains closed.** The dipole-cancellation benchmark still passes, and
T-3.7 added a second independent cross-check: linear memory reproduces the
settled quadrupole waveform bit-for-bit on-axis, exactly as ADR-0004 predicted
before the code existed.

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

**Large-number cancellation destroys signals silently — and float64 is not a
fix.** Found 2026-07-31, twice, in different modules. Differencing two ~1e12 m
ranges at 40 AU returns **exactly zero** in float64: every element's range
rounds to the same value, so 100% of the focusing information is lost with no
error, no warning, and a perfectly plausible-looking array of zeros. The same
happens to propagation phase — at 1.25e8 rad, float64's spacing is ~340× larger
than the entire per-element differential. Both are fixed by never forming the
large quantity: use the identity in `array/focus.py:_differential_range`, and
`SplitPhase.phasor()` rather than `.recombine()`. If you are subtracting two
astronomical-scale numbers to get a small one, assume it is broken until a
`decimal`-arithmetic reference says otherwise. Both modules test against
60-digit `decimal` references for exactly this reason.

**An acceptance criterion can be satisfied by returning zeros.** T-9.5's "residual
phase error < 1e-9 rad" is trivially met at 40 AU, where the true differential
phase is ~1e-11 rad. T-11.3's "matches full FP64" is met because *both* sides are
degenerate. In each case the test was moved to a regime where the criterion can
actually fail. When a criterion passes on the first run, check what would have to
break for it to fail.

**`np.allclose` has a default `atol=1e-8`.** It called a factor-of-two difference
between ~1e-9 quantities "close", nearly hiding T-4.3's headline result. Pass
`atol=0` whenever comparing small numbers. This is the same scale-dependence trap
recorded above, in a different disguise.

**Tests that hard-code batch sizes expire.** Two `test_schedule.py` tests asserted
literal chunk lengths and began failing as tasks completed and the leading batch
shrank — with nothing actually wrong. Both now size against the batch. A test
whose fixture is the real backlog must not assume how much work is left.

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

## 9. Open work needing `opus` judgment — **none left as of 2026-08-02**

> Both items in this section are now closed (T-9.6 by ADR-0006, T-4.5 by
> ADR-0007). **There is no `opus`-tier work outstanding in the backlog.** The
> section is kept because the traps each spike found are still live for anyone
> editing that code — read them before touching `array/focus.py` or
> `bodies/multipole.py`, not after.

### ✅ T-9.6 is now Ready — SPIKE-9.6 closed the tension (ADR-0006)

**Resolved 2026-07-31.** `focused_field` builds on `superpose_tt` unchanged, with
weights `exp(+i · focal_phases(...))`. The angular spread of per-element
observation directions at 40 AU is **1.03e-9 rad** against ADR-0003's 5.0e-2 rad
alignment budget — a **2.4e7× margin** — so ADR-0003's common-`n̂` reversal
condition is not triggered. Near-field focusing stays out of scope and
`superpose_tt`'s Fraunhofer guard enforces it; propagate that error, don't catch
it.

**Before writing T-9.6's tests, read the four traps** in its backlog entry and
[ADR-0006](adr/0006-focused-field-far-field-regime.md). Each produces a test that
passes while asserting nothing. The worst: at the nominal 1 kHz drive the
reference aperture is **sub-wavelength** (`D/λ = 0.041`), so every weighting —
including uniform `w = 1` — returns exactly `N`, and the AC passes with the
focusing logic deleted. Test at `f ≥ 1e5 Hz` and assert `D/λ > 1`.

The original tension is recorded below for context.

---

### T-9.6 `focused_field` — the tension as it stood

T-9.6 is tiered `opus` and marked critical path. It was **not** Definition-of-Ready
as written, and the reason was found while building T-9.5:

`superpose_tt` (T-6.5) sums TT tensors along **one common observation direction**
and *raises* inside the Fraunhofer distance, because tensors projected along
different directions live in different polarization spaces and cannot be added
(ADR-0003's reversal condition). That is a far-field construction. Focusing is
ordinarily a near-field operation. So `focused_field` cannot simply call
`superpose_tt` at a focal point — and the near-field alternative, projecting each
element along its own direction to the focus, is exactly what ADR-0003 forbids.

**The measured numbers say the tension resolves in favour of the far field, but
that must be decided deliberately, not by default.** At 40 AU with a 12.4 km
aperture, `R/R_Fraunhofer ≈ 5.9e9` at 1 kHz and the entire focusing phase
correction is ~6.7e-11 rad: focusing is numerically indistinguishable from
steering (`tests/unit/test_focus.py::test_focusing_is_degenerate_with_steering_at_40_au`).
If the engagement geometry is always this deep in the far field, `focused_field`
is a steered far-field superposition and `superpose_tt` applies unchanged. The
open decision is whether the API should *also* support genuine near-field focusing
(it is reachable: ~1e5 m at 1 MHz), and if so under what projection rule.

**This was resolved by SPIKE-9.6 → ADR-0006, above.** T-10.1 (`spot_size`) sits
behind T-9.6.

Two further things are already settled and waiting:

- **T-10.1's citation is verified.** The −3 dB (FWHM) transverse extent of a
  uniformly-illuminated circular aperture is `w = 1.029 λr/D`, from the root
  `x = 1.61633` of `2J₁(x)/x = 1/√2` — reproducible with `scipy.special.j1`, so
  no textbook page is needed. **Do not use 1.22**: that is the Rayleigh first
  null, not the −3 dB width. The result is polarization-independent (it is the
  Fourier transform of the aperture function) and is therefore safe here — but
  only for aperture geometry, never for how `h₊`/`h×` combine.
- **The far-field degeneracy is a wall, not a bug** (CLAUDE.md rule 5). It is the
  same wall T-10.2 states as `D/λ ≳ 6e9`. If a change makes it vanish, the change
  is defective.

### ✅ T-4.5 is done — SPIKE-4.5 closed it (ADR-0007)

**Resolved 2026-08-02.** `finite_size_correction` is implemented in
`bodies/multipole.py` as `F₂(kR) = 1 − 5(kR)²/98` (EQ-034), and T-4.7/4.8/4.9 are
unblocked. See §0 for the summary and
[ADR-0007](adr/0007-uniform-sphere-quadrupole-form-factor.md) for the derivation,
the numerical verification, and the reversal condition.

**The citation search failed and that outcome is the decision.** No numbered
equation exists in any accessible source; the result is **Category B** (our
derivation), justified by three independent numerical routes rather than by a
reference. Thorne, *Rev. Mod. Phys.* 52:299 (1980) is still paywalled with an
**unconfirmed** equation number — per rule 1 a guessed number is worse than
none, so it is cited *without* one, deliberately.

**Do not "improve" this by finding a source that says `1 − (kR)²/14`.** That is
the *surface*-deformation profile (ADR-0007 eq. 5), a different physical case,
and it confirms something else. See §0 for both traps.

The original tension is recorded below for context.

---

#### T-4.5 — the block as it stood

`researcher` returned **UNVERIFIED** and, in doing so, found the task's premise
was wrong. Both form factors named in the backlog are the wrong multipole order:
`sin(kR)/(kR)` is `l=0` **spin-1 antenna machinery** (rule 4's trap), and
`3j₁(kR)/(kR)` is the total-mass monopole. The `l=2` result appears to be
`1 − 5(kR)²/98`, but no numbered equation for it was found — it is a derivation.
The AC's ">1% at R/λ > 0.1" threshold was computed from the wrong form factor and
must be redone. **Resolved as above; the recomputed departure is 2.0142%.**

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
.venv\Scripts\python.exe -m mypy src
.venv\Scripts\python.exe tools\check_citations.py
.venv\Scripts\python.exe -m pytest -q
```

All five must pass. All five are green as of 2026-08-03 (896 passing, 3 skipped).

> ⚠️ **Use `python -m mypy` / `python -m pytest`, NOT `mypy.exe` / `pytest.exe`.**
> Found 2026-08-03: both console-script shims in `.venv\Scripts\` are broken on this host —
> they exit **1 with zero output**. The previously-documented `.venv\Scripts\mypy.exe src`
> therefore looks exactly like a failing gate carrying no diagnostic, which is this
> project's own rule-8 failure mode — something vanishing with no signal — reproduced
> inside its own commit gate. **The code was clean throughout:** `python -m mypy src`
> reports *Success: no issues found in 38 source files*. `ruff.exe` is unaffected because
> it is a standalone Rust binary rather than a Python shim. If any `.venv\Scripts\*.exe`
> ever exits non-zero with no output, reach for the `python -m` form before believing the
> failure. Then mark finished tasks
✅ in `BACKLOG.md` so the scheduler stays truthful.
