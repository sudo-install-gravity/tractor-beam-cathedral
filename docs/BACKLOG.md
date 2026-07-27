# Backlog

Full task enumeration, Sprints 0–12. Two-week sprints, ~22 points velocity.

**Every task here must satisfy the Definition of Ready before work starts:** exact file path,
exact signature, formula and citation supplied, exact test assertions with tolerances, zero
open design decisions, ≤3 story points.

Citations marked `[verify]` must be confirmed by the `researcher` agent at sprint planning
before the task may be implemented. A task whose citation cannot be verified is **blocked** and
becomes a spike.

**Legend:** `pts` = story points · `deps` = blocking task IDs · `SPIKE-*` = design work, produces
an ADR in `docs/adr/`, never production code.

## Agent tiers

Every task carries a recommended execution tier. The scheduler
(`tools/schedule.py`) reads these to batch work into sessions — run
`python tools/schedule.py --plan` for the current run order.

| Tier | Count | When it applies |
|---|---|---|
| `sonnet-low` | 79 | Fully specified. Exact path, signature, formula, citation, and test assertions supplied; **zero open decisions**. The Definition of Ready exists to make tasks land here. |
| `sonnet` | 20 | Moderate judgment: parity against an external package, visual encoding, prose for humans, reproducing a published worked example, interpreting a sweep. |
| `opus` | 16 | **Heavy lift.** A task is `opus` if it (a) is a spike or produces an ADR, (b) requires a physics derivation, (c) defines a cross-cutting interface every later epic writes to, (d) has no reference implementation to check against, or (e) authors specs for other tasks. |

The three support agents (`researcher`, `code-reviewer`, `indexer`) run at their
own defined models on **every** task regardless of tier — they are workflow
stages, not a tier. See [`../CLAUDE.md`](../CLAUDE.md).

**Why the tier is a scheduling input, not just a label.** Switching models costs a
session boundary: context must be re-established, and the cost is paid per switch
rather than per task. The scheduler therefore looks ahead across the dependency
graph and batches every reachable `opus` task into one session before handing the
bulk back to `sonnet-low`. Tiering tasks without batching them would pay that cost
16 times.

---

## Sprint 0 — Foundation & Governance ✅ complete (24 pts)

**Carry-over: T-0.9 branch protection.** GitHub returns 403 —
`Upgrade to GitHub Pro or make this repository public to enable this feature`.
Branch protection on `main` requiring green CI is therefore **deferred until the repo
goes public**, which the plan schedules for no later than gate G1 (end of Sprint 2).
Tracked as **T-2.9** below, which carries the remaining acceptance criterion. T-0.9 itself is
complete (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, PR template all present) and is marked ✅ so
the scheduler stops offering it.

| ID | Task | pts | agent | deps | Status |
|---|---|---|---|---|---|
| T-0.1 | Repo scaffold, `pyproject.toml`, package tree | 3 | `sonnet-low` | — | ✅ |
| T-0.2 | Agent definitions in `.claude/agents/` | 3 | `sonnet-low` | T-0.1 | ✅ |
| T-0.3 | `CLAUDE.md` operating instructions | 2 | `sonnet-low` | T-0.1 | ✅ |
| T-0.4 | Governance docs: CLAIMS, PHYSICS, INDEX, ADR-0001 | 3 | `sonnet-low` | T-0.1 | ✅ |
| T-0.5 | CI pipeline (`ruff`, `mypy`, `pytest`) | 3 | `sonnet-low` | T-0.1 | ✅ |
| T-0.6 | Citation-discipline CI check | 3 | `sonnet-low` | T-0.5 | ✅ |
| T-0.7 | Validation harness skeleton | 3 | `sonnet-low` | T-0.1 | ✅ |
| T-0.8 | This backlog | 2 | `opus` | T-0.4 | ✅ |
| T-0.9 | LICENSE, CONTRIBUTING, CoC, PR template | 2 | `sonnet-low` | T-0.1 | ✅ |

---

## Sprint 1 — Source Physics Engine, part 1 (30 pts) ⚠️ over velocity

Gate: none. Feeds **G1**.

**Citations verified 2026-07-26.** All Sprint 1 equations resolved to open-access, peer-reviewed
sources with checkable equation numbers. Textbook citations (Maggiore, MTW) were *rejected*
during verification: their exact equation numbers could not be confirmed without the physical
books, and a citation a contributor cannot check is not a citation. Primary sources are now:

- **[B]** Blanchet, L., "Gravitational Radiation from Post-Newtonian Sources and Inspiralling
  Compact Binaries," *Living Rev. Relativ.* **17**:2 (2014), arXiv:1310.1528. Open access.
- **[FH]** Flanagan, É.É. & Hughes, S.A., "The basics of gravitational wave theory,"
  *New J. Phys.* **7**:204 (2005), arXiv:gr-qc/0501041. Open access.

⚠️ **[FH] Eqs. (4.41) and (4.42) contain typos** — see [`docs/ERRATA.md`](ERRATA.md), ERR-001 and
ERR-002. T-1.9 must use the corrected forms.

**All tasks assume [ADR-0002](adr/0002-array-conventions.md):** `masses (N,)`, `positions (N,3)`,
tensors with trailing indices, `n_hat` unit-validated, SI units, float64, `Q_ij` trace-free.

**Over-commit, stated deliberately.** 30 points against a ~22 velocity. **Drop candidate: T-1.9**
— it moves to Sprint 2 alongside T-2.8 without endangering gate G1, which closes at the end of
Sprint 2. T-1.10 is *not* a drop candidate despite also being a benchmark: it was pulled forward
precisely because discovering a dipole surprise late is the expensive failure mode.

**T-1.0 · Canonical circular-binary fixture · 2 pts · `sonnet` · deps T-0.7** ✅
`tests/benchmarks/helpers.py` — add `circular_binary(m1, m2, a, t)` returning
`(masses, positions, velocities, accelerations, jerks)` in **ADR-0002 shapes and SI units**, for
two bodies in a circular orbit about their common barycentre in the xy-plane:

```
M = m1 + m2 ;  mu = m1 m2 / M ;  omega = sqrt(G M / a^3)     (Kepler)
relative displacement   x_rel(t) = ( a cos(omega t), a sin(omega t), 0 )
body 1 at  +(m2/M) x_rel(t) ,  body 2 at  -(m1/M) x_rel(t)
v, acc, jerk are the analytic 1st/2nd/3rd derivatives of those positions
```

