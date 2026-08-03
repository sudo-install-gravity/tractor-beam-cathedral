# ADR 0003 — Spin-2 tensor superposition for a gravitational-wave phased array

- **Status:** Accepted
- **Date:** 2026-07-27
- **Sprint:** 2 (SPIKE-4.4)
- **Supersedes for GW purposes:** the scalar array factor in `array/beamform.py`

## Context

`T-6.5` (spin-2 tensor superposition) is the highest-risk node on this project's
critical path. It is the point where the phased-array formalism borrowed from radar must be
extended from a spin-1 to a spin-2 field, and **no external reference implementation exists to
check it against**. A conceptual error here would silently invalidate `T-6.6`, `T-9.6`, `T-10.1`
and every result built on them.

`SPIKE-4.4` was pulled forward from Sprint 6 to Sprint 2 specifically so that risk would surface
four sprints before anything depended on it. This ADR is its output. Per the Definition of Ready,
a spike produces a decision record and **no production code**; the prototype used here was
scratch.

## Decision

**Superposition acts on the TT-projected tensor, and the resulting element-to-element mismatch
factor is `cos(2Δψ)`, not `cos(Δψ)`.**

For an array of `N` elements observed along `n̂`, the total strain is

```
h_ij^TT(n̂) = Σ_n  Λ_ij,kl(n̂) · h_kl^(n) · e^(i φ_n)
```

After TT projection the field lives in a **two-dimensional** polarization space spanned by
`e⁺` and `e^×`, so the sum is a *vector* sum in that space, not a scalar sum:

```
(h₊, h_×)_total = Σ_n A_n · (cos 2ψ_n, sin 2ψ_n) · e^(i φ_n)
```

where `ψ_n` is the orientation of element `n` about the line of sight. Equivalently, writing
`h ≡ h₊ − i h_×`, a rotation by `ψ` acts as `h → h e^(2iψ)`.

### Verified against hand-derived analytics

For a linear quadrupole oscillator along `û = (cos ψ, sin ψ, 0)` observed along `ẑ`, the TT part
is analytically

```
h^TT = ½ [[ cos2ψ,  sin2ψ ],
          [ sin2ψ, -cos2ψ ]]
```

The prototype reproduced this **to 1e-14** across ψ ∈ {0°, 15°, 22.5°, 30°, 45°, 60°, 90°, 135°,
180°}, and confirmed the period in ψ is **180°, not 360°**.

Two co-phased elements, the second rotated by `Δψ`:

| Δψ | measured gain | `2 + 2cos(2Δψ)` | EM would predict | outcome |
|---|---|---|---|---|
| 0° | 4.000000 | 4.000000 | 4.000000 | full coherence, gain N² |
| 30° | 3.000000 | 3.000000 | 3.732051 | partial |
| **45°** | **2.000000** | 2.000000 | 3.414214 | **orthogonal — power adds, gain N** |
| 60° | 1.000000 | 1.000000 | 3.000000 | partial |
| **90°** | **0.000000** | 0.000000 | 2.000000 | **complete cancellation** |
| 180° | 4.000000 | 4.000000 | 0.000000 | full coherence again |

## Consequences

### 1. The 90° case is a qualitative trap, not a quantitative correction

Two elements at 90° **cancel completely**. Spin-1 intuition says they are polarization-orthogonal
and their powers add (2×). An array laid out on EM reasoning with orthogonally-oriented elements
would radiate **nothing** along the intended axis, and the designer would have every reason to
expect twice the single-element power.

Physically this is not exotic: an x-oriented oscillator stretches along x and squeezes along y,
while a y-oriented one does the reverse. Co-phased, they annihilate. But it is invisible to
anyone reasoning by analogy from antenna theory, which is why `CLAUDE.md` rule 4 exists.

### 2. Array gain is N² only for co-oriented elements

```
gain = | Σ_n A_n e^(2iψ_n) |² / A²
```

This equals `N²` only when all `ψ_n` are equal modulo 180°. Any orientation spread costs gain,
and the loss is governed by `2ψ`, so it accrues twice as fast as spin-1 intuition suggests.

### 3. Element alignment tolerance — a hard engineering requirement

For orientations jittered with standard deviation `σ` about a common axis, the gain fraction is

```
gain / N²  ≈  exp(−4σ²)
```

Measured against 400 realizations at N = 100 and N = 1000, this matches to ~1e-4 across
σ ∈ [0°, 20°]:

| σ | 1° | 2° | 2.9° | 5° | 10° | 20° |
|---|---|---|---|---|---|---|
| measured (N=1000) | 0.99879 | 0.99515 | 0.98978 | 0.97010 | 0.88562 | 0.61511 |
| `exp(−4σ²)` | 0.99878 | 0.99514 | 0.98980 | 0.97000 | 0.88528 | 0.61423 |

**For 1% power loss, elements must be co-oriented to σ ≤ 2.87°.** The spin-1 equivalent
(`exp(−σ²)`) would permit 5.73°. **The spin-2 tolerance is exactly 2× tighter**, and this is a
constraint on any physical array design, not a modelling detail.

---

#### ⚠ Amendment, 2026-08-03 — the law is the N → ∞ limit, and the "~1e-4" above is overstated

**The physics is unchanged. The stated precision was wrong, and the reason is a finite-N
bias that this ADR never named.** Original text above retained verbatim; do not delete it.

`exp(−4σ²)` is the **N → ∞ limit**. At finite `N` the estimator carries an exact positive
bias:

```
E[gain / N²]  =  exp(−4σ²)  +  (1 − exp(−4σ²)) / N
                     ↑ the law above      ↑ finite-N bias, falls as 1/N
```

**Derivation.** With `z_n = exp(2iψ_n)`, `ψ_n ~ N(0, σ²)` iid, and `μ = E[z] = exp(−2σ²)`
(the normal characteristic function at `t = 2`):

```
E[|S|²] = Σ_n E[|z_n|²] + Σ_{n≠m} E[z_n] E[z_m*] = N·1 + N(N−1)μ²
E[gain] = E[|S|²]/N² = μ² + (1 − μ²)/N ,   μ² = exp(−4σ²)
```

The `N·1` term is the `|z|² = 1` self-term. It cannot vanish, and divided by `N²` it leaves
a `1/N` floor.

**Verified** — `scratchpad/spike_b1_alignment_bias.py`, 400,000 realizations per point.
Observed/predicted lands in **[0.95, 1.03]** across `N ∈ {100, 200, 1000}` and
`σ ∈ {2.87°, 10°, 20°}`, and the deviation halves as `N` doubles (mean ratio **1.962**
against an expected 2.000).

**What this means for the table above.** Its own numbers already contradict the "~1e-4"
summary, which nobody checked at the time:

| σ | 1° | 2° | 2.9° | 5° | 10° | 20° |
|---|---|---|---|---|---|---|
| deviation in the table above | +1e-5 | +1e-5 | −2e-5 | +1e-4 | **+3.4e-4** | **+8.8e-4** |
| predicted bias `(1−exp(−4σ²))/N`, N=1000 | 1.2e-6 | 4.9e-6 | 1.0e-5 | 3.0e-5 | 1.1e-4 | 3.9e-4 |

⚠️ **These two rows are not expected to match, and the gap is not evidence against the bias
formula.** The original table used only **400 realizations**, whose standard error (~2.4e-4
at σ = 10°, ~6.8e-4 at σ = 20°) is itself comparable to or larger than the systematic term —
so its printed deviations are noise-dominated, and the σ = 2.9° entry is even *negative*
where the bias is strictly positive. The row is shown to make one point only: **the table's
own deviations already exceed the "~1e-4" summary above it**, whatever their composition.
The clean, noise-suppressed confirmation of the bias formula is check A of
`spike_b1_alignment_bias.py` (400,000 realizations; observed/predicted ∈ [0.95, 1.03]).

The claim holds only for **σ ≲ 5°, and only at the larger N**. At `N = 100` — which this
ADR also cites — the bias *alone* is **1.2e-3 at σ = 10°** and **3.9e-3 at σ = 20°**, i.e.
up to 39× the claimed figure. **The corrected statement:** the law is exact as `N → ∞`, and
at finite `N` the measured gain fraction sits **above** it by `(1 − exp(−4σ²))/N`.

**Consequences.**

- The **engineering conclusion is unaffected, and is if anything conservative**: the bias is
  positive, so a real finite array performs *slightly better* than `exp(−4σ²)` predicts.
  **σ ≤ 2.87° for 1% loss, exactly 2× tighter than spin-1, stands** — it is a property of
  the law itself, now asserted analytically rather than by simulation.
- `tests/unit/test_superposition.py` previously asserted the **bare law** at `N = 200` with
  `abs=2e-3`. That tolerance was **correctly sized, not sloppy** — at `N = 200` the bias
  alone is 5.7e-4 and per-run noise ~7.6e-4 — and it **could not have been tightened** to
  the ADR's figure, because no tolerance at `N = 200` can reach 1e-4. The test now asserts
  the **bias-corrected** prediction to **5 standard errors of the estimator's own sampling
  distribution**, over σ ∈ {2.87°, 5°, 10°, 20°} at N = 200, 50,000 realizations.
