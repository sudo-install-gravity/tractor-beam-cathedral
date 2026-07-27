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