Also add fixture `binary_si()` returning the canonical parameter set used by every Sprint 1
benchmark: `m1 = m2 = 1.0e30 kg`, `a = 1.0e9 m`, `r = 1.0e20 m`, evaluated at `t = 0.3 / omega`.
*AC:* barycentric to **relative** precision — `|sum_A m_A x_A| / max_A|m_A x_A| < 1e-14`;
numerical derivative of `positions` matches `velocities` to rtol 1e-6 at step `h = 1e-3/omega`,
and likewise `accelerations`, `jerks`; `omega` satisfies Kepler's third law to rtol 1e-12.
⚠️ **The barycentric criterion must be relative, not absolute.** An earlier draft specified
`atol 1e-9`, which is unachievable at astronomical scale: with `m ~ 1e30` and `x ~ 1e9`, the
products are `~1e39` and the FP64 roundoff floor is `~1e23` — thirty-two orders above the
stated tolerance. It appeared to pass only because the canonical set is **equal-mass**, where
`f1 = +0.5` and `f2 = -0.5` cancel exactly; at any other mass ratio it fails. Measured
residuals: `0.0` at 1:1 and 1:2, `1.5e23` at 1:3 and 1.3:2.7.
*Why this exists:* T-1.4, T-1.5, T-1.8 and T-1.9 all assert "on a circular binary" but none
defined one. Four tasks would each invent a fixture and they would differ — the same
cross-cutting gap ADR-0002 fixed for array shapes.

**T-1.1 · Physical constants · 2 pts · `sonnet-low` · deps T-0.1** ✅
`src/gwtb/core/constants.py`. Module-level `float` constants, each with a source comment:
`G = 6.67430e-11` (CODATA 2018), `c = 299792458.0` (SI exact), `AU = 1.495978707e11` (IAU 2012
exact), `M_SUN = 1.98892e30` (IAU 2015 nominal solar mass parameter GM_sun/G),
`PARSEC = 3.0856775814913673e16` (IAU 2015, = 648000/pi x AU). Derived: `G_OVER_C4`, `G_OVER_C5`.
*AC:* `G == 6.67430e-11` and `c == 299792458.0` exactly; `G_OVER_C4 == 8.2627176397e-45` and
`G_OVER_C5 == 2.7561459334e-53`, both to rtol 1e-9.

**T-1.2 · Scaled strain units · 3 pts · `sonnet-low` · deps T-1.1** ✅
`src/gwtb/core/units.py` — `class StrainScale` with `__init__(self, reference: float = 1e-40)`,
`to_scaled(self, h: float | np.ndarray) -> float | np.ndarray` returning `h / reference`, and
`from_scaled(self, h_s)` returning `h_s * reference`. Accepts scalars and arrays.
*AC:* `from_scaled(to_scaled(x)) == x` to rtol 1e-15 for `x` in `np.logspace(-45, -35, 50)`;
`to_scaled(1e-40) == 1.0` exactly; `ValueError` on `reference <= 0` or non-finite.

**T-1.3 · Trace-free mass quadrupole moment · 3 pts · `sonnet-low` · deps T-1.1** ✅
`src/gwtb/bodies/multipole.py` — `quadrupole_moment(masses, positions) -> np.ndarray` of shape
`(3,3)`. For point masses, Blanchet eq. (3) with `rho = sum_A m_A delta^3(x - x_A)`:

```
Q_ij = sum_A m_A ( x_i x_j - (1/3) delta_ij |x|^2 )
```

Implement as `einsum('a,ai,aj->ij', m, x, x) - eye(3) * einsum('a,ai,ai->', m, x, x) / 3`.
*Citation:* `Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 3`
*AC:* traceless to atol 1e-12 (relative to `max|Q|`); symmetric to atol 1e-15; unit mass at
`(1,0,0)` returns `diag(2/3, -1/3, -1/3)` to rtol 1e-15; a 50-point spherically symmetric shell
returns zeros to atol 1e-12; raises on shape mismatch or float32 input.

**T-1.4 · Analytic second derivative of Q · 3 pts · `sonnet-low` · deps T-1.3, T-1.0** ✅
`src/gwtb/bodies/multipole.py` — `quadrupole_second_derivative(masses, positions, velocities,
accelerations) -> np.ndarray` of shape `(3,3)`. **Analytic. Never finite-difference.**

Differentiating Blanchet eq. (3) twice for point masses:

```
Qdd_ij = sum_A m_A ( a_i x_j + 2 v_i v_j + x_i a_j )
         - (2/3) delta_ij sum_A m_A ( v.v + x.a )
```

*Citation:* `Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 3` (differentiated; see
`docs/PHYSICS.md` §2.1). Claim category **B** (derived) in `CLAIMS.md`.
*AC:* traceless to atol 1e-12; symmetric; matches a central difference of `quadrupole_moment`
on a circular binary to **rtol 1e-5 using step `h = 1e-3` in units where `omega = 1`**
(second derivatives are roundoff-dominated below `h ~ 1e-4`).

**T-1.5 · Analytic third derivative of Q · 3 pts · `sonnet-low` · deps T-1.4, T-1.0** ✅
`src/gwtb/bodies/multipole.py` — `quadrupole_third_derivative(masses, positions, velocities,
accelerations, jerks) -> np.ndarray` of shape `(3,3)`. **Analytic. Never finite-difference.**

```
Qddd_ij = sum_A m_A ( j_i x_j + 3 a_i v_j + 3 v_i a_j + x_i j_j )
          - (2/3) delta_ij sum_A m_A ( 3 v.a + x.j )
```

*Citation:* `Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 3` (differentiated). Claim
category **B**.
*AC:* traceless to atol 1e-12; symmetric; matches the **first** derivative of
`quadrupole_second_derivative` taken with the 5-point central stencil
`(-f(t+2h) + 8f(t+h) - 8f(t-h) + f(t-2h)) / (12h)` at step `h = 1e-3 / omega`, to **rtol 1e-5**.
Differentiating `Qdd` once this way measures 5.9e-13; do **not** instead build a third-derivative
stencil directly on `quadrupole_moment`, which is roundoff-dominated (see the table below).
⚠️ **The tolerance is step-size dependent and this is not negotiable.** Third-derivative
finite differences are roundoff-dominated as `eps/h^3`: measured relative error is `1.1e-1` at
`h = 1e-5` and `1.1e+2` at `h = 1e-6`, versus `8.0e-7` at `h = 1e-3`. A test written with a
"tighter" step **will fail against correct code**. This is the concrete reason ADR-0001 and
`code-reviewer.md` forbid numerical differentiation of `Q`.

**T-1.6 · TT projector · 3 pts · `sonnet-low` · deps T-1.1** ✅
`src/gwtb/propagate/tt_projection.py` — `tt_projector(n_hat) -> np.ndarray` of shape
`(3,3,3,3)`:

```
P_ij       = delta_ij - n_i n_j
Lambda_ijkl = P_ik P_jl - (1/2) P_ij P_kl
```

Also `apply_tt(tensor, n_hat) -> np.ndarray` contracting `Lambda_ijkl T_kl`.
*Citation:* `Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.22` (projector defined
at eq. 4.20; equivalent form at Blanchet eq. 2).
*AC:* over 20 random `n_hat` and 20 random symmetric `M`: idempotent
(`apply_tt(apply_tt(M)) == apply_tt(M)`) to rtol 1e-12; result traceless to atol 1e-12;
transverse (`n_i (Lambda:M)_ij == 0`) to atol 1e-12; `ValueError` if `|n_hat| != 1` to atol 1e-12.

**T-1.7 · Quadrupole strain · 3 pts · `sonnet-low` · deps T-1.4, T-1.6** ✅
`src/gwtb/source/quadrupole.py` — `strain_tt(q_ddot, r, n_hat) -> np.ndarray` of shape `(3,3)`:

```
h_ij^TT = (2G / (c^4 r)) * Lambda_ijkl * Qdd_kl
```

**This function does not compute retarded time.** It takes `q_ddot` as an already-evaluated
`(3,3)` array; the caller is responsible for having evaluated it at `t - r/c`. Do **not** add a
time parameter or perform retardation here — that belongs in `propagate/retarded.py` (Sprint 6),
where retardation must be computed per source element rather than from an array centroid.

*Citation:* `Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 2`
*AC:* traceless and transverse to atol 1e-12; halving `r` doubles `|h|` to rtol 1e-12;
dimensionless (a dimensional-consistency test asserts SI units cancel); `ValueError` on `r <= 0`.
**Note:** [FH] eq. 4.23 gives this in geometric units (`G = c = 1`); the `2G/c^4` prefactor per
ADR-0002 §4 is mandatory here.

**T-1.8 · GW luminosity · 2 pts · `sonnet-low` · deps T-1.5, T-1.0** ✅
`src/gwtb/source/quadrupole.py` — `luminosity(q_dddot) -> float`:

```
F = (G / (5 c^5)) * Qddd_ij * Qddd_ij
```

*Citation:* `Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 4`
*AC:* for an equal-mass circular binary reproduces
`L = (32/5)(G/c^5) mu^2 a^4 omega^6` (with `a` the **separation**) to **rtol 1e-12** — an exact algebraic
identity, not an approximation, and was confirmed numerically at 4.1e-16. Equivalently
`L = (32/5)(G^4/c^5) m1^2 m2^2 M / a^5` under Kepler's third law. Returns a non-negative float.

**T-1.9 · Benchmark: circular binary · 3 pts · `sonnet-low` · deps T-1.7, T-1.8, T-1.0** ✅
`tests/benchmarks/test_binary.py`. Equal-mass circular binary, separation `a`, orbital angular
frequency `omega`, reduced mass `mu = m1 m2 / (m1 + m2)`, observer at distance `r`,
inclination `iota`:

```
amplitude  A   = 4 G mu omega^2 a^2 / (c^4 r)
h_plus         = -A * (1 + cos^2 iota)/2 * cos(2 omega t)
h_cross        = -A * cos(iota)          * sin(2 omega t)
L              = (32/5)(G/c^5) mu^2 a^4 omega^6
```

**The signs above hold only under these two conventions, which are binding for this test:**

1. **Phase origin:** relative displacement `x_rel(t) = (a cos(omega t), a sin(omega t), 0)` with
   `t = 0` at `x_rel = (a, 0, 0)` — i.e. the fixture from T-1.0, used unmodified.
2. **Polarization extraction:** `h_plus := (h_11 - h_22) / 2` and `h_cross := h_12`.

Swapping the phase origin to `(a sin, a cos, 0)` **flips the sign of `h_plus`**, and the AC below
compares *signed* values at rtol 1e-6, so a mismatched convention fails with no obvious cause.
Verified: under conventions (1) and (2) the implementation reproduces the closed forms to 2.7e-7
(finite-difference limited).

For the face-on case (`iota = 0`, `n_hat = z_hat`) the trace-free `Qdd` is already transverse,
so TT projection is the identity — use this as the simplest assertion.
*Citation:* `Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.43` (amplitude);
luminosity per T-1.8.
*AC:* `h_plus`, `h_cross`, and `L` each to rtol 1e-6.
⚠️ **Include a test named `test_errata_flanagan_hughes_4_41_4_42`** asserting the **corrected**
forms from [`docs/ERRATA.md`](ERRATA.md): `I_22 = mu R^2 (sin^2 wt - 1/3)`, and `Qdd` symmetric
with `(2,1) = +sin(2wt)` inside the `-2 omega^2 mu R^2` prefactor. The as-printed `(4.42)` is
non-symmetric and differs from ground truth by 3.98 in units `mu = R = omega = 1`. **Do not
"fix" this test to match the paper.**

**T-1.10 · Benchmark: dipole cancellation · 3 pts · `sonnet-low` · deps T-1.3, T-1.7** ✅ ⚠️ **pulled forward**
`tests/benchmarks/test_dipole_cancellation.py`. In a momentum-conserving configuration the mass
dipole's second derivative must vanish:

```
d_i     = sum_A m_A x_i                 (mass dipole)
ddd_i   = sum_A m_A a_i                 (equals dP/dt, the net external force)
a_char  = max_A |a_A|                   (characteristic acceleration scale)
M_total = sum_A m_A
```