- **The tolerance is statistical, not absolute, and that is deliberate.** A flat absolute
  tolerance was tried first and is the wrong tool: the estimator's standard error spans 30×
  across this σ range (4.5e-6 at 2.87°, 1.4e-4 at 20°), so any single number is either
  vacuous at small σ or *below one standard error* at large σ. A flat `abs=1e-4` sat at
  **0.7 SE** at σ = 20° and failed **13 of 30 reseeds** while passing on the committed seed
  — a coin flip dressed as a margin. **Do not reintroduce one.** The 5-SE form is
  seed-robust (0 failures in 40 reseeds at every σ).
- **Do not "simplify" the `(1 − exp(−4σ²))/N` term back out.** Dropping it is rejected by
  **2.2–2.9× at every σ tested**, guarded by name in
  `test_uncorrected_asymptotic_law_is_rejected_at_finite_n`, which also asserts that the
  departure *is* the predicted bias rather than an arbitrary disagreement.

**Citation status — Category B, with an unresolved precedent question.** The bias term is
recorded as this project's own derivation (EQ-054, eq. n/a). But `code-reviewer` flagged
2026-08-03 that the *statistical skeleton* — `E[|S|²] = N + N(N−1)μ²` for `N` iid random
unit phasors, giving a finite-array gain law of exactly this shape — is plausibly the
classical antenna-tolerance result of **Ruze, "Antenna Tolerance Theory — A Review," *Proc.
IEEE* 54(4):633–640 (1966)**, whose equation number could **not** be confirmed here. Per
rule 1 it is therefore cited *without* one, and deliberately not treated as established.

Two conditions on anyone who resolves this:

1. **Ruze is a spin-1 antenna source** (rule 4, rule 6). It could at most supply the generic
   random-phasor statistics. The `4σ²` prefactor — the spin-2 doubling that makes this
   tolerance 2× tighter than the EM case — is *not* in it and remains Category B regardless.
2. A confirmed Ruze equation would promote only the `(1−μ²)/N` structure, not the alignment
   law. **Do not let a spin-1 citation launder the spin-2 result into Category A.**

This sub-result did **not** go through a `researcher` pass before implementation, which the
mandatory workflow requires for physics formulae. It was derived and verified numerically
instead. That is a real process deviation and is recorded here rather than glossed: the
numerical evidence is strong (three checks, agreement to within 5%), but a citation search
is still owed.

**Process finding.** This was caught by an audit of the manuscript against the test suite,
not by any gate: the paper quoted a precision figure **better than CI enforced**, and both
numbers traced back to this sentence. A stated precision is a claim, and this project had no
mechanism requiring one to match the assertion that backs it. Nothing was numerically wrong
anywhere — the *summary of how well it was known* was.

### 4. What `array/beamform.py` is and is not

The existing scalar array factor remains correct **as the spin-1 baseline it is documented to
be**. `T-6.5` must reduce to it exactly for co-oriented elements — that is the regression check
that proves the extension is a controlled departure rather than a rewrite. It must **not** be
used for gravitational radiation on its own.

## What T-6.5 and T-6.6 must implement

**T-6.5 `superpose_tt`:**
- Sum TT-projected tensors along the common observation direction; never scalar amplitudes.
- Reduce to the scalar array factor for co-oriented elements, to rtol 1e-9.
- For orthogonally-oriented elements (Δψ = 45°), gain must be strictly less than N².

**T-6.6 `mismatch_loss`:**
- Returns `cos(2Δψ)`.
- Zero loss at Δψ = 0; **maximal at 45°, not 90°**; period 180°.
- A test must assert the 90° **cancellation** explicitly — it is the case most likely to be
  "fixed" by someone applying EM intuition.

## Claims classification

- The `e^(2iψ)` transformation of GW polarization is **Category A** (established physics;
  `CLAIMS.md` A-5).
- Its consequences for phased-array gain, the `cos(2Δψ)` mismatch factor, and the `exp(−4σ²)`
  alignment tolerance are **Category B** (our derivation) — this ADR discharges claim **B-1**,
  which was previously "not yet derived".

## Reversal condition

This analysis assumes the far-field, linear, TT regime — valid throughout this project
(`h ~ 1e-40`, `r/λ ~ 2e4` at target range). It also assumes elements share an observation
direction, which holds for a distant target but **not** within the near field of a large array.
If a future configuration places the target inside the array's near zone, the common-`n̂`
assumption fails and this must be revisited.
