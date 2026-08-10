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

**T-2.2 · UNPHYSICAL stamping · 3 pts · `opus` · deps T-2.1** ✅
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

**T-2.4 · Dipole radiation term (flagged) · 3 pts · `sonnet-low` · deps T-2.2, T-2.3** ✅
`src/gwtb/source/multipole_rad.py` — `dipole_strain(d_ddot, r, n_hat) -> StampedResult`.
*AC:* always returns a stamped result; raises if called with a momentum-conserving source
unless `allow_trivial=True`.

**T-2.5 · Mass octupole moment · 3 pts · `sonnet-low` · deps T-1.3** ✅
`src/gwtb/bodies/multipole.py` — `octupole_moment(masses, positions) -> np.ndarray` (3,3,3).
*Citation:* `Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 123a, Newtonian
point-mass limit` — **derived**, category B (EQ-044). Verified at source 2026-08-03: eq. 123a
is Theorem 6's general *post-Newtonian* multipole, so the citation is scoped to its Newtonian
limit. Cross-checked against eq. 302a's leading term `I_ijk = −νm∆x⟨ijk⟩`.
*AC:* fully symmetric; traceless on all index pairs to atol 1e-12; reproduces eq. 302a's
Newtonian term across five mass ratios to rtol 1e-12.

> ⚠️ **Two corrections to this entry, 2026-08-03.** (1) Its *Citation* line previously read
> "eq. 2 applied to the quadrupole of eq. 3", which disagrees with the implementation's own
> `Source:` line (eq. 123a) — the backlog and the code cited different equations for the same
> function. (2) Its verification note ("Both patterns cross-checked … residuals fall as 1/N^2
> in orbital-phase sampling") was **pasted in from T-5.4's element-pattern task** and describes
> work that has nothing to do with the octupole. Recorded rather than silently overwritten.
>
> **Scope decision, 2026-08-03:** `octupole_moment` has no caller and none is planned. It is
> retained and marked speculative in its docstring; **no `l = 3` radiative path is to be built
> to justify it.** Establish the need first.

**T-2.6 · Ledger metric schema · 3 pts · `opus` · deps T-1.8** ✅ 🔒 **freeze**
`src/gwtb/ledger/gap_report.py` — `@dataclass GapMetric(name, achieved, required, units,
source_module)` and `class GapReport` with `add()`, `to_markdown()`, `to_json()`.
*AC:* schema round-trips through JSON; `to_markdown` renders a stable table.
*Why freeze:* the ledger reads outputs from every epic. Later epics write to this contract;
without a freeze the ledger chases interface changes all project long.

**T-2.7 · Ledger: emission-magnitude row · 2 pts · `sonnet-low` · deps T-2.6** ✅
`src/gwtb/ledger/gap_report.py` — `emission_gap(luminosity, target_impulse, duration)`.
*AC:* for a 10 t / 10 m / 1 kHz rod reports a gap within 0.5 decades of 1e-19 W.

**T-2.8 · Benchmark: spinning rod · 2 pts · `sonnet` · deps T-1.8** ✅
`tests/benchmarks/test_spinning_rod.py`. `P = (2/45)(G/c⁵) M² L⁴ ω⁶`.
*Citation:* `[verify]`.
*AC:* rtol 1e-6 against the analytic expression.

**T-2.10 · Convention enforcement tests · 2 pts · `sonnet-low` · deps T-1.7** ✅
`tests/unit/test_conventions.py`. Assert the ADR-0002 contracts against every public function
shipped so far: `(N,)`/`(N,3)` input shapes accepted and wrong shapes rejected; trailing tensor
indices; `n_hat` non-unit input raises `ValueError`; float32 input raises rather than upcasting;
returned arrays are float64.
*AC:* every public function in `bodies/`, `propagate/`, `source/` is covered by at least one
shape-rejection and one dtype-rejection assertion.
*Why here:* [ADR-0002](adr/0002-array-conventions.md) states these are enforced by this file, but
no Sprint 1 task created it — an ADR promising an artifact nothing delivered.

**T-2.9 · Branch protection (carried from T-0.9) · 1 pts · `sonnet-low` · deps T-13.2** ✅
**Closed 2026-08-10.** `gh api repos/sudo-install-gravity/tractor-beam-cathedral/branches/main/protection`
returns `required_status_checks` naming all three matrix jobs (`strict: true`),
`enforce_admins: true`, `allow_force_pushes: false`, `allow_deletions: false` — the AC,
confirmed by reading the live setting back, not just by the PUT succeeding. Applied by
the owner directly (repo-settings changes execute outside the harness's own permission
boundary); this session supplied the exact payload and verified the result.
`repo-level`. Require green CI on `main`; block force-push and deletion.
*AC:* `gh api repos/sudo-install-gravity/tractor-beam-cathedral/branches/main/protection` returns a
`required_status_checks` block listing `test (3.10)`, `test (3.11)`, `test (3.12)`.
*Blocked by:* ~~GitHub plan limits — private repos on the free tier cannot set branch
protection.~~ ✅ **Unblocked 2026-08-06: the repository is public.** Verified without
credentials — the API reports `private: false, visibility: public`, and an unauthenticated
`git ls-remote` returns HEAD. The `deps` field is now `none` so the scheduler can see it;
it previously read `repo made public`, which is prose the scheduler cannot evaluate and
which therefore excluded this task even after the condition was met (HANDOVER §5).

⚠️ **THE TASK IS NOT DONE, AND A LARGER FINDING BLOCKS IT.** `gh api
.../branches/main/protection` returns **404** — no protection is configured. But the AC
requires `required_status_checks` naming `test (3.10/3.11/3.12)`, and **those checks have
never reported**: `actions/runs` shows **`total_count: 0`. CI has never run, in the entire
history of this repository.**

`.github/workflows/ci.yml` is present on the remote (939 bytes), correct, and was added in
the very first commit — 63 commits ago. Job id `test`, `on: push: branches:[main]`, matrix
`["3.10","3.11","3.12"]`, which would produce exactly the check names this AC names. So the
workflow is not the defect. The cause could not be determined from here: reading
`actions/permissions` returns 403 for this token.

**Consequence, and it reaches the manuscript.** The paper's Methods states that "citation
discipline is enforced in continuous integration" and that a build "fails without it". The
*script* is real and does run — it is gate 4 of the five-gate local check, and has run on
every commit this session. **But it has never run in CI, so the enforcement claim is true
locally and false on the remote.** Fix the Actions configuration first, confirm a green run,
then set branch protection — in that order, because you cannot require a status check that
has never reported.

**SPIKE-4.4 · Two-element spin-2 superposition prototype · 3 pts · `opus` · deps T-1.7, T-1.6** ✅ ⚠️
Scratch prototype only. Superpose two quadrupole sources of differing orientation at a common
far-field point; compare polarization-mismatch behavior against hand-derived analytics.
*Deliverable:* [`docs/adr/0003-spin2-superposition.md`](adr/0003-spin2-superposition.md) ✅ written — the correct formulation, the
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

**T-3.7 · Linear memory · 3 pts · `opus` · deps T-1.7** ✅
`src/gwtb/source/memory.py` — `linear_memory(masses, velocities_initial, velocities_final, r,
n_hat)`. `Δh_ij^TT = (4G/c⁴r) Λ_ij,kl Δ[Σ_A M_A v^k v^l]`.
*Citation:* Braginsky & Thorne, *Nature* 327:123 (1987) `[verify]`.
*AC:* traceless/transverse; zero when velocities unchanged; scales as 1/r.
⚠️ **A validated target already exists.** The settled (post-maneuver) value of
`waveform_from_profile` reaches the linear memory by the independent quadrupole route, and the
two agree to **0.0 relative difference** — see [ADR-0004](adr/0004-maneuvering-body-model.md).
Add a benchmark asserting `linear_memory(...)` reproduces that settled value to machine
precision; it is a far stronger check than any standalone tolerance.

**T-3.8 · Waveform from a maneuver · 3 pts · `sonnet-low` · deps T-3.1, T-1.7** ✅
`src/gwtb/source/quadrupole.py` — `waveform_from_profile(body, profile, r, n_hat, times)`.
*AC:* strain returns to the memory offset (not zero) after the maneuver ends, to rtol 1e-6.

**T-3.9 · Benchmark: memory effect · 2 pts · `sonnet-low` · deps T-3.7** ✅
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

**T-4.3 · Love-number deformation model · 3 pts · `opus` · deps T-4.1** ✅
`src/gwtb/bodies/elastic.py` — `induced_quadrupole(sphere, acceleration, love_k2, rigidity)`.
*Citation:* `[verify]` — tidal Love number formalism.
*AC:* scales linearly with acceleration; → 0 as rigidity → ∞; **R and ρ now enter
independently** (asserted against T-4.2).

**T-4.4 · Material property library · 2 pts · `sonnet-low` · deps T-4.3** ✅
`src/gwtb/bodies/elastic.py` — `MATERIALS` dict with rigidity and density for steel, tungsten,
osmium, and a nominal degenerate-matter placeholder, each with a source.
*AC:* every entry has a citation comment; densities within 1% of published values.

**SPIKE-4.5 · Uniform-sphere `l = 2` form factor · 2 pts · `opus` · deps T-4.1** ✅ ⚠️
Scratch prototype only, no production code. Resolved which form factor is correct for the
mass quadrupole of a uniform-density body, after `researcher` returned **UNVERIFIED** and
found T-4.5's premise wrong.
*Output:* [ADR-0007](adr/0007-uniform-sphere-quadrupole-form-factor.md). **Answer:
`F₂(kR) = 1 − 5(kR)²/98`**, Category B (our derivation) — no citable numbered equation
exists, so it is instead verified by three independent numerical routes, the strongest
agreeing to **1.7e-12**. Prototype: `scratchpad/spike_4_5.py`.
⚠️ **Two traps, both recorded in ADR-0007.** (1) `sin(kR)/(kR)` (`1 − (kR)²/6`) is `l = 0`
**spin-1 antenna machinery** — rule 4's trap; `3j₁(kR)/(kR)` (`1 − (kR)²/10`) is the
*total-mass monopole*. Both → 1 as `R/λ → 0` and both satisfy the *original* AC, so only
the coefficient distinguishes them. (2) **The radial profile is load-bearing**: a
*surface* deformation gives `1 − (kR)²/14`, **40% larger**, so this correction must not
be applied to `elastic.py:induced_quadrupole` (T-4.3) or `sphere.py:oblateness_quadrupole`
(T-4.6) without re-deriving.

**T-4.5 · Finite-size retardation correction · 3 pts · `opus` · deps T-4.1, SPIKE-4.5** ✅ ⚠️
`src/gwtb/bodies/multipole.py` — `finite_size_correction(sphere, wavelength) -> float`,
the leading correction in `R/λ`.
*Citation:* `Source: docs/adr/0007-uniform-sphere-quadrupole-form-factor.md, eq. 3` —
this project's own derivation; **do not substitute an external equation number**, none
was found (ADR-0007 "Citation status").
*AC (recomputed 2026-08-02):* → 1 as `R/λ → 0`; departure from unity at `R/λ = 0.1` is
**0.020142049798** (i.e. 2.0142%) to rtol 1e-12; the 1% departure point is
`R/λ = 0.070460897`. Regression guards assert the result is *inconsistent* with
`1 − (kR)²/6`, `1 − (kR)²/10` and `1 − (kR)²/14`. **Open question OQ-3.**

> **The original AC said "departs from unity by >1% when `R/λ > 0.1`" and was written
> against the wrong form factor.** It is *satisfied* by the correct one but badly
> understated — the true departure there is 2.0142%, and ">1%" would also pass for a
> formula wrong by a factor of two. Superseded by the recomputed AC above; see ADR-0007
> "Recomputed acceptance criterion" for the full table.

*Validity floor:* `1 − 5(kR)²/98` is a leading-order truncation and goes **negative** at
`kR = √(98/5)`, i.e. `R/λ = 0.7046`. That is a wall, not a bug (rule 5). T-4.7 adds the
structured out-of-regime warning at `R/λ > 0.1`.

**T-4.6 · Rotational oblateness · 2 pts · `sonnet-low` · deps T-4.1** ✅
`src/gwtb/bodies/sphere.py` — `oblateness_quadrupole(sphere, spin_rate)`.
*AC:* zero at zero spin; scales as spin²; matches the Maclaurin spheroid limit to rtol 1e-3.

**T-4.7 · Assumption-ledger integration · 2 pts · `sonnet-low` · deps T-4.5** ✅
`src/gwtb/bodies/multipole.py` — `LongWavelengthAssumptionWarning`, raised by
`finite_size_correction` when `R/λ ≥ 0.1` (inclusive), naming the "Long wavelength
(R << lambda)" row of `docs/INDEX.md` §3 by name in the message text.
*AC:* warning raised exactly at the threshold (tested at `R/λ = 0.1` and one part in a
million below it, so a `>` vs `≥` off-by-one would be caught); message contains "Long
wavelength", "R << lambda", "INDEX.md" and "§3".

**T-4.8 · Sensitivity study · 3 pts · `sonnet` · deps T-4.3, T-4.5** ✅
`tests/benchmarks/test_body_sensitivity.py` — sweeps 5 radii spanning two orders of
magnitude at fixed `M = 1e15 kg` (density set at each point to hold `M` fixed). Rigid
model: `Sphere.self_quadrupole()`, identically zero for every `(R, ρ)` (T-4.2), plus the
point-mass trajectory quadrupole, which never reads `R` or `ρ` at all. Elastic model:
`induced_quadrupole` (T-4.3) at fixed material rigidity (steel/tungsten/osmium from
`MATERIALS`, T-4.4) and a fixed external tidal field.
*AC:* rigid variation < 1e-12 relative (measured: exactly 0, both by the absolute-zero
floor and by the trajectory-quadrupole ratio) — elastic variation > 1e-3 relative for
realistic rigidity (measured: ~7.6e4–1.0e5 across the three materials, i.e. eight orders
of magnitude above the threshold; pinned at >1e4 so a weakened `R⁵` dependence still
fails even though it would pass the AC's own looser bound).

**T-4.9 · Ledger: body-parameter row · 3 pts · `sonnet-low` · deps T-2.6, T-4.8** ✅
`src/gwtb/ledger/gap_report.py` — `body_quadrupole_gap(achieved_quadrupole,
required_quadrupole, source_module=...)`. A thin wrapper in `focusing_gap`'s style:
`name="body quadrupole"` and `units="kg m^2"` are fixed; both values are supplied by the
caller, since which body model (rigid/elastic/oblate/finite-size) produced `achieved` and
what scenario fixes `required` are call-site decisions, not the ledger's.
*AC:* row appears in `to_markdown()` with correct units — verified end-to-end using
T-4.8's own fixed-mass sphere fixture and its measured elastic-quadrupole magnitude.

---

## Sprint 5 — Spin-2 foundations and array geometry (22 pts)

**T-5.1 · Polarization basis · 3 pts · `opus` · deps T-1.6** ✅
`src/gwtb/propagate/polarization.py` — `polarization_basis(n_hat) -> (e_plus, e_cross)`.
*Citation:* `Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 2.22` ✅ verified
(component definition h^TT_xx = -h^TT_yy = h_plus, h^TT_xy = h_cross). The MTW reference was
dropped: its exact equation number could not be confirmed, per the standing open-access rule.
*AC:* both traceless and transverse; orthonormal under `e_A:e_B = 2δ_AB`; **rotating the basis
by ψ about `n_hat` transforms the amplitudes by e^(2iψ) — asserted directly, not assumed.**

**T-5.2 · Strain decomposition · 2 pts · `sonnet-low` · deps T-5.1** ✅
`src/gwtb/propagate/polarization.py` — `decompose(h_ij, n_hat) -> (h_plus, h_cross)` and
`recompose(h_plus, h_cross, n_hat)`.
*AC:* round-trip identity to rtol 1e-12 over 20 random TT tensors.

**T-5.3 · Spin-2 rotation operator · 3 pts · `sonnet-low` · deps T-5.1** ✅
`src/gwtb/propagate/polarization.py` — `rotate_polarization(h_plus, h_cross, psi)`.
*AC:* period is π, not 2π (the spin-2 signature); `rotate(·, π/4)` maps `h₊ → h×`.

**T-5.4 · Quadrupole element patterns · 3 pts · `opus` · deps T-5.1** ✅
`src/gwtb/propagate/polarization.py` — `element_pattern_rotating(theta)` returning
`h₊ ∝ (1+cos²θ)/2`, `h× ∝ cos θ`; `element_pattern_linear(theta)` returning `h₊ ∝ sin²θ`.
*Citation:* `Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 2` applied to the
quadrupole of eq. 3 ✅ — **derived**, category B. Both patterns cross-checked against the
already-validated `quadrupole_second_derivative` + `apply_tt` path; residuals fall as 1/N^2 in
orbital-phase sampling, confirming exactness. Maggiore dropped (unverifiable equation number).
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

**T-5.9 · Ledger v1: aperture row · 3 pts · `sonnet-low` · deps T-2.6, T-5.5** ✅
`src/gwtb/ledger/gap_report.py` — `aperture_gap(geometry, wavelength, range_m, spot_size)`
reporting achieved vs. required `D/λ ≳ r/w`.
*AC:* for a 1 km spot at 40 AU reports required `D/λ` within 0.5 decades of 6e9, **at any
frequency** — the frequency-independence is the assertion.

---

## Sprint 6 — Phased array and propagation (24 pts) → **GATE G2**

**T-6.1 · Scalar array factor · 3 pts · `sonnet` · deps T-5.5** ✅
`src/gwtb/array/beamform.py` — `array_factor(geometry, weights, wavelength, direction)`.
`AF = Σ_n w_n exp[i(k·r_n + φ_n)]`.
*Citation:* Balanis ch. 6 `[verify]`.
*AC:* uniform broadside array reproduces the analytic `sin(Nψ/2)/sin(ψ/2)` to rtol 1e-9;
**matches `arraytool` output to rtol 1e-9** — the known-good baseline before departing to spin-2.

**T-6.2 · Beam steering · 2 pts · `sonnet-low` · deps T-6.1** ✅
`src/gwtb/array/beamform.py` — `steering_phases(geometry, wavelength, target_direction) -> np.ndarray`.
*AC:* peak of the steered pattern lies within 1e-6 rad of the requested direction.

**T-6.3 · Beamwidth and sidelobes · 2 pts · `sonnet-low` · deps T-6.1** ✅
`src/gwtb/array/beamform.py` — `beamwidth_3db(...)`, `peak_sidelobe_level(...)`.
*AC:* uniform array reproduces `θ_3dB ≈ 0.886 λ/(Nd)` to rtol 1e-3 and −13.2 dB PSL to ±0.2 dB.

**T-6.4 · Amplitude tapering · 3 pts · `sonnet` · deps T-6.1** ✅
`src/gwtb/array/beamform.py` — `taper(n, kind)` for `uniform`, `hann`, `hamming`,
`chebyshev(sll)`, `taylor(sll, nbar)`.
*AC:* Chebyshev taper achieves the requested sidelobe level to ±0.5 dB; beamwidth broadens
monotonically with taper depth.

**T-6.5 · Spin-2 tensor superposition · 3 pts · `opus` · deps T-5.4, T-6.1, SPIKE-4.4** ✅ ⚠️ **critical path**
`src/gwtb/array/beamform.py` — `superpose_tt(elements, weights, field_point)`. Sum the
**TT-projected tensor** `h_ij` along the common observation direction. Formulation per [ADR-0003](adr/0003-spin2-superposition.md).
*AC:* reduces to the scalar array factor for co-oriented elements to rtol 1e-9; **for
orthogonally-oriented elements, gain is strictly less than N²** — the polarization-mismatch
signature that distinguishes spin-2 from spin-1.

**T-6.6 · Polarization-mismatch loss · 3 pts · `opus` · deps T-6.5** ✅
`src/gwtb/array/beamform.py` — `mismatch_loss(orientation_a, orientation_b, n_hat)`.
*AC:* zero loss for identical orientations; maximal at the spin-2 mismatch angle (45°, **not**
90°); period π.

**T-6.7 · Retarded-time field evaluation · 3 pts · `sonnet-low` · deps T-1.7** ✅
`src/gwtb/propagate/retarded.py` — `field_at(sources, field_point, time)`. Retarded time per
**element**, not array center.
*AC:* a single source reproduces `strain_tt` exactly; retarded time uses per-element distance —
asserted by a test where array-center retardation would give a detectably different answer.

**T-6.8 · Propagation to 40 AU · 3 pts · `sonnet-low` · deps T-6.5, T-6.7** ✅
`src/gwtb/propagate/retarded.py` — `propagate(array, field_points, times)`.
*AC:* amplitude scales as 1/r to rtol 1e-9 over `r ∈ [1e9, 6e12]` m; phase accumulation is FP64
throughout (asserted by dtype check).

**T-6.9 · Benchmark: array factor vs. arraytool · 2 pts · `sonnet-low` · deps T-6.1** ✅
`tests/benchmarks/test_array_factor.py`.
*AC:* rtol 1e-9 across 5 geometries and 3 tapers.

---

## Sprint 7 — Visualization (21 pts)

**T-7.1 · Field slice extraction · 2 pts · `sonnet-low` · deps T-6.8** ✅
`src/gwtb/viz/slices.py` — `extract_slice(field, plane, extent, resolution)`.
*AC:* correct shape; coordinates match the requested extent to rtol 1e-12.

**T-7.2 · 2D strain heatmap · 3 pts · `sonnet` · deps T-7.1** ✅
`src/gwtb/viz/slices.py` — `plot_strain_slice(...) -> matplotlib.figure.Figure`. Diverging
colormap centered at zero; annotate the scaled-strain reference.
*AC:* figure renders headless (Agg); colorbar symmetric about zero.

**T-7.3 · Wavefront animation · 3 pts · `sonnet` · deps T-7.2** ✅
`src/gwtb/viz/slices.py` — `animate_propagation(...)`.
*AC:* frame count matches the time array; writes an mp4/gif headless.

**T-7.4 · Beam pattern: polar · 2 pts · `sonnet` · deps T-6.3** ✅
`src/gwtb/viz/patterns.py` — `plot_pattern_polar(...)` in dB with configurable floor.
*AC:* main lobe at the steered direction; sidelobe structure visible at −40 dB floor.

**T-7.5 · Beam pattern: 3D · 3 pts · `sonnet` · deps T-7.4** ✅
`src/gwtb/viz/patterns.py` — `plot_pattern_3d(...)`.
*AC:* renders headless; peak direction matches `steering_phases` to 1e-3 rad.

**T-7.6 · Polarization visualization · 3 pts · `sonnet` · deps T-5.2** ✅
`src/gwtb/viz/patterns.py` — `plot_polarization_ellipse(h_plus, h_cross)` showing the
characteristic spin-2 quadrupolar deformation of a test-particle ring.
*AC:* pure `h₊` produces a ring deforming along the axes; pure `h×` at 45° — the visual signature
that the field is spin-2.

**T-7.7 · 3D volumetric rendering · 3 pts · `sonnet` · deps T-7.1** ✅
`src/gwtb/viz/volume.py` — `render_volume(field, ...)` using PyVista. Optional dependency;
degrade gracefully if absent.
*AC:* skips with a clear message when PyVista is not installed; renders offscreen otherwise.

**T-7.8 · ParaView/VTK export · 2 pts · `sonnet-low` · deps T-7.1** ✅
`src/gwtb/viz/export_vtk.py` — `export_field(field, path)` writing `.vti`.
*AC:* output reloads via `pyvista.read` with matching shape and values to rtol 1e-12.

---

## Sprint 8 — Target coupling and deflection (23 pts)

**T-8.1 · Geodesic deviation · 3 pts · `sonnet-low` · deps T-6.8** ✅
`src/gwtb/target/geodesic.py` — `deviation_acceleration(h_ddot, separation)`.
`d²ξ_i/dt² = ½ ḧ_ij^TT ξ_j`.
*Citation:* MTW §37.2 `[verify]`.
*AC:* transverse to propagation; **net acceleration of the center of mass is zero** — the
defining property, asserted directly.

**T-8.2 · Tidal strain on a body · 2 pts · `sonnet-low` · deps T-8.1** ✅
`src/gwtb/target/coupling.py` — `tidal_strain(h_amplitude, body_radius)`.
*AC:* scales linearly with both arguments; dimensionless output.

**T-8.3 · Coupling channel 1: tidal · 2 pts · `sonnet-low` · deps T-8.2** ✅
`src/gwtb/target/coupling.py` — `channel_tidal(...) -> CouplingResult`.
*AC:* returns strain, not force; a test asserts the result carries no net-force field.

**T-8.4 · Coupling channel 2: absorption thrust · 3 pts · `sonnet-low` · deps T-8.2** ✅
`src/gwtb/target/coupling.py` — `channel_absorption(luminosity, cross_section, distance)`. Momentum flux × absorption
cross-section.
*AC:* for a 1 km asteroid at 40 AU the result is below 1e-30 N — **the smallness is the finding**,
asserted rather than hidden.

**T-8.5 · Coupling channel 3: near-zone gradient · 3 pts · `sonnet` · deps T-4.1** ✅
`src/gwtb/target/coupling.py` — `channel_gravity_tractor(tractor_mass, separation, asteroid_mass)`.
*Citation:* Lu & Love, *Nature* 438:177 (2005) `[verify]`.
*AC:* reproduces the paper's worked example to rtol 1e-2. **Open question OQ-5.**

**T-8.6 · Coupling comparison · 2 pts · `sonnet-low` · deps T-8.3–T-8.5** ✅
`src/gwtb/target/coupling.py` — `compare_channels(...) -> GapReport` reporting all three side by side.
*AC:* all three present; ordered by magnitude; never sums them (they are not additive
mechanisms).

**T-8.7 · Impulse to Δv · 2 pts · `sonnet-low` · deps T-8.6** ✅
`src/gwtb/target/deflection.py` — `delta_v(force, duration, asteroid_mass)`.
*AC:* DART cross-check — 4.3e9 kg, ~1.16e7 N·s → 2.7 mm/s to rtol 1e-2.

**T-8.8 · Δv to miss distance · 3 pts · `sonnet` · deps T-8.7** ✅
`src/gwtb/target/deflection.py` — `miss_distance(delta_v, lead_time, orbit)`.
*AC:* scales linearly with both `delta_v` and `lead_time` in the impulsive limit to rtol 1e-6.

**T-8.9 · Ledger v2: coupling and deflection rows · 3 pts · `sonnet-low` · deps T-2.6, T-8.6** ✅
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

**T-9.5 · Focal phase solution · 3 pts · `opus` · deps T-9.4** ✅
`src/gwtb/array/focus.py` — `focal_phases(geometry, frequencies, focal_point, focal_time)`.
Phases such that all components coincide at one space-time point.
*AC:* residual phase error at the focus < 1e-9 rad for all elements and frequencies.

**SPIKE-9.6 · `focused_field` superposition regime · 2 pts · `opus` · deps T-9.5, T-6.5** ✅ ⚠️
Scratch prototype only, no production code. Resolved whether `focused_field` can build on
`superpose_tt` given ADR-0003's common-`n̂` premise and its Fraunhofer guard.
*Output:* [ADR-0006](adr/0006-focused-field-far-field-regime.md). **Answer: yes** — the angular
spread at 40 AU is 1.03e-9 rad against ADR-0003's 5.0e-2 rad budget, a 2.4e7× margin, so the
reversal condition is not triggered. Near-field focusing stays out of scope.

**T-9.6 · Spatiotemporal focusing · 3 pts · `opus` · deps SPIKE-9.6, T-9.5, T-6.5** ✅ ⚠️ **critical path**
`src/gwtb/array/focus.py` — `focused_field(array, drive, field_points, times)`.
Weights are `exp(+i · focal_phases(...))`, superposed by `superpose_tt`; **no new projection
logic**. Propagate `superpose_tt`'s Fraunhofer `ValueError` rather than catching it — a
near-field request is out of scope and must fail loudly.
*AC:* peak amplitude at the focus is `N·A` to rtol 1e-6 **at broadside**; **peak-to-background
ratio scales as √N** — the mode-locking signature.
⚠️ **Four measured traps; every one of them yields a passing but meaningless test.** Full detail
in [ADR-0006](adr/0006-focused-field-far-field-regime.md) §"Four traps":
1. **Test at `f ≥ 1e5 Hz`, and assert `D/λ > 1` in the test.** At the nominal 1 kHz the 12.4 km
   reference aperture spans **0.041 λ** — a point source, no beam. Every weighting, including
   `w = 1`, returns exactly `N`, so the AC passes with the focusing logic deleted.
2. **Pin the sign convention ≥ 50 beamwidths off-axis.** At 5 beamwidths `exp(+iφ)` and
   `exp(−iφ)` differ by 0.08% and both pass; at 50 they give 44.97 vs 5.68. Assert the wrong
   sign fails.
3. **`N·A` holds at broadside only.** At 50 beamwidths the correctly-steered peak is 44.97, not
   64 — the element pattern falls off. Do not tighten the tolerance to force agreement.
4. **Background mean is `√(Nπ)/2 ≈ 0.886√N`, not `√N`** (7.09 vs 8.00 at N=64). The *ratio* is
   what scales as √N.

**T-9.7 · Focus propagation · 3 pts · `sonnet-low` · deps T-9.6** ✅
`src/gwtb/array/focus.py` — `focus_trajectory(...)` — track the focal region over time.
*AC:* the focus **moves at c** and does not remain stationary — the non-dispersive consequence
that requirement 6's framing must confront, asserted rather than glossed.

**T-9.8 · Benchmark: mode-locking · 3 pts · `sonnet-low` · deps T-9.6** ✅
`tests/benchmarks/test_focusing.py`.
*AC:* N·A peak and √N background to rtol 1e-3 for N ∈ {10, 100, 1000}.

---

## Sprint 10 — Focus metrics and band sweep (21 pts) → **GATE G3**

**T-10.1 · Focal spot size · 3 pts · `opus` · deps T-9.6** ✅
`src/gwtb/array/focus.py` — `spot_size(array, wavelength, range_m)` (−3 dB transverse extent).
*AC:* recovers `w ≈ λr/D` to rtol 1e-2 across 5 aperture/frequency combinations.
*Coefficient:* `w = 1.0290 λr/D`, from the root `x = 1.6163399` of `2J₁(x)/x = 1/√2`
(`FWHM_COEFFICIENT`). **Not 1.22** — that is the Rayleigh first null, a 19% overstatement.
Cited by its reproducible root rather than a textbook page; `test_spot_size.py` re-solves it
with `scipy` *and* measures it from a simulated filled circular aperture.
⚠️ The coefficient assumes a **uniformly-illuminated circular** aperture; a square aperture's
FWHM is `0.886 λ/D`, 14% narrower — outside the AC's own rtol.

**T-10.2 · Benchmark: diffraction limit · 3 pts · `sonnet-low` · deps T-10.1** ✅
`tests/benchmarks/test_diffraction.py`.
*AC:* numerically recovered spot size matches `λr/D` to rtol 1e-2; a 1 km spot at 40 AU requires
`D/λ ≳ 6e9` **independent of frequency**, asserted across 4 decades of frequency.

**T-10.3 · Focal dwell time · 2 pts · `sonnet-low` · deps T-9.7** ✅
`src/gwtb/array/focus.py` — `dwell_time(...)` — how long the focus persists at a point.
*AC:* scales inversely with drive bandwidth to rtol 1e-2.

**T-10.4 · Peak-to-sidelobe ratio · 2 pts · `sonnet-low` · deps T-9.6** ✅
`src/gwtb/array/focus.py` — `peak_to_sidelobe(...)`.
*AC:* improves as √N; degrades with sparse geometries (links OQ-4).

**T-10.5 · Band sweep · 3 pts · `sonnet` · deps T-9.2, T-1.8** ✅
`src/gwtb/array/focus.py` — `band_sweep(config, unit_range_hz)` sweeping the prime unit scale.
*AC:* radiated power scales as f⁶ to rtol 1e-6 across Hz → MHz; **the sweep spans ~10³⁶ in
power**, the dominant design lever.

**T-10.6 · Aperture/frequency trade surface · 3 pts · `sonnet` · deps T-10.1, T-10.5** ✅
`src/gwtb/array/focus.py` — `trade_surface(...)` producing the required-aperture-vs-frequency curve.
*AC:* reproduces 1.8e18 m at 1 Hz and 1.8e12 m at 1 MHz to rtol 1e-2.

**T-10.7 · Trade-surface visualization · 2 pts · `sonnet-low` · deps T-10.6, T-7.4** ✅
`src/gwtb/viz/patterns.py` — `plot_trade_surface(...)`.
*AC:* log-log axes; renders headless; annotates the 6e9 wavelength invariant.

**T-10.8 · Ledger v3: focusing rows · 3 pts · `sonnet-low` · deps T-2.6, T-10.2** ✅
`src/gwtb/ledger/gap_report.py` — *AC:* rows for spot size, dwell time, PSL, and required aperture, each with achieved-vs-required.

---

## Sprint 11 — Compute backend and performance (21 pts)

**T-11.1 · Backend shim · 3 pts · `sonnet-low` · deps T-1.1** ✅
`src/gwtb/core/backend.py` — `get_backend(name)` dispatching to numpy or numba; uniform array
API.
*AC:* identical results across backends to rtol 1e-12; unknown backend raises.

**T-11.2 · Numba field kernel · 3 pts · `sonnet-low` · deps T-11.1, T-6.8** ✅
`src/gwtb/core/backend.py` — JIT-compiled retarded-field evaluation.
*AC:* matches the numpy path to rtol 1e-12; ≥10× faster on a 128³ grid.

**T-11.3 · Split-phase decomposition · 3 pts · `opus` · deps T-11.2** ✅ ⚠️
`src/gwtb/core/backend.py` — `split_phase(reference_geometry, element_offsets)` returning FP64
reference phase plus FP32-safe differential.
*AC:* recombined phase matches full FP64 to <1e-5 rad for D=10 km at 40 AU; a test asserts naive
FP32 **fails** the same check — documenting why the decomposition exists.

**T-11.4 · Optional GPU backend · 3 pts · `sonnet-low` · deps T-11.3** ✅
`src/gwtb/core/backend.py` — CuPy/JAX backend using the split-phase scheme. Optional dependency; degrade gracefully.
*AC:* skips cleanly with no GPU; matches CPU to rtol 1e-5 when present.

**T-11.5 · Precision guard · 2 pts · `sonnet-low` · deps T-11.3** ✅
`src/gwtb/core/backend.py` — Raise if FP32 is used for absolute phase outside an authorized split-phase kernel.
*AC:* raises on unauthorized float32 phase input; passes inside the marked kernel.

**T-11.6 · Performance benchmarks · 3 pts · `sonnet-low` · deps T-11.2** ✅
`tests/benchmarks/test_performance.py` — timing across grid sizes.
*AC:* records timings; fails if a 128³ evaluation exceeds 60 s on CPU (the G2 watch threshold).

**T-11.7 · Memory-efficient chunking · 2 pts · `sonnet-low` · deps T-11.2** ✅
`src/gwtb/core/backend.py` — Chunked evaluation for grids exceeding RAM.
*AC:* a 512³ grid completes within a 4 GB budget; results match unchunked to rtol 1e-12.

**T-11.8 · Run manifest · 2 pts · `sonnet-low` · deps T-2.6** ✅
`src/gwtb/ledger/gap_report.py` — emit version, git SHA, full parameters, seeds.
*AC:* manifest round-trips through JSON; a fixed seed reproduces identical output.

---

## Sprint 12 — Integration and release (20 pts) → **GATE G4**

**T-12.1 · End-to-end scenario · 3 pts · `sonnet` · deps all** ✅
`examples/deflection_scenario.py` — 1 km asteroid at 40 AU, N-element array, prime-band drive.
*AC:* runs to completion; emits field visualization, beam pattern, Δv, miss distance, gap report.
**Closed 2026-08-10.** Two findings caught and fixed while building it, both worth recording:
(1) ``superpose_tt`` returns its sum in the units of ``QuadrupoleElement.quadrupole``
(kg m² s⁻²), **not** strain — feeding that raw into a "strain" plot label would have been
exactly the physically-mislabeled-output failure mode this project exists to avoid. Fixed
by applying the ``2·G/(c⁴r)`` prefactor explicitly, per point for the field slice (``r``
varies across it). (2) a naively-chosen slice extent (1000 m) produced a flat, structureless
blob at the chosen distance — sized from the beam's own diffraction scale
(``wavelength · distance / aperture``) instead, which shows real lobe structure. `examples/`
added to `tools/gates.py` and `.github/workflows/ci.yml`'s ruff/mypy coverage, since neither
checked it before this task and a file outside the checked paths is a file nothing verifies.

**T-12.2 · Benchmark: Hulse–Taylor · 3 pts · `sonnet` · deps T-1.8** ✅
`tests/benchmarks/test_hulse_taylor.py` — PSR B1913+16 orbital decay.
*AC:* reproduces −2.4e-12 s/s to rtol 1e-2.

*Citation resolved 2026-08-02.* Three prior `researcher` passes could not reach a
fetchable primary source for Peters (1964) itself: the Caltech-hosted PDF
permanently refuses the connection from this environment (`ECONNREFUSED`,
confirmed twice, stop retrying it), and Blanchet arXiv:1310.1528 — though
reachable — turns out **not to contain the eccentric-orbit decay formula at all**;
it focuses on quasi-circular inspiral. A fourth pass found a citable substitute
instead of the original: **Kowalska, Bulik, Belczyński, Dominik & Gondek-Rósińska,
"The eccentricity distribution of compact binaries," A&A 527:A70 (2011),
arXiv:1010.0511**, an open-access, peer-reviewed source whose eq. (1) gives
⟨da/dt⟩ and eq. (3) gives ⟨de/dt⟩, confirmed algebraically to match the
73/24, 37/96, 121/304-coefficient form term-for-term (their `-(19/12)β` prefactor
reduces to exactly `-304/15`, the stated `de/dt` coefficient). They attribute the
result to Peters & Mathews (1963) and Peters (1964), Phys. Rev. 136, B1224 — that
original paper's own equation numbers remain unverified (paywalled, no open
mirror), so **cite Kowalska et al., not "Peters 1964 eq. 5.6/5.7."**
PSR B1913+16 system parameters (masses, period, eccentricity, observed Ṗ_b) are
separately verified via arXiv:1606.04581 (Weisberg & Huang 2016).

**T-12.3 · Benchmark: energy conservation · 3 pts · `sonnet-low` · deps T-6.8** ✅
`tests/benchmarks/test_energy_conservation.py` — Radiated energy integrated over a distant sphere vs. the quadrupole luminosity integral.
*AC:* agreement to rtol 1e-4.

**T-12.4 · Property test suite · 2 pts · `sonnet-low` · deps all** ✅
`tests/unit/test_properties.py` — dimensional consistency, TT idempotency, superposition
linearity across the public API.
*AC:* all public physics functions covered.
**Closed 2026-08-10.** 111 property tests (5 random seeds each) across 12 public functions
spanning `source/`, `propagate/`, `bodies/`, `target/` — the citation-CI physics packages,
same set `tools/check_citations.py` enforces. "Covered" interpreted as: each function
exercised by whichever of the three named properties actually applies to it (idempotency
is meaningless for `delta_v`; superposition linearity is meaningless for a single-body
function like `tidal_strain` — forcing an inapplicable property would be a fabricated
test). The coverage claim itself is a checkable artifact (`_COVERED` set plus a test that
every entry is still importable), not just asserted in a docstring.

**T-12.5 · Complete PHYSICS.md · 3 pts · `opus` · deps all** ✅
`docs/PHYSICS.md` — Replace every `[UNVERIFIED]` with a confirmed citation; add derivations for claims B-1…B-5.
*AC:* no `[UNVERIFIED]` markers remain; every Category B claim has a derivation and a reducing
limit.
**Closed 2026-08-10.** All three `[UNVERIFIED]` markers were **documentation lag, not open
research** — each citation had already been verified elsewhere in the project and PHYSICS.md
never got the update (memory → Favata eq. 10k, 2026-07-31; geodesic deviation → [FH] eq. 3.11,
2026-08-03; array relations → Orfanidis ch. 19 eqs. 19.4.1/19.9.6/19.7.6, Sprint 6). All three
had been sitting behind **chapter references**, so A-6 and A-8 in `CLAIMS.md` were corrected too
— the last two Category A equation rows to carry one. The AC's "every Category B claim" was read
literally and taken to **B-1…B-9**, not the task line's B-1…B-5: B-7/B-8/B-9 postdate this task's
wording, and a ledger that skipped them would not satisfy the AC as written. New §10 indexes all
nine against their reducing limits. **B-5 was the one genuinely open claim** and is now derived:
both coupling channels fall as `1/d²` so distance cancels exactly, and the surviving ratio is
`(v/c)⁶`-suppressed; R6's measured 1.3143e-31 decomposes to 3.3e-16 into mechanism × geometry,
showing most of its 31 decades is the geometry of the comparison rather than the mechanism.
**Two claim cells were stale, not blocked** (B-3 named T-10.1/10.2 outstanding, B-4 named T-9.8;
all three had landed). **`code-reviewer` found one Major and it was real:** B-8's "Reduces to"
named A-6, the geodesic-deviation claim, which has nothing to do with gravitational focusing of a
hyperbolic impactor — corrected, and the underlying gap recorded rather than re-papered (B-8
reduces to elementary mechanics, which is **not** a Category A row; B-9 inherits this). The
review also challenged ADR-0006's Fresnel-phase figure as 2% off; **checked, and the ADR is right
— the code's output is the unreliable one**: the sag is 300× below one float64 ULP at 40 AU, so
`focal_phases`' value there is quantization noise. Recorded in §8.1 as a finding, which makes
"focusing is numerically degenerate with steering" literal. Every number was recomputed against
the code before being written; `tools/gates.py` green (1193 passed, 3 skipped).

**T-12.6 · Final index reconciliation · 2 pts · `sonnet-low` · deps all** ✅
`docs/INDEX.md` — `indexer` pass: registry matches code, assumption ledger complete, validation status current.
*AC:* every implemented equation has a registry row; no row points at a missing function.
**Closed 2026-08-10.** Full-codebase sweep of §1–§4, not incremental: every citation-carrying
public function in `source/`, `propagate/`, `bodies/`, `target/` confirmed against a registry
row by grepping current `^def`/`^class` lines (not the row's own prose); §1/§2 had no drift.
§4 had a real gap — T-12.1 and T-12.4 (both landed 2026-08-10) had no validation-status row,
added. One pre-existing cosmetic inconsistency flagged rather than silently rewritten (a
2026-08-08 header paragraph describing only the planning commit, not the same-day
implementation commit — §1's own body text already has it right). Independently re-verified:
`tools/gates.py` green (1193 passed, 3 skipped), matching the pass's own reported figures.

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

## Sprint 13 — CI enablement and the enforcement claim (9 pts)

**Why this sprint exists.** The manuscript's Methods states that citation discipline is
"enforced in continuous integration" and that the build fails without it. Verified
2026-08-06: **`actions/runs` reports `total_count: 0` for the entire history of this
repository.** The five gates are real and have run on every commit — *locally*. They have
never run on the remote. Until they do, the enforcement claim is true of a script and false
of a pipeline, and the paper cannot carry it as written.

**Diagnostic ground already covered**, so SPIKE-13.1 does not re-derive it:

| Hypothesis | Status | Evidence |
|---|---|---|
| Workflow file missing from the remote | **eliminated** | present, 939 bytes, sha `820b299` |
| Workflow file malformed / unregistered | **eliminated** | GitHub lists it: id `325748978`, `state: active` |
| Wrong path or wrong trigger | **eliminated** | `.github/workflows/ci.yml`; `on: push: branches:[main]`; 64 pushes to `main` |
| Repository is a fork (Actions off by default) | **eliminated** | `fork: false` |
| Repository archived or disabled | **eliminated** | `archived: false`, `disabled: false` |
| Job names cannot satisfy T-2.9's AC | **eliminated** | job id `test`, matrix `["3.10","3.11","3.12"]` → `test (3.10)` etc., exactly as required |
| **Actions disabled in repository or account settings** | **NOT TESTED — the leading hypothesis** | `actions/permissions` returns **403**: it requires repo admin, and the `gh` CLI is signed in as `Thanatos7777`, which has `push: false` — read-only — on this repository |

> **`git push` is not affected and needs no change.** The two authenticate separately:
> Git Credential Manager holds the push credential and it is already correct — GitHub reports
> `committer_login: sudo-install-gravity` and attributes every commit to that account. Only
> the **`gh` CLI** is on the wrong identity. Signing `gh` in as the owner would let
> `actions/permissions` be read directly and may close SPIKE-13.1 without a settings hunt;
> it is not otherwise required for the project to function.

**SPIKE-13.1 · Why has CI never run? · 2 pts · `opus` · deps none** ✅ **resolved 2026-08-10 — see ADR-0008 "Resolution"**
`docs/adr/0008-ci-never-ran.md`. Cannot be delegated to an agent: every remaining hypothesis
needs **repository-admin access**, which no available token has.
*Procedure, in order — stop at the first that explains it:*
1. **Settings → Actions → General.** If "Allow all actions and reusable workflows" is not
   selected, or Actions are disabled for this repository, that is the answer.
2. **Account settings → Actions.** A user-level policy disables Actions across all repos.
3. **Actions tab.** A banner such as "Workflows aren't being run on this forked repository"
   or a disabled-due-to-inactivity notice names the cause directly.
4. **Billing → Plan.** Exhausted minutes produce *failed* runs, not zero, so this would be a
   surprise — check last.
*AC:* ADR-0008 records which hypothesis held, the evidence, and the setting changed. If none
of the four explains it, the ADR says so and the spike escalates rather than guessing —
**a plausible cause recorded without evidence is worse than an open question** (rule 1's
reasoning, applied to infrastructure).

**Owner checked all four, 2026-08-09 — none held.** (1) "Allow all actions" is already
selected. (2) `github.com/settings/actions` 404s — that page doesn't exist for personal
accounts (only orgs have an account-wide Actions policy), so the hypothesis is inapplicable
rather than tested-and-clear. (3) No banner; adjacent finding: **Workflow permissions** is
"read"-only, not "read and write" — but that governs the `GITHUB_TOKEN`'s scope **inside**
an already-running job, not whether a run triggers, so it cannot produce `total_count: 0`
and is ruled out for *this* symptom (worth flipping to read+write anyway, separately).
(4) Free tier, but the repo is public — unlimited minutes, not the constrained allowance.
**Live test performed the same session, not just settings review:** commit `30efb77` was
pushed to `main` via the normal path and confirmed on GitHub (`GET .../commits/main`
returns that exact SHA); the workflow is `state: active` with the expected unrestricted
`on: push: branches: [main]` trigger, fetched from GitHub's own Contents API, not local
disk; the repo is healthy (`default_branch: "main"`, not a fork, not archived/disabled,
public). `GET .../actions/runs` **immediately after** still returned `total_count: 0`.
**Escalated to GitHub Support per the AC's own instruction** — full evidence trail in
ADR-0008. T-13.2 now depends on a support ticket, not on repository configuration.

**Resolved 2026-08-10, the day after escalation — it was a UI-only "Enable GitHub Actions
in this repository" button** the settings reviews never surfaced, clicked by the owner
while preparing the support ticket. The next push triggered the repository's first-ever
run within seconds; no configuration changed. The API had been misreporting
`enabled: true` the whole time — ADR-0008 "Resolution" records both the fix and the
GitHub-side API/backend disagreement worth reporting upstream.

**T-13.2 · Confirm a green CI run on `main` · 1 pts · `sonnet-low` · deps SPIKE-13.1** ✅
**Closed 2026-08-10: run 31350735475 on `91fe97c` — `conclusion: success`, all three
jobs green (`test (3.10)`, `test (3.11)`, `test (3.12)`), exactly the AC below.**
**Unblocked 2026-08-10** (SPIKE-13.1 resolved). First-ever run (31350375335, on
`af6036b`): `test (3.11)` and `test (3.12)` **fully green on clean Ubuntu** — lint,
format, citations, and all 1082 tests — and `test (3.10)` failed only at the mypy step,
on six numpy-stub-generation typing divergences (Python 3.10 resolves an older numpy at
install time than 3.11/3.12, and dtype inference differs between those stub
generations). All six call sites made explicitly float64-typed — the fix the project's
own FP64-everywhere rule would ask for anyway — rather than weakening or version-pinning
the CI mypy gate.
`repo-level`. Push any commit to `main` and observe the result.
*AC:* `gh api repos/sudo-install-gravity/tractor-beam-cathedral/actions/runs --jq .total_count`
returns **≥ 1**; the newest run has `conclusion == "success"` and **three** completed jobs
named `test (3.10)`, `test (3.11)`, `test (3.12)`.
*Trap:* a run that is merely *present* is not enough. It must be **green**, because CI runs
`ruff`, `mypy`, `check_citations.py` and `pytest` on a clean Ubuntu box with no `.venv` — and
3 tests skip locally for absent CuPy/PyVista, which may behave differently there. **Expect
the first remote run to fail, and treat that as the point of the exercise.**

**T-13.3 · Make the enforcement claim true in the manuscript · 1 pts · `sonnet-low` · deps T-13.2** ✅
`docs/paper/nature-draft.md` Methods, "Citation CI"; `README.md` Status.
*AC:* the ⚠️ caveat added 2026-08-06 ("it has run locally, not in GitHub Actions") is removed
**only after** T-13.2 is green, and replaced with the run URL. Removing it before then
restores a false claim — this task's whole content is *not* doing it early.

**T-13.4 · `tools/check_ci_status.py` · 2 pts · `sonnet-low` · deps T-13.2** ✅
**Verified against live state 2026-08-10**: correctly reported `status='in_progress'`
while run 31351420162 was running, then `OK` with the run URL once it completed
successfully for the exact commit checked out. Found and fixed one bug during
testing: `gh api -f key=value` submits as a POST body and 404s against this GET-only
endpoint — query params go directly in the URL string instead (documented in
`HANDOVER.md` §8).
`tools/check_ci_status.py` — `main() -> int`. Queries `actions/runs` for `main` and reports
the newest run's conclusion and age.
*AC:* exit 0 only when the newest `main` run is `success`; exit 1 with a named reason for
`total_count == 0` ("CI has never run"), a non-success conclusion, or a run older than the
current `HEAD`. Deliberately **not** a pytest test and **not** a sixth gate: it needs network
and credentials, and a gate that cannot run offline would break the local five. Documented in
`HANDOVER.md` §8 as an on-demand check.
*Rationale:* zero runs went unnoticed for 64 commits because nothing looked. This is the same
"derive, don't assert" fix applied to the pipeline (cf. `test_architecture.py`).

**T-13.5 · De-flake the two wall-clock assertions · 2 pts · `sonnet-low` · deps none** ✅
`tests/unit/test_backend.py` — **both** timing-sensitive tests, not just the first:
`test_field_grid_numba_10x_faster_on_128_cubed_grid` (line 140) and
`test_a_512_cubed_grid_completes_within_a_4gb_budget` (line 278).
Measured 2026-08-06: the suite failed **2 tests** on one contended run and then passed
**5 consecutive full runs** (956 passed each). The pair are the only wall-clock assertions in
the suite, and they fail together under load — which is the signature of contention rather
than regression.
*AC:* the test no longer fails under load. Take **best-of-3 wall-clock** rather than a single
timing, keeping the 10× threshold; do **not** lower the threshold — that would weaken a real
performance claim to fix a measurement problem, which is the inverse of HANDOVER §5's "fix
the measurement, never the tolerance".
*Trap:* this assertion will be *more* fragile on CI runners than locally — shared vCPUs,
noisy neighbours. If it proves unfixable there, mark it `@pytest.mark.skipif` on CI with the
reason recorded, rather than deleting a performance guard.

⚠️ **Found 2026-08-08: this task's own premise was half wrong, and the AC as literally
stated could not be fully satisfied.** `test_a_512_cubed_grid_completes_within_a_4gb_budget`
contains **no wall-clock or memory measurement at all** — no `time.perf_counter()`, no
budget assertion — and git history shows it has been written that way (a pure rtol-1e-12
correctness check on a reduced grid) since it was added; this is not a regression from an
earlier, real timing test. Only `test_field_grid_numba_10x_faster_on_128_cubed_grid` is a
genuine wall-clock assertion, and it is the one de-flaked with best-of-3 timing (minimum
of three repeated measurements per path, 10× threshold unchanged), stable across three
consecutive local runs. Recorded per rule 8 rather than silently treating "one of two"
as "both" — if the 512³ test is meant to carry a real budget check later, that is new
work, not a de-flake.

**T-13.6 · Retarget T-2.9 behind a green pipeline · 1 pts · `sonnet-low` · deps T-13.2** ✅
`docs/BACKLOG.md`. Change T-2.9's `deps` from `none` to `T-13.2`.
*AC:* `schedule.py --plan` shows T-2.9 after T-13.2. **You cannot require a status check that
has never reported**, so branch protection set before a green run either fails or silently
protects nothing.

*Done 2026-08-06, immediately rather than scheduled.* The plan was checked the moment Sprint
13 parsed, and it put **T-2.9 first** — ahead of the green run it depends on. Leaving that
ordering in place while a task existed to fix it later is exactly how the wrong thing gets
done first.

**T-13.8 · `tools/gates.py` — run the five gates and report honestly · 2 pts · `sonnet-low` · deps none** ✅
`tools/gates.py` — `main() -> int`. Runs ruff check, ruff format --check, `python -m mypy src`,
`check_citations.py` and `pytest -q` in order, and prints a pass/fail line per gate.
*AC:* exits non-zero if **any** gate fails; prints each gate's name and status; never masks a
gate's exit code behind a pipe. A gate that produces no output must be reported as **failed**,
not skipped.
*Why this exists — two near-misses on 2026-08-06, both mine:*
1. `.venv\Scripts\mypy.exe src` exited **1 with zero output** for an hour before anyone
   noticed, because a broken console shim produced a silent failure indistinguishable from
   silence (HANDOVER §8).
2. Running the gates chained as `... && pytest -q 2>&1 | tail -1 && git commit` **masked a
   2-test failure**: the pipe's exit code is `tail`'s, always 0, so the chain proceeded and a
   commit was pushed unverified. The tests turned out to be the flaky pair above and the tree
   was green — but the check had stopped checking, which is the failure whether or not it
   happened to matter that time.
Both are the same defect class the project keeps finding: **a verification that cannot fail
loudly is not a verification.** A single entry point removes the chance to compose the
commands wrongly.

**T-13.7 · Trigger a fresh `researcher` pass on EQ-040's neighbours · 2 pts · `sonnet` · deps none** ✅
Not CI, but the last verification debt outstanding. `docs/INDEX.md` §1: EQ-041/042 ([FH] 4.30,
4.35), EQ-044 ([B] 123a) and EQ-045 ([FH] 3.11) were read at source 2026-08-03 by this
project rather than by an independent pass.
*AC:* an independent `researcher` confirms or corrects each; disagreements are recorded in
`docs/CLAIMS.md` with a date, not silently reconciled.

---

## Sprint 14 — Deflection tradespace (paper section R8) (22 pts)

**Why this sprint exists.** Requested 2026-08-08: the paper needs an exploration of the
tradespace among detection distance, closure velocity, threat-object mass, and the
gravity-spike strength required to move an Earth-impacting trajectory to a miss within the
lead time detection allows. Literature grounding is in
[`docs/paper/threat-population-survey.md`](paper/threat-population-survey.md). The section
generalizes R6's single-point "required = 43 N" into a surface, and is expected to be a
**walls result** (rule 5): the falsifier in T-14.6 fires if any cell reports feasibility.

**Citations verified 2026-08-08** (single batched `researcher` pass + one visual check):

- **[I]** Izzo, D., "On the Deflection of Potentially Hazardous Objects," AAS 05-141 (2005),
  open PDF: `https://www.esa.int/gsp/ACT/doc/MAD/pub/ACT-RPR-MAD-2005-OnTheDeflectionOfPotentiallyHazardousObjects.pdf`.
  **Eqs. (1)–(3) confirmed by eye this session** (automated extraction was unreliable):
  eq. (2) is the along-track drift `s = (3a/√(μR_E)) ∫ (t_s−t) v⃗·A⃗ dt`, which for an
  impulsive tangential Δv on a near-circular orbit reduces exactly to `s = 3·Δv·t_s`
  (correspondence to Scheeres & Schweickart shown on the paper's p. 6); eq. (3) is
  `d_min = γ·s` with γ ∈ [0.65, 1] tabulated in its Table 1.
  ⚠️ The PDF's *metadata* title is stale ("…density of a debris cloud" — template reuse).
  The content is the correct paper. Recorded so a future verifier is not spooked.
- **[G12]** Greenstreet, Ngo & Gladman, *Icarus* 217:355 (2012), Fig. 10 / §6: mean Earth
  impact speed **20.6 km/s**, peak ~15 km/s, tail to ~45 km/s.
- **[G20]** Greenstreet et al., *Icarus* 347:113792 (2020): median required Δv for a 1 R⊕
  miss = **1.4 / 0.76 / 0.55 / 0.46 / 0.38 cm/s** at 10/20/30/40/50 yr before impact
  (numbers confirmed via B612's own project page; Icarus PDF paywalled).
- **[P13]** Popova et al., *Science* 342:1069 (2013): Chelyabinsk 19.16 ± 0.15 km/s,
  1.3×10⁷ kg (factor-2), 19.8 ± 4.6 m. Brown et al., *Nature* 503:238 (2013): ~500 kt.
- **[S19]** Scheeres et al., *Nature Astron.* 3:352 (2019): Bennu mass 7.329 ± 0.009×10¹⁰ kg,
  bulk density **1190 ± 13 kg/m³**. ⚠️ Not Lauretta et al. *Nature* 568:55 — wrong paper for
  this claim; do not cite it.
- **[D23]** Daly et al., *Nature* 616:443 (2023): Dimorphos D = 151 ± 5 m, assumed density
  **2400 ± 300 kg/m³**; mass 4.3×10⁹ kg is *derived* from those two (the paper states no
  mass directly — docstrings must say "derived from [D23] diameter + density").
- **[C23]** Cheng et al., *Nature* 616:457 (2023), abstract: DART Δv = 2.70 ± 0.10 mm/s,
  β ∈ [2.2, 4.9].
- **[C26]** Cheng, Scolnic, Kurlander, Chow & Fernandes, arXiv:2601.16255, abstract: LSST
  discovers 79.7% of >140 m impactors (39.0% with >1 yr warning), 50.3% of 50–140 m
  (median warning 106.2 d), 26.8% of 20–50 m (21.5 d), 10.5% of 10–20 m (12.4 d).
- **Gravitational focusing** `b = R⊕√(1+v_esc²/v∞²)`: no open numbered source found
  (4 genuine attempts logged) — **elementary-mechanics carve-out** invoked, per the
  precedent in `target/deflection.py`'s module docstring.
- **UNVERIFIED and not used:** the 2017 SDT report's 2.6 g/cm³ density (40 MB PDF resisted
  fetch; only unsourced secondary mentions found). Superseded by the two *measured*
  densities [S19] 1190 and [D23] 2400 kg/m³, which are strictly better anchors.
- **[IAU]** Prša et al., *AJ* 152:41 (2016), arXiv:1605.09788, **Table 1** ("Nominal solar
  and planetary conversion constants set forth by IAU 2015 Resolution B3"): Earth equatorial
  radius (nominal) **6.3781×10⁶ m**; terrestrial mass parameter GM_E (nominal)
  **3.986004×10¹⁴ m³ s⁻²**. Verified against the full text 2026-08-08 (plan review flagged
  the earlier "verify at implementation" deferral as violating this file's own
  verify-at-planning rule — it was resolved the same day rather than deferred).

**Decisions fixed at planning — tasks below have zero open decisions:**

- **D-14.1 Miss criterion:** deflection succeeds when the unperturbed impact parameter grows
  by `b_req(v∞) = R⊕·√(1 + v_esc²/v∞²)` (gravitational focusing; carve-out above).
- **D-14.2 Lead time:** `t = d / v∞` — radial closing at the hyperbolic excess speed,
  detection distance `d` measured from Earth. Heliocentric encounter geometry is a stated
  approximation → assumption-ledger entry (T-14.8).
- **D-14.3 Required Δv, two published bounds, no invented interpolation:**
  *conservative* (impulsive floor) `Δv = b_req/t`, valid as an upper bound at all leads;
  *optimistic* (secular) `Δv = b_req/(3t)`, [I] eq. (2), valid only for `t ≥` one orbital
  period, with γ = 1 ([I] eq. (3); real encounters γ ∈ [0.65, 1] → requirement optimistic by
  ≤ 0.19 decades — ledger entry, negligible against ~30-decade gaps).
- **D-14.4 Thrust profile:** the spike force is applied continuously over the entire lead
  time (`duration = t`) — best case for the spike; ledger entry.
- **D-14.5 Channel:** absorption thrust is the only net-force radiative channel (T-8.3's
  finding: tidal coupling produces strain, no net force, and cannot alter a trajectory).
  Required luminosity is sized **at engagement start**, i.e. at source–target distance `d`,
  with geometric cross-section `σ = π(D/2)²`.
- **D-14.6 The d-cancellation is a derived result, asserted, not discovered:** with D-14.2,
  D-14.4, D-14.5: `F_req = m·b_req/(k t²)` and `L_req = F_req·4πd²c/σ`, and `t = d/v∞` gives
  `L_req = 4π c · m · b_req · v∞² / (k σ)` — **detection distance cancels exactly.** For an
  Earth-based array, detecting farther buys lower force and Δv but not lower luminosity:
  the r² dilution eats exactly what the longer lead time buys. This is the section's
  headline structural finding; T-14.5 and T-14.6 assert it to machine precision.
- **D-14.7 Grid:** `d ∈ {0.1, 0.3, 1, 3, 10, 40} AU`; `v∞ ∈ {5, 10, 17.3, 30, 50, 72} km/s`
  (17.3 = the [G12] mean impact speed 20.6 km/s stripped of focusing:
  `√(20.6² − 11.19²)`); diameters `{20, 50, 140, 500, 1000, 10000} m`; densities
  `{1190 [S19], 2400 [D23]} kg/m³`. Achieved luminosity: `7.5e-2 W`, the same array
  configuration constant `campaign_r6` uses (`lum` in `tools/run_campaign.py:652`).

**T-14.1 · Threat-population anchors · 2 pts · `sonnet-low` · deps none** ✅
`src/gwtb/target/threat.py` — frozen dataclass `ThreatAnchor(name: str, diameter_m: float,
mass_kg: float, speed_mps: float | None, source: str)`; module constants
`RHO_RUBBLE_PILE = 1190.0` ([S19]), `RHO_STONY = 2400.0` ([D23]);
`ANCHORS: tuple[ThreatAnchor, ...]` = Chelyabinsk (19.8, 1.3e7, 1.916e4, [P13]),
Dimorphos (151.0, 4.3e9, None, [D23] — "derived from diameter + density"),
Bennu (490.0, 7.329e10, None, [S19]); `mass_from_diameter(diameter: float, density: float)
-> float` = `density * pi * diameter**3 / 6`.
*AC:* `mass_from_diameter(151.0, RHO_STONY)` matches the Dimorphos anchor to rtol 2e-2;
`mass_from_diameter(490.0, RHO_RUBBLE_PILE)` matches Bennu to rtol 2e-2 (the two anchors
close on their own sources' density/diameter — this is the test that the anchor table is
self-consistent); every anchor's `source` is non-empty (absence-loud); raises on
non-positive/non-finite inputs.

**T-14.2 · Gravitational-focusing miss criterion · 2 pts · `sonnet-low` · deps T-8.8** ✅
`src/gwtb/core/constants.py` — add `GM_EARTH = 3.986004e14` and `R_EARTH_EQ = 6.3781e6`
(source comments: [IAU] Table 1 — verified at planning, see the citation block above).
`src/gwtb/target/deflection.py` — `required_miss_distance(v_infinity: float) -> float` =
`R_EARTH_EQ * sqrt(1 + v_esc**2 / v_infinity**2)` with `v_esc = sqrt(2*GM_EARTH/R_EARTH_EQ)`.
Elementary-mechanics carve-out (module-docstring precedent); docstring must state the
derivation (energy + angular-momentum conservation, unperturbed hyperbolic encounter) and
that no open numbered source exists (researcher, 2026-08-08, 4 attempts).
*AC:* `required_miss_distance(sqrt(2*GM_EARTH/R_EARTH_EQ))` = `√2 · R_EARTH_EQ` rtol 1e-12;
`required_miss_distance(1e8)` → `R_EARTH_EQ` rtol 1e-3; strictly decreasing in `v_infinity`;
raises on `v_infinity ≤ 0` or non-finite.

**T-14.3 · Required Δv, both published regimes · 3 pts · `sonnet-low` · deps T-14.2** ✅
`src/gwtb/target/deflection.py` — `required_delta_v(miss: float, lead_time: float,
orbit: float, regime: str) -> float`. `regime="impulsive-floor"`: `miss/lead_time` — an
**upper bound** on the requirement at every lead (drift is never less than impulsive);
`regime="secular"`: `miss/(3*lead_time)` per [I] eq. (2) with γ = 1 ([I] eq. (3)); **raise**
`ValueError` if `lead_time` < the orbital period implied by `orbit` (mirror image of
`miss_distance`'s existing guard — secular drift needs multiple orbits to accumulate).
Any other `regime` raises (absence-loud; no silent default).
*AC:* `secular == impulsive/3` to rtol 1e-12 wherever both are defined; **bracketing test
against [G20]** — for each published pair (10 yr, 1.4 cm/s), (20, 0.76), (30, 0.55),
(40, 0.46), (50, 0.38), with `miss = R_EARTH_EQ` (matching [G20]'s stated 1 R⊕ target,
**not** the D-14.1 focusing-corrected value) and `orbit = AU`:
`required_delta_v(..., "secular") ≤ published ≤ required_delta_v(..., "impulsive-floor")`.
All five bracket — verified at planning: impulsive gives 2.02/1.01/0.67/0.51/0.40 cm/s,
secular a third of each. This is a zero-tolerance test of *consistency with the field's
own numbers*, not a fit.

**T-14.4 · Absorption-channel inversion · 2 pts · `sonnet-low` · deps T-8.4** ✅
`src/gwtb/target/coupling.py` — `required_luminosity(force: float, cross_section: float,
distance: float) -> float` = `force * 4*pi*distance**2 * c / cross_section` (algebraic
inverse of `channel_absorption`; same Source line, same validation style; `force` must be
positive here — a required magnitude, not a signed thrust).
*AC:* round-trip `channel_absorption(required_luminosity(F, σ, d), σ, d).force == F` to
rtol 1e-12 over a log-spaced grid of F, σ, d; R6 anchor: F = 43 N, σ = π·500² m²,
d = `TARGET_RANGE` → **7.39e30 W** rtol 1e-2 (≈ 1.9e4 L_sun — the paper's scale sentence).

**T-14.5 · Tradespace grid · 3 pts · `sonnet-low` · deps T-14.1, T-14.2, T-14.3, T-14.4** ✅
⚠️ **Path deviation, found and fixed during implementation:** built at
`src/gwtb/target/tradespace.py`, **not** the `ledger/` path below. This module
imports `target/threat.py`, `target/deflection.py` and `target/coupling.py`
directly, and `target/coupling.py` already imports `ledger/gap_report.py` for
`GapReport` — placing this module under `ledger/` as originally specified
creates a *new* `(ledger, target)` package cycle, caught immediately by
`tests/unit/test_architecture.py`'s `test_the_source_propagate_cycle_is_the_only_one`.
Unlike the one documented cycle (`source`, `propagate`, a real mutual
dependency), this one would be an artifact of file placement, not a design
decision — so the fix keeps the codebase's existing one-directional rule
(`target` depends on `ledger`, never the reverse) rather than documenting a
second, spurious cycle in `KNOWN_CYCLES` and the paper's Fig. 1. See the
module docstring for the full reasoning. All downstream references (T-14.6's
`campaign_r8`, the module's own tests) import from `gwtb.target.tradespace`.
`src/gwtb/target/tradespace.py` (as built) — frozen dataclass with exactly these fifteen typed fields:
`TradespaceCell(detection_distance_m: float, v_infinity_mps: float, diameter_m: float,
density_kgm3: float, mass_kg: float, lead_time_s: float, miss_required_m: float,
delta_v_floor_mps: float, delta_v_secular_mps: float, force_floor_n: float,
luminosity_floor_w: float, luminosity_secular_w: float, gap_decades_floor: float,
gap_decades_secular: float, secular_valid: bool)`, and
`tradespace(detection_distances, v_infinities, diameters, densities, achieved_luminosity)
-> list[TradespaceCell]` over the D-14.7 grid, computing exactly the D-14.1…D-14.6 chain.
`secular_valid` is `lead_time ≥` the orbital period at `orbit = AU`; the three `*_secular*`
float fields are `nan` **iff** `secular_valid` is `False` — `nan` in any other field, or a
finite secular value alongside `secular_valid == False`, is an error. (Deliberate
asymmetry: there is no `force_secular_n`; the d-cancelled form `L = 4πc·m·b·v∞²/(kσ)`
needs no intermediate force, and a field nobody computes would invite a silent-wrong fill.)
**Every consumer of secular fields must filter on `secular_valid`, never on `isnan`** — the
flag is the contract, the `nan` is just the poison behind it. On this grid the filter bites
hard: at v∞ ≥ 17.3 km/s only d = 40 AU is secular-valid; at 5–10 km/s, d ∈ {3, 10, 40} AU.
*AC:* every field finite except the guarded secular `nan`s, with a single loud `ValueError`
naming the first offending cell otherwise; **d-cancellation (D-14.6), asserted per branch:**
`gap_decades_floor` agrees across *all* d at fixed (v∞, D, ρ) to atol 1e-9 decades, and
`gap_decades_secular` agrees across the `secular_valid` subset of d at fixed (v∞, D, ρ)
to atol 1e-9 (skipping, and counting, subsets with < 2 valid cells — the test asserts the
floor branch checked ≥ 2 points for every (v∞, D, ρ) and reports how many secular subsets
were single-point); a test feeds a mixed valid/`nan` column through the aggregation helper
and asserts the `nan` cells were excluded by the flag, not by luck; `gap_decades_floor`
strictly increasing in mass at fixed (d, v∞, ρ); spot cell pinned: (d = 40 AU, v∞ = 5 km/s,
D = 20 m, ρ = 2400) → `luminosity_secular_w` = **1.57e28 W** rtol 2e-2 (planning-session
arithmetic, confirmed independently at plan review: `4πc·m·b·v∞²/(3σ)` with
m = 1.005e7 kg, b = 1.563e7 m, σ = 314.16 m²). Note: this spot cell is deliberately *not*
the grid's minimum-gap cell (that is ρ = 1190 — see T-14.6); the two numbers must not be
expected to coincide.

**T-14.6 · Campaign R8 · 3 pts · `sonnet-low` · deps T-14.5** ✅
`tools/run_campaign.py` — `campaign_r8(outdir)` registered as `"R8"` in `CAMPAIGNS`; runs
`tradespace(...)` on the D-14.7 grid with `achieved_luminosity = 7.5e-2` (same constant as
`campaign_r6`); writes `R8.json` with the full cell list, the grid, and the achieved value.
*Falsifier (self-evaluated, like R2–R6):* fires if **(a)** any `gap_decades_*` ≤ 0 anywhere
(a vanished wall is a defect until proven a discovery — rule 5), or **(b)** the D-14.6
d-cancellation fails at atol 1e-9 decades, or **(c)** any cell is non-finite outside the
guarded secular-`nan` case.
*AC:* `--only R8` runs green; `manifest.json` gains R8 with a verdict; exit-code semantics
unchanged; R8.json's top level carries `best_case_gap_decades` = the minimum
`gap_decades_secular` **over `secular_valid` cells only** (filter on the flag, then `min` —
never bare `min()` over a `nan`-bearing sequence, which is order-dependent and silent), and
the campaign asserts `28.5 ≤ best_case_gap_decades ≤ 29.5` — plan-review computed the true
minimum as **29.016 decades**, at (D = 20 m, ρ = 1190, v∞ = 5 km/s): the rubble-pile
density, not the ρ = 2400 of T-14.5's spot cell, since the lighter body is the easier
target. That number is the section's punchline and must not be buried.

**T-14.7 · Figure 8: the tradespace · 3 pts · `sonnet` · deps T-14.6** ✅
`tools/run_campaign.py` (alongside the existing fig writers) — `fig8_tradespace.png`,
two panels, shared colourblind-safe style of Figs 3–7 (2026-08-07 redraw).
**Panel a:** heatmap of `gap_decades_secular` over (v∞, diameter) at ρ = 2400 — the axes
that *survive* the d-cancellation — annotated with the [P13]/[D23]/[S19] anchor points and
contour labels in decades. **Panel b:** required Δv vs lead time: both D-14.3 bounds as
lines, the five [G20] medians as points falling between them (the bracketing is *visible*),
and the [C26] median-warning verticals (12.4 d, 21.5 d, 106.2 d) shading the region the
discovery literature actually delivers.
*AC:* legible at single-column width; caption text lives in the figure-legends section
(T-14.8), not baked into the image; anchor points labelled by name.

**T-14.8 · Paper section R8 + ledger entries · 3 pts · `sonnet` · deps T-14.6, T-14.7** ✅
`docs/paper/nature-draft.md` — new Results subsection "R8 — The deflection tradespace"
after R7; a Methods paragraph (the D-14.1…D-14.6 chain, with citations [I], [G12], [G20],
[C26], carve-out stated); Figure 8 legend; the R8 row in the Numbers-in-this-draft section.
Content requirements: the d-cancellation stated as the structural finding; the ≈29-decade
best-corner gap; the [C26] warning-time reality check reframing *detection distance* (not
survey completeness) as what sets lead time for most size classes; explicit statement that
this section *quantifies* the wall rather than removing it.
`docs/INDEX.md` assumption-ledger entries: D-14.2 radial closing; D-14.4 duration = lead
time; D-14.3 γ = 1 (≤ 0.19-decade optimism); D-14.5 geometric cross-section.
`docs/CLAIMS.md`: tradespace inputs filed as *established*; the d-cancellation filed as
*our derivation* (elementary, from D-14.2/D-14.4/D-14.5).
*AC:* `check_citations.py` green; every number in the section traces to R8.json or a [·]
source; the survey file's remaining `NEEDS-VERIFY` rows are resolved or explicitly carried.

**T-14.9 · Rebuild the .docx · 1 pts · `sonnet-low` · deps T-14.8** ✅
Run `tools/build_paper_docx.py` after the md changes land.
*AC:* exit 0; `docs/paper/nature-draft.docx` mtime newer than `nature-draft.md`.
*Trap:* the build **overwrites** the docx — it is one-way md → docx, and a LibreOffice lock
file (`.~lock.nature-draft.docx#`) is present as of 2026-08-08. Confirm the document is
closed (or the lock is stale) before running; edits made directly in the docx are lost.

**Tier census:** 16 pts `sonnet-low`, 6 pts `sonnet`, **0 pts `opus`** — the planning
session (this one) absorbed the sprint's entire heavy lift: all decisions above are fixed,
all formulas supplied, all citations verified. 22 pts against ~22 velocity; no over-commit.
Drop candidate if needed: T-14.7's panel b (the heatmap alone carries the section; the
Δv-vs-lead panel is the strongest candidate to move to a follow-up sprint).

---

### Critical path

`T-1.1 → T-1.3 → T-1.4 → T-1.7 → T-2.1 → T-5.1 → T-6.1 → T-6.5 → T-6.8 → T-9.6 → T-10.1 →
T-12.1 → T-12.8`

Off-path branches with float: kinematics (Sprint 3), bodies (Sprint 4), visualization
(Sprint 7), backend (Sprint 11). These touch disjoint modules and are safe to parallelize —
roughly 3 sprints of compression is available if run as separate workstreams.

**Highest-risk node:** T-6.5 (spin-2 tensor superposition). No external reference
implementation exists, and a conceptual error there silently invalidates everything from G2
onward. `SPIKE-4.4` in Sprint 2 exists to surface that risk four sprints early.