Generate configurations by drawing `N = 5` random masses and accelerations, then subtracting the
mass-weighted mean acceleration so `sum_A m_A a_A = 0` exactly.
*Citation:* `Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 3` (multipole structure; the
dipole's non-radiation follows from momentum conservation — see `docs/PHYSICS.md` §2).
*AC:* `|ddd_i| / (M_total * a_char) < 1e-12` for 20 random momentum-conserving configurations;
and a positive control asserting the ratio **exceeds 1e-3** for a deliberately unbalanced
configuration, so the test cannot pass vacuously.
*Why here:* validates the project's central physics framing (decision 1). **Open question OQ-1.**

---

## Sprint 2 — Conservation auditing, dipole flagging, ledger v0 (26 pts) → **GATE G1**

**T-2.1 · Stress-energy conservation auditor · 3 pts · `sonnet-low` · deps T-1.3** ✅
`src/gwtb/source/conservation.py` — `audit(masses, accelerations) -> ConservationReport` with
fields `net_force`, `is_conserving`, `residual`.
*AC:* returns `is_conserving=True` for balanced configurations, `False` otherwise; residual
scales linearly with imposed imbalance.

**T-2.2 · UNPHYSICAL stamping · 3 pts · `opus` · deps T-2.1**
`src/gwtb/source/conservation.py` — `class StampedResult` wrapping any array with a
`provenance` field; `repr` and any serialization carry
`UNPHYSICAL: violates d_mu T^mu-nu = 0` when set.
*AC:* stamp survives arithmetic, slicing, and `str()`; a test asserts it cannot be silently
dropped by `np.asarray`.

**T-2.3 · Mass dipole moment · 2 pts · `sonnet-low` · deps T-1.3** ✅
`src/gwtb/source/multipole_rad.py` — `dipole_moment(masses, positions)` and
`dipole_second_derivative(masses, accelerations)`.
*Citation:* MTW §36.1 `[verify]`.
*AC:* equals total momentum derivative; zero for momentum-conserving input to atol 1e-12.

**T-2.4 · Dipole radiation term (flagged) · 3 pts · `sonnet-low` · deps T-2.2, T-2.3**
`src/gwtb/source/multipole_rad.py` — `dipole_strain(d_ddot, r, n_hat) -> StampedResult`.
*AC:* always returns a stamped result; raises if called with a momentum-conserving source
unless `allow_trivial=True`.

**T-2.5 · Mass octupole moment · 3 pts · `sonnet-low` · deps T-1.3** ✅
`src/gwtb/bodies/multipole.py` — `octupole_moment(masses, positions) -> np.ndarray` (3,3,3).
*Citation:* Maggiore Vol. 1, ch. 3 `[verify]`.
*AC:* fully symmetric; traceless on all index pairs to atol 1e-12.

**T-2.6 · Ledger metric schema · 3 pts · `opus` · deps T-1.8** 🔒 **freeze**
`src/gwtb/ledger/gap_report.py` — `@dataclass GapMetric(name, achieved, required, units,
source_module)` and `class GapReport` with `add()`, `to_markdown()`, `to_json()`.
*AC:* schema round-trips through JSON; `to_markdown` renders a stable table.
*Why freeze:* the ledger reads outputs from every epic. Later epics write to this contract;
without a freeze the ledger chases interface changes all project long.

**T-2.7 · Ledger: emission-magnitude row · 2 pts · `sonnet-low` · deps T-2.6**
`src/gwtb/ledger/gap_report.py` — `emission_gap(luminosity, target_impulse, duration)`.
*AC:* for a 10 t / 10 m / 1 kHz rod reports a gap within 0.5 decades of 1e-19 W.

**T-2.8 · Benchmark: spinning rod · 2 pts · `sonnet` · deps T-1.8** ✅
`tests/benchmarks/test_spinning_rod.py`. `P = (2/45)(G/c⁵) M² L⁴ ω⁶`.
*Citation:* `[verify]`.
*AC:* rtol 1e-6 against the analytic expression.

**T-2.10 · Convention enforcement tests · 2 pts · `sonnet-low` · deps T-1.7**
`tests/unit/test_conventions.py`. Assert the ADR-0002 contracts against every public function
shipped so far: `(N,)`/`(N,3)` input shapes accepted and wrong shapes rejected; trailing tensor
indices; `n_hat` non-unit input raises `ValueError`; float32 input raises rather than upcasting;
returned arrays are float64.
*AC:* every public function in `bodies/`, `propagate/`, `source/` is covered by at least one
shape-rejection and one dtype-rejection assertion.
*Why here:* [ADR-0002](adr/0002-array-conventions.md) states these are enforced by this file, but
no Sprint 1 task created it — an ADR promising an artifact nothing delivered.

**T-2.9 · Branch protection (carried from T-0.9) · 1 pts · `sonnet-low` · deps repo made public**
`repo-level`. Require green CI on `main`; block force-push and deletion.
*AC:* `gh api repos/Thanatos7777/tractor_beam_cathedral/branches/main/protection` returns a
`required_status_checks` block listing `test (3.10)`, `test (3.11)`, `test (3.12)`.
*Blocked by:* GitHub plan limits — private repos on the free tier cannot set branch
protection. Unblocks the moment the repo is made public.

**SPIKE-4.4 · Two-element spin-2 superposition prototype · 3 pts · `opus` · deps T-1.7, T-1.6** ⚠️
Scratch prototype only. Superpose two quadrupole sources of differing orientation at a common
far-field point; compare polarization-mismatch behavior against hand-derived analytics.
*Deliverable:* `docs/adr/0002-spin2-superposition.md` — the correct formulation, the
mismatch-loss expression, and whether array gain departs from N². **No production code.**
*Why here:* `F-4.4` is the highest-risk node on the critical path and has no external reference
implementation. Four sprints of lead time on a conceptual error. **Open question OQ-2.**

---

## Sprint 3 — Finite maneuver kinematics (22 pts)

**T-3.1 · Profile base class · 2 pts · `sonnet-low` · deps T-1.1** ✅
`src/gwtb/kinematics/profiles.py` — `class AccelerationProfile` (ABC) with
`acceleration(t)`, `velocity(t)`, `position(t)`, `jerk(t)`, property `duration`.
*AC:* subclass contract enforced; velocity/position match analytic integrals to rtol 1e-9.

**T-3.2 · Bang-bang profile · 2 pts · `sonnet-low` · deps T-3.1** ✅
`src/gwtb/kinematics/profiles.py` — `BangBangProfile(a_max, duration)`. Rectangular acceleration.
*AC:* Δv = a_max·duration/2 for the symmetric case; spectrum shows −13 dB first sidelobe.

**T-3.3 · Jerk-limited S-curve · 3 pts · `sonnet-low` · deps T-3.1** ✅
`src/gwtb/kinematics/profiles.py` — `SCurveProfile(a_max, j_max, duration)` — trapezoidal acceleration, standard in spacecraft
maneuver planning.
*AC:* `|jerk| ≤ j_max` everywhere; `|a| ≤ a_max`; C¹ continuous.

**T-3.4 · Quintic polynomial profile · 2 pts · `sonnet-low` · deps T-3.1** ✅
`src/gwtb/kinematics/profiles.py` — `QuinticProfile(delta_v, duration)`. Zero acceleration and jerk at both endpoints.
*AC:* endpoint derivatives zero to atol 1e-12; Δv exact to rtol 1e-12.

**T-3.5 · Raised-cosine profile · 2 pts · `sonnet-low` · deps T-3.1** ✅
`src/gwtb/kinematics/profiles.py` — `RaisedCosineProfile(delta_v, duration)`.
*AC:* matches a Hann window in spectral rolloff to rtol 1e-6.

**T-3.6 · Spectral analysis of profiles · 3 pts · `sonnet` · deps T-3.2–T-3.5** ✅
`src/gwtb/kinematics/profiles.py` — `spectrum(profile, n_fft) -> (freqs, magnitude)`.
*AC:* Parseval holds to rtol 1e-9; first-sidelobe levels match the window-function analogues
(rect −13 dB, Hann −31 dB) to ±1 dB.

**T-3.7 · Linear memory · 3 pts · `opus` · deps T-1.7**
`src/gwtb/source/memory.py` — `linear_memory(masses, velocities_initial, velocities_final, r,
n_hat)`. `Δh_ij^TT = (4G/c⁴r) Λ_ij,kl Δ[Σ_A M_A v^k v^l]`.
*Citation:* Braginsky & Thorne, *Nature* 327:123 (1987) `[verify]`.
*AC:* traceless/transverse; zero when velocities unchanged; scales as 1/r.

**T-3.8 · Waveform from a maneuver · 3 pts · `sonnet-low` · deps T-3.1, T-1.7**
`src/gwtb/source/quadrupole.py` — `waveform_from_profile(body, profile, r, n_hat, times)`.
*AC:* strain returns to the memory offset (not zero) after the maneuver ends, to rtol 1e-6.

**T-3.9 · Benchmark: memory effect · 2 pts · `sonnet-low` · deps T-3.7**
`tests/benchmarks/test_memory.py` — hyperbolic two-body scattering.
*AC:* offset matches the analytic result to rtol 1e-4.

---

## Sprint 4 — Body parameterization (23 pts)

**T-4.1 · Rigid uniform sphere · 2 pts · `sonnet-low` · deps T-1.1** ✅
`src/gwtb/bodies/sphere.py` — `@dataclass Sphere(radius, density)` with `mass`, `moment_of_inertia`.
*AC:* `mass == (4/3)πR³ρ` to rtol 1e-12; rejects non-positive radius or density.

**T-4.2 · Degeneracy guard · 3 pts · `sonnet-low` · deps T-4.1** ✅ ⚠️
`src/gwtb/bodies/sphere.py` — `Sphere.self_quadrupole()` returns exact zeros, and
`degeneracy_warning()` explains that R and ρ enter only through M in the rigid
long-wavelength model.
*Citation:* claim B-2 in `CLAIMS.md`.
*AC:* self-quadrupole is zero to atol 1e-15 for 20 random spheres; two spheres with equal M but
different (R, ρ) produce **identical** radiation in the rigid model — asserted explicitly, since
this is the surprising result the API must not hide.

**T-4.3 · Love-number deformation model · 3 pts · `opus` · deps T-4.1**
`src/gwtb/bodies/elastic.py` — `induced_quadrupole(sphere, acceleration, love_k2, rigidity)`.
*Citation:* `[verify]` — tidal Love number formalism.
*AC:* scales linearly with acceleration; → 0 as rigidity → ∞; **R and ρ now enter
independently** (asserted against T-4.2).

**T-4.4 · Material property library · 2 pts · `sonnet-low` · deps T-4.3**
`src/gwtb/bodies/elastic.py` — `MATERIALS` dict with rigidity and density for steel, tungsten,
osmium, and a nominal degenerate-matter placeholder, each with a source.
*AC:* every entry has a citation comment; densities within 1% of published values.

**T-4.5 · Finite-size retardation correction · 3 pts · `opus` · deps T-4.1**
`src/gwtb/bodies/multipole.py` — `finite_size_correction(sphere, wavelength) -> float`,
the leading correction in `R/λ`.
*AC:* → 1 as `R/λ → 0`; departs from unity by >1% when `R/λ > 0.1`. **Open question OQ-3.**

**T-4.6 · Rotational oblateness · 2 pts · `sonnet-low` · deps T-4.1** ✅
`src/gwtb/bodies/sphere.py` — `oblateness_quadrupole(sphere, spin_rate)`.
*AC:* zero at zero spin; scales as spin²; matches the Maclaurin spheroid limit to rtol 1e-3.

**T-4.7 · Assumption-ledger integration · 2 pts · `sonnet-low` · deps T-4.5**
`src/gwtb/bodies/multipole.py` — emit a structured warning when `R/λ > 0.1` naming the
violated assumption and pointing at `docs/INDEX.md` §3.
*AC:* warning raised exactly at the threshold; message names the assumption.

**T-4.8 · Sensitivity study · 3 pts · `sonnet` · deps T-4.3, T-4.5**
`tests/benchmarks/test_body_sensitivity.py` — sweep R and ρ at fixed M; assert radiation is
invariant in the rigid model and variant in the elastic model.
*AC:* rigid variation < 1e-12 relative; elastic variation > 1e-3 relative for realistic rigidity.

**T-4.9 · Ledger: body-parameter row · 3 pts · `sonnet-low` · deps T-2.6, T-4.8**
`src/gwtb/ledger/gap_report.py` — record achievable quadrupole vs. required.
*AC:* row appears in `to_markdown()` with correct units.

---

## Sprint 5 — Spin-2 foundations and array geometry (22 pts)

**T-5.1 · Polarization basis · 3 pts · `opus` · deps T-1.6**
`src/gwtb/propagate/polarization.py` — `polarization_basis(n_hat) -> (e_plus, e_cross)`.
*Citation:* MTW §35.6 `[verify]`.
*AC:* both traceless and transverse; orthonormal under `e_A:e_B = 2δ_AB`; **rotating the basis
by ψ about `n_hat` transforms the amplitudes by e^(2iψ) — asserted directly, not assumed.**

**T-5.2 · Strain decomposition · 2 pts · `sonnet-low` · deps T-5.1**
`src/gwtb/propagate/polarization.py` — `decompose(h_ij, n_hat) -> (h_plus, h_cross)` and
`recompose(h_plus, h_cross, n_hat)`.
*AC:* round-trip identity to rtol 1e-12 over 20 random TT tensors.

**T-5.3 · Spin-2 rotation operator · 3 pts · `sonnet-low` · deps T-5.1**
`src/gwtb/propagate/polarization.py` — `rotate_polarization(h_plus, h_cross, psi)`.
*AC:* period is π, not 2π (the spin-2 signature); `rotate(·, π/4)` maps `h₊ → h×`.

**T-5.4 · Quadrupole element patterns · 3 pts · `opus` · deps T-5.1**
`src/gwtb/propagate/polarization.py` — `element_pattern_rotating(theta)` returning
`h₊ ∝ (1+cos²θ)/2`, `h× ∝ cos θ`; `element_pattern_linear(theta)` returning `h₊ ∝ sin²θ`.
*Citation:* Maggiore Vol. 1, ch. 3 `[verify]`.
*AC:* linear pattern is zero on-axis (θ=0) and maximal at θ=π/2 — **the opposite of a dipole
antenna pattern**, asserted explicitly to catch spin-1 substitution.

**T-5.5 · Array geometry: linear · 2 pts · `sonnet-low` · deps T-1.1** ✅
`src/gwtb/array/geometry.py` — `linear_array(n_elements, spacing) -> np.ndarray` (N,3).
*AC:* correct count; uniform spacing to rtol 1e-12; centered on origin.

**T-5.6 · Array geometry: planar · 2 pts · `sonnet-low` · deps T-5.5** ✅
`src/gwtb/array/geometry.py` — `planar_array(nx, ny, dx, dy)`.
*AC:* `nx*ny` elements; all coplanar to atol 1e-12.

**T-5.7 · Array geometry: sparse/random · 2 pts · `sonnet` · deps T-5.5** ✅
`src/gwtb/array/geometry.py` — `sparse_array(n_elements, aperture, seed)`.
*AC:* reproducible for a fixed seed; all elements within the aperture. **Open question OQ-4.**

**T-5.8 · Grating-lobe constraint · 2 pts · `sonnet-low` · deps T-5.5** ✅
`src/gwtb/array/grating.py` — `max_spacing(wavelength, scan_angle_max)` returning
`λ/(1+|sin θ_max|)`, and `has_grating_lobes(geometry, wavelength, scan_angle_max)`.
*Citation:* Balanis ch. 6 `[verify]`.
*AC:* at 1 Hz (λ=3e8 m) full-hemisphere scan requires spacing ≤ 1.5e8 m — asserted, because the
scale of that number is itself a finding.

**T-5.9 · Ledger v1: aperture row · 3 pts · `sonnet-low` · deps T-2.6, T-5.5**
`src/gwtb/ledger/gap_report.py` — `aperture_gap(geometry, wavelength, range_m, spot_size)`
reporting achieved vs. required `D/λ ≳ r/w`.
*AC:* for a 1 km spot at 40 AU reports required `D/λ` within 0.5 decades of 6e9, **at any
frequency** — the frequency-independence is the assertion.

---

## Sprint 6 — Phased array and propagation (24 pts) → **GATE G2**

**T-6.1 · Scalar array factor · 3 pts · `sonnet` · deps T-5.5**
`src/gwtb/array/beamform.py` — `array_factor(geometry, weights, wavelength, direction)`.
`AF = Σ_n w_n exp[i(k·r_n + φ_n)]`.
*Citation:* Balanis ch. 6 `[verify]`.
*AC:* uniform broadside array reproduces the analytic `sin(Nψ/2)/sin(ψ/2)` to rtol 1e-9;
**matches `arraytool` output to rtol 1e-9** — the known-good baseline before departing to spin-2.

**T-6.2 · Beam steering · 2 pts · `sonnet-low` · deps T-6.1**
`src/gwtb/array/beamform.py` — `steering_phases(geometry, wavelength, target_direction) -> np.ndarray`.
*AC:* peak of the steered pattern lies within 1e-6 rad of the requested direction.

**T-6.3 · Beamwidth and sidelobes · 2 pts · `sonnet-low` · deps T-6.1**
`src/gwtb/array/beamform.py` — `beamwidth_3db(...)`, `peak_sidelobe_level(...)`.
*AC:* uniform array reproduces `θ_3dB ≈ 0.886 λ/(Nd)` to rtol 1e-3 and −13.2 dB PSL to ±0.2 dB.

**T-6.4 · Amplitude tapering · 3 pts · `sonnet` · deps T-6.1**
`src/gwtb/array/beamform.py` — `taper(n, kind)` for `uniform`, `hann`, `hamming`,
`chebyshev(sll)`, `taylor(sll, nbar)`.
*AC:* Chebyshev taper achieves the requested sidelobe level to ±0.5 dB; beamwidth broadens
monotonically with taper depth.

**T-6.5 · Spin-2 tensor superposition · 3 pts · `opus` · deps T-5.4, T-6.1, SPIKE-4.4** ⚠️ **critical path**
`src/gwtb/array/beamform.py` — `superpose_tt(elements, weights, field_point)`. Sum the
**TT-projected tensor** `h_ij` along the common observation direction. Formulation per ADR-0002.
*AC:* reduces to the scalar array factor for co-oriented elements to rtol 1e-9; **for
orthogonally-oriented elements, gain is strictly less than N²** — the polarization-mismatch
signature that distinguishes spin-2 from spin-1.

**T-6.6 · Polarization-mismatch loss · 3 pts · `opus` · deps T-6.5**
`src/gwtb/array/beamform.py` — `mismatch_loss(orientation_a, orientation_b, n_hat)`.
*AC:* zero loss for identical orientations; maximal at the spin-2 mismatch angle (45°, **not**
90°); period π.

**T-6.7 · Retarded-time field evaluation · 3 pts · `sonnet-low` · deps T-1.7**
`src/gwtb/propagate/retarded.py` — `field_at(sources, field_point, time)`. Retarded time per
**element**, not array center.
*AC:* a single source reproduces `strain_tt` exactly; retarded time uses per-element distance —
asserted by a test where array-center retardation would give a detectably different answer.

**T-6.8 · Propagation to 40 AU · 3 pts · `sonnet-low` · deps T-6.5, T-6.7**
`src/gwtb/propagate/retarded.py` — `propagate(array, field_points, times)`.
*AC:* amplitude scales as 1/r to rtol 1e-9 over `r ∈ [1e9, 6e12]` m; phase accumulation is FP64
throughout (asserted by dtype check).

**T-6.9 · Benchmark: array factor vs. arraytool · 2 pts · `sonnet-low` · deps T-6.1**
`tests/benchmarks/test_array_factor.py`.
*AC:* rtol 1e-9 across 5 geometries and 3 tapers.

---

## Sprint 7 — Visualization (21 pts)

**T-7.1 · Field slice extraction · 2 pts · `sonnet-low` · deps T-6.8**
`src/gwtb/viz/slices.py` — `extract_slice(field, plane, extent, resolution)`.
*AC:* correct shape; coordinates match the requested extent to rtol 1e-12.

**T-7.2 · 2D strain heatmap · 3 pts · `sonnet` · deps T-7.1**
`src/gwtb/viz/slices.py` — `plot_strain_slice(...) -> matplotlib.figure.Figure`. Diverging
colormap centered at zero; annotate the scaled-strain reference.
*AC:* figure renders headless (Agg); colorbar symmetric about zero.

**T-7.3 · Wavefront animation · 3 pts · `sonnet` · deps T-7.2**
`src/gwtb/viz/slices.py` — `animate_propagation(...)`.
*AC:* frame count matches the time array; writes an mp4/gif headless.

**T-7.4 · Beam pattern: polar · 2 pts · `sonnet` · deps T-6.3**
`src/gwtb/viz/patterns.py` — `plot_pattern_polar(...)` in dB with configurable floor.
*AC:* main lobe at the steered direction; sidelobe structure visible at −40 dB floor.

**T-7.5 · Beam pattern: 3D · 3 pts · `sonnet` · deps T-7.4**
`src/gwtb/viz/patterns.py` — `plot_pattern_3d(...)`.
*AC:* renders headless; peak direction matches `steering_phases` to 1e-3 rad.

**T-7.6 · Polarization visualization · 3 pts · `sonnet` · deps T-5.2**
`src/gwtb/viz/patterns.py` — `plot_polarization_ellipse(h_plus, h_cross)` showing the
characteristic spin-2 quadrupolar deformation of a test-particle ring.
*AC:* pure `h₊` produces a ring deforming along the axes; pure `h×` at 45° — the visual signature
that the field is spin-2.

**T-7.7 · 3D volumetric rendering · 3 pts · `sonnet` · deps T-7.1**
`src/gwtb/viz/volume.py` — `render_volume(field, ...)` using PyVista. Optional dependency;
degrade gracefully if absent.
*AC:* skips with a clear message when PyVista is not installed; renders offscreen otherwise.

**T-7.8 · ParaView/VTK export · 2 pts · `sonnet-low` · deps T-7.1**
`src/gwtb/viz/export_vtk.py` — `export_field(field, path)` writing `.vti`.
*AC:* output reloads via `pyvista.read` with matching shape and values to rtol 1e-12.

---

## Sprint 8 — Target coupling and deflection (23 pts)

**T-8.1 · Geodesic deviation · 3 pts · `sonnet-low` · deps T-6.8**
`src/gwtb/target/geodesic.py` — `deviation_acceleration(h_ddot, separation)`.
`d²ξ_i/dt² = ½ ḧ_ij^TT ξ_j`.
*Citation:* MTW §37.2 `[verify]`.
*AC:* transverse to propagation; **net acceleration of the center of mass is zero** — the
defining property, asserted directly.

**T-8.2 · Tidal strain on a body · 2 pts · `sonnet-low` · deps T-8.1**
`src/gwtb/target/coupling.py` — `tidal_strain(h_amplitude, body_radius)`.
*AC:* scales linearly with both arguments; dimensionless output.

**T-8.3 · Coupling channel 1: tidal · 2 pts · `sonnet-low` · deps T-8.2**
`src/gwtb/target/coupling.py` — `channel_tidal(...) -> CouplingResult`.
*AC:* returns strain, not force; a test asserts the result carries no net-force field.

**T-8.4 · Coupling channel 2: absorption thrust · 3 pts · `sonnet-low` · deps T-8.2**
`src/gwtb/target/coupling.py` — `channel_absorption(luminosity, cross_section, distance)`. Momentum flux × absorption
cross-section.
*AC:* for a 1 km asteroid at 40 AU the result is below 1e-30 N — **the smallness is the finding**,
asserted rather than hidden.

**T-8.5 · Coupling channel 3: near-zone gradient · 3 pts · `sonnet` · deps T-4.1**
`src/gwtb/target/coupling.py` — `channel_gravity_tractor(tractor_mass, separation, asteroid_mass)`.
*Citation:* Lu & Love, *Nature* 438:177 (2005) `[verify]`.
*AC:* reproduces the paper's worked example to rtol 1e-2. **Open question OQ-5.**

**T-8.6 · Coupling comparison · 2 pts · `sonnet-low` · deps T-8.3–T-8.5**
`src/gwtb/target/coupling.py` — `compare_channels(...) -> GapReport` reporting all three side by side.
*AC:* all three present; ordered by magnitude; never sums them (they are not additive
mechanisms).

**T-8.7 · Impulse to Δv · 2 pts · `sonnet-low` · deps T-8.6**
`src/gwtb/target/deflection.py` — `delta_v(force, duration, asteroid_mass)`.
*AC:* DART cross-check — 4.3e9 kg, ~1.16e7 N·s → 2.7 mm/s to rtol 1e-2.

**T-8.8 · Δv to miss distance · 3 pts · `sonnet` · deps T-8.7**
`src/gwtb/target/deflection.py` — `miss_distance(delta_v, lead_time, orbit)`.
*AC:* scales linearly with both `delta_v` and `lead_time` in the impulsive limit to rtol 1e-6.

**T-8.9 · Ledger v2: coupling and deflection rows · 3 pts · `sonnet-low` · deps T-2.6, T-8.6**
`src/gwtb/ledger/gap_report.py` — *AC:* rows for all three channels plus required-vs-achieved impulse, benchmarked against DART
(1.16e7 N·s) and a 1 km asteroid requirement (1.4e10 N·s).

---

## Sprint 9 — Prime-frequency synthesis and focusing (22 pts)

**T-9.1 · Prime generator · 2 pts · `sonnet-low` · deps T-1.1** ✅
`src/gwtb/kinematics/oscillators.py` — `first_n_primes(n) -> list[int]` (sieve).
*AC:* first 10 are `[2,3,5,7,11,13,17,19,23,29]`; `n=1000` completes in <1 s.

**T-9.2 · Prime frequency set with band scaling · 3 pts · `sonnet-low` · deps T-9.1** ✅
`src/gwtb/kinematics/oscillators.py` — `prime_frequencies(n, unit_hz=1.0) -> np.ndarray`. The band scale is a **free parameter**
(decision 2).
*AC:* `unit_hz=1e6` yields 2 MHz, 3 MHz, …; recurrence period equals the product of primes to
rtol 1e-12.

**T-9.3 · Recurrence period · 2 pts · `sonnet-low` · deps T-9.2** ✅
`src/gwtb/kinematics/oscillators.py` — `recurrence_period(frequencies) -> float`.
*AC:* first 10 primes at 1 Hz → 6.469693230e9 s (≈205 years) exactly.

**T-9.4 · Multi-frequency oscillator drive · 3 pts · `sonnet-low` · deps T-9.2, T-3.1** ✅
`src/gwtb/kinematics/oscillators.py` — `class PrimeOscillatorDrive(frequencies, amplitudes, phases)` implementing
`AccelerationProfile`.
*AC:* superposition of sinusoids; phase offsets applied correctly; `|a| ≤ a_max`.

**T-9.5 · Focal phase solution · 3 pts · `opus` · deps T-9.4**
`src/gwtb/array/focus.py` — `focal_phases(geometry, frequencies, focal_point, focal_time)`.
Phases such that all components coincide at one space-time point.
*AC:* residual phase error at the focus < 1e-9 rad for all elements and frequencies.

**T-9.6 · Spatiotemporal focusing · 3 pts · `opus` · deps T-9.5, T-6.5** ⚠️ **critical path**
`src/gwtb/array/focus.py` — `focused_field(array, drive, field_points, times)`.
*AC:* peak amplitude at the focus is `N·A` to rtol 1e-6; background is `~√N·A`; **peak-to-
background ratio scales as √N** — the mode-locking signature.

**T-9.7 · Focus propagation · 3 pts · `sonnet-low` · deps T-9.6**
`src/gwtb/array/focus.py` — `focus_trajectory(...)` — track the focal region over time.
*AC:* the focus **moves at c** and does not remain stationary — the non-dispersive consequence
that requirement 6's framing must confront, asserted rather than glossed.

**T-9.8 · Benchmark: mode-locking · 3 pts · `sonnet-low` · deps T-9.6**
`tests/benchmarks/test_focusing.py`.
*AC:* N·A peak and √N background to rtol 1e-3 for N ∈ {10, 100, 1000}.

---

## Sprint 10 — Focus metrics and band sweep (21 pts) → **GATE G3**

**T-10.1 · Focal spot size · 3 pts · `opus` · deps T-9.6**
`src/gwtb/array/focus.py` — `spot_size(array, wavelength, range_m)` (−3 dB transverse extent).
*AC:* recovers `w ≈ λr/D` to rtol 1e-2 across 5 aperture/frequency combinations.

**T-10.2 · Benchmark: diffraction limit · 3 pts · `sonnet-low` · deps T-10.1**
`tests/benchmarks/test_diffraction.py`.
*AC:* numerically recovered spot size matches `λr/D` to rtol 1e-2; a 1 km spot at 40 AU requires
`D/λ ≳ 6e9` **independent of frequency**, asserted across 4 decades of frequency.

**T-10.3 · Focal dwell time · 2 pts · `sonnet-low` · deps T-9.7**
`src/gwtb/array/focus.py` — `dwell_time(...)` — how long the focus persists at a point.
*AC:* scales inversely with drive bandwidth to rtol 1e-2.

**T-10.4 · Peak-to-sidelobe ratio · 2 pts · `sonnet-low` · deps T-9.6**
`src/gwtb/array/focus.py` — `peak_to_sidelobe(...)`.
*AC:* improves as √N; degrades with sparse geometries (links OQ-4).

**T-10.5 · Band sweep · 3 pts · `sonnet` · deps T-9.2, T-1.8**
`src/gwtb/array/focus.py` — `band_sweep(config, unit_range_hz)` sweeping the prime unit scale.
*AC:* radiated power scales as f⁶ to rtol 1e-6 across Hz → MHz; **the sweep spans ~10³⁶ in
power**, the dominant design lever.

**T-10.6 · Aperture/frequency trade surface · 3 pts · `sonnet` · deps T-10.1, T-10.5**
`src/gwtb/array/focus.py` — `trade_surface(...)` producing the required-aperture-vs-frequency curve.
*AC:* reproduces 1.8e18 m at 1 Hz and 1.8e12 m at 1 MHz to rtol 1e-2.

**T-10.7 · Trade-surface visualization · 2 pts · `sonnet-low` · deps T-10.6, T-7.4**
`src/gwtb/viz/patterns.py` — `plot_trade_surface(...)`.
*AC:* log-log axes; renders headless; annotates the 6e9 wavelength invariant.

**T-10.8 · Ledger v3: focusing rows · 3 pts · `sonnet-low` · deps T-2.6, T-10.2**
`src/gwtb/ledger/gap_report.py` — *AC:* rows for spot size, dwell time, PSL, and required aperture, each with achieved-vs-required.

---

## Sprint 11 — Compute backend and performance (21 pts)

**T-11.1 · Backend shim · 3 pts · `sonnet-low` · deps T-1.1**
`src/gwtb/core/backend.py` — `get_backend(name)` dispatching to numpy or numba; uniform array
API.
*AC:* identical results across backends to rtol 1e-12; unknown backend raises.

**T-11.2 · Numba field kernel · 3 pts · `sonnet-low` · deps T-11.1, T-6.8**
`src/gwtb/core/backend.py` — JIT-compiled retarded-field evaluation.
*AC:* matches the numpy path to rtol 1e-12; ≥10× faster on a 128³ grid.

**T-11.3 · Split-phase decomposition · 3 pts · `opus` · deps T-11.2** ⚠️
`src/gwtb/core/backend.py` — `split_phase(reference_geometry, element_offsets)` returning FP64
reference phase plus FP32-safe differential.
*AC:* recombined phase matches full FP64 to <1e-5 rad for D=10 km at 40 AU; a test asserts naive
FP32 **fails** the same check — documenting why the decomposition exists.

**T-11.4 · Optional GPU backend · 3 pts · `sonnet-low` · deps T-11.3**
`src/gwtb/core/backend.py` — CuPy/JAX backend using the split-phase scheme. Optional dependency; degrade gracefully.
*AC:* skips cleanly with no GPU; matches CPU to rtol 1e-5 when present.

**T-11.5 · Precision guard · 2 pts · `sonnet-low` · deps T-11.3**
`src/gwtb/core/backend.py` — Raise if FP32 is used for absolute phase outside an authorized split-phase kernel.
*AC:* raises on unauthorized float32 phase input; passes inside the marked kernel.

**T-11.6 · Performance benchmarks · 3 pts · `sonnet-low` · deps T-11.2**
`tests/benchmarks/test_performance.py` — timing across grid sizes.
*AC:* records timings; fails if a 128³ evaluation exceeds 60 s on CPU (the G2 watch threshold).

**T-11.7 · Memory-efficient chunking · 2 pts · `sonnet-low` · deps T-11.2**
`src/gwtb/core/backend.py` — Chunked evaluation for grids exceeding RAM.
*AC:* a 512³ grid completes within a 4 GB budget; results match unchunked to rtol 1e-12.

**T-11.8 · Run manifest · 2 pts · `sonnet-low` · deps T-2.6**
`src/gwtb/ledger/gap_report.py` — emit version, git SHA, full parameters, seeds.
*AC:* manifest round-trips through JSON; a fixed seed reproduces identical output.

---

## Sprint 12 — Integration and release (20 pts) → **GATE G4**

**T-12.1 · End-to-end scenario · 3 pts · `sonnet` · deps all**
`examples/deflection_scenario.py` — 1 km asteroid at 40 AU, N-element array, prime-band drive.
*AC:* runs to completion; emits field visualization, beam pattern, Δv, miss distance, gap report.

**T-12.2 · Benchmark: Hulse–Taylor · 3 pts · `sonnet` · deps T-1.8**
`tests/benchmarks/test_hulse_taylor.py` — PSR B1913+16 orbital decay.
*AC:* reproduces −2.4e-12 s/s to rtol 1e-2.

**T-12.3 · Benchmark: energy conservation · 3 pts · `sonnet-low` · deps T-6.8**
`tests/benchmarks/test_energy_conservation.py` — Radiated energy integrated over a distant sphere vs. the quadrupole luminosity integral.
*AC:* agreement to rtol 1e-4.

**T-12.4 · Property test suite · 2 pts · `sonnet-low` · deps all**
`tests/unit/test_properties.py` — dimensional consistency, TT idempotency, superposition
linearity across the public API.
*AC:* all public physics functions covered.

**T-12.5 · Complete PHYSICS.md · 3 pts · `opus` · deps all**
`docs/PHYSICS.md` — Replace every `[UNVERIFIED]` with a confirmed citation; add derivations for claims B-1…B-5.
*AC:* no `[UNVERIFIED]` markers remain; every Category B claim has a derivation and a reducing
limit.

**T-12.6 · Final index reconciliation · 2 pts · `sonnet-low` · deps all**
`docs/INDEX.md` — `indexer` pass: registry matches code, assumption ledger complete, validation status current.
*AC:* every implemented equation has a registry row; no row points at a missing function.

**T-12.7 · Contributor on-ramp · 2 pts · `sonnet` · deps T-12.5**
`docs/GETTING_STARTED.md` — from clone to first contribution.
*AC:* a reader with no prior context can run the E2E scenario.

**T-12.8 · v1.0 release · 2 pts · `sonnet-low` · deps T-12.1–T-12.7**
repo-level (tag, release notes, Zenodo). Tag, release notes, Zenodo DOI for citability.
*AC:* all 8 benchmarks pass; CI green; ledger publishes all four walls quantitatively.

---

## Summary

| Sprint | Focus | Points | Gate |
|---|---|---|---|
| 0 | Foundation & governance | 24 | — |
| 1 | Source physics, part 1 | 30 | — |
| 2 | Conservation, dipole flagging, ledger v0 | 26 | **G1** |
| 3 | Finite maneuver kinematics | 22 | — |
| 4 | Body parameterization | 23 | — |
| 5 | Spin-2 foundations, array geometry | 22 | — |
| 6 | Phased array and propagation | 24 | **G2** |
| 7 | Visualization | 21 | — |
| 8 | Target coupling and deflection | 23 | — |
| 9 | Prime synthesis and focusing | 22 | — |
| 10 | Focus metrics and band sweep | 21 | **G3** |
| 11 | Compute backend | 21 | — |
| 12 | Integration and release | 20 | **G4** |
| | **Total** | **299** | |

**115 tasks**, all ≤3 points, all with explicit file paths.

### Critical path

`T-1.1 → T-1.3 → T-1.4 → T-1.7 → T-2.1 → T-5.1 → T-6.1 → T-6.5 → T-6.8 → T-9.6 → T-10.1 →
T-12.1 → T-12.8`

Off-path branches with float: kinematics (Sprint 3), bodies (Sprint 4), visualization
(Sprint 7), backend (Sprint 11). These touch disjoint modules and are safe to parallelize —
roughly 3 sprints of compression is available if run as separate workstreams.

**Highest-risk node:** T-6.5 (spin-2 tensor superposition). No external reference
implementation exists, and a conceptual error there silently invalidates everything from G2
onward. `SPIKE-4.4` in Sprint 2 exists to surface that risk four sprints early.
