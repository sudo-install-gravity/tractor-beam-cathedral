# ADR 0006 — `focused_field` operates in the far field, and what that costs

- **Status:** Accepted
- **Date:** 2026-07-31
- **Sprint:** 9 (SPIKE-9.6)
- **Discharges:** the open design decision that made T-9.6 not Definition-of-Ready

## Context

T-9.6 (`focused_field`) is `opus`-tier and on the critical path. It was **not** Ready: it
contained an unresolved design decision that only surfaced while building T-9.5.

`superpose_tt` (T-6.5, per [ADR-0003](0003-spin2-superposition.md)) sums TT-projected tensors
along **one common observation direction**, and raises inside the Fraunhofer distance. ADR-0003's
own reversal condition says the common-`n̂` assumption "holds for a distant target but **not**
within the near field of a large array." Focusing, meanwhile, is conventionally a *near-field*
operation — a focal point at finite range, not a direction at infinity.

So either `focused_field` cannot use `superpose_tt`, or the premise of "focusing" needs
restating. Per the Definition of Ready this is a spike, not an implementation detail.

Prototype: `scratchpad/spike_9_6.py`, `spike_9_6b.py` (scratch, not production code).

## Decision

**`focused_field` is a far-field construction and builds on `superpose_tt` unchanged.**

```
focused_field(...) = superpose_tt(elements, weights = exp(+i · focal_phases(...)), λ, x)
```

ADR-0003's reversal condition is **not** triggered at engagement range, by a wide margin. The
angular spread of per-element observation directions at 40 AU is:

| Quantity | Value |
|---|---|
| Max angle between per-element `n̂_a` and the common `n̂` | **1.034e-9 rad** |
| Resulting spin-2 polarization error (`2Δθ`) | **2.068e-9 rad** |
| ADR-0003's alignment budget for 1% gain loss (`σ`) | 5.009e-2 rad |
| **Margin** | **2.4 × 10⁷ ×** |

The wavefront sag across the aperture is 3.20e-6 m, i.e. 6.7e-8 rad of discarded Fresnel phase
at 1 MHz, and `R / R_Fraunhofer = 5.9e6`. A single common direction is not an approximation here
in any practical sense.

**Consequence, stated plainly: at 40 AU a "focal point" is a steering direction.** Focusing and
steering are the same operation at this range. This is the wall already recorded in the
assumption ledger, seen from the array side rather than the target side.

Near-field focusing is **out of scope**, and `superpose_tt`'s existing Fraunhofer guard enforces
that by raising. Supporting it would require projecting each element along its own `n̂_a`, which
ADR-0003 forbids, and therefore a new ADR.

## Four traps this spike found, all of which would produce a passing but meaningless test

These are the spike's real value. Each was measured, not reasoned about.

### 1. The array is sub-wavelength at the project's nominal drive frequency

| `f` | `λ` | `D/λ` for the 12.4 km reference aperture |
|---|---|---|
| 100 Hz | 3.00e6 m | 0.004 |
| **1 kHz** | **3.00e5 m** | **0.041** |
| 10 kHz | 3.00e4 m | 0.413 |
| 100 kHz | 3.00e3 m | 4.13 |
| 1 MHz | 3.00e2 m | 41.3 |

At 1 kHz the entire aperture spans **0.04 wavelengths**. It is not an array — it is a point
source, automatically co-phased, with no beam, no steering and no focusing. Every weighting
returns exactly `N`:

```
0 beamwidths off-axis:  exp(+iφ) = 64.000   exp(−iφ) = 64.000   unsteered = 64.000
```

**T-9.6's acceptance criterion "peak amplitude at the focus is N·A" is therefore satisfied by
returning `N·A` unconditionally, with the focusing logic deleted.** Any test at 1 kHz is vacuous.
Use `f ≥ 1e5 Hz` for this geometry, and assert `D/λ > 1` in the test itself.

### 2. The sign convention is undetermined near broadside

| Off-axis | `exp(+iφ)` | `exp(−iφ)` | unsteered |
|---|---|---|---|
| 0 beamwidths | 64.000 | 64.000 | 64.000 |
| 5 beamwidths | 63.537 | 63.485 | 0.282 |
| **50 beamwidths** | **44.969** | **5.677** | 6.851 |

**`exp(+i·φ)` is correct**, matching `superpose_tt`'s `exp(+i k·r_n)` array-factor convention.
But at 5 beamwidths the two signs differ by 0.08% — a test there passes with the sign inverted.
The convention must be pinned **tens of beamwidths off-axis**.

### 3. Peak gain is `N` only near broadside

At 50 beamwidths (≈69° off broadside) the correctly-steered peak is **44.97, not 64**: the
element's own quadrupole pattern and the geometric projection both fall off. The AC's "N·A to
rtol 1e-6" is a **broadside** statement. Off-axis it is wrong, and tightening the tolerance to
force agreement would be fitting the test to a misreading.

### 4. The background is `√(Nπ)/2`, not `√N`

For random phases the mean magnitude of the sum is Rayleigh-distributed with mean `√(Nπ)/2 ≈
0.886√N` — **7.09** at N=64, against a naive `√N` of 8.00. The AC's "background is ~√N·A" is
right to within its "~", but an implementer chasing the 12% discrepancy would be chasing correct
behavior. The peak-to-background *ratio* does scale as `√N` (measured 8.75 vs 8.00), and that
ratio is the mode-locking signature worth asserting.

## What T-9.6 must now implement

Definition of Ready is satisfied by this ADR. The task is:

- `focused_field(array, drive, field_points, times)` in `src/gwtb/array/focus.py`.
- Weights `exp(+i · focal_phases(...))`, superposed by `superpose_tt`. No new projection logic.
- Propagate `superpose_tt`'s Fraunhofer `ValueError` rather than catching it — a near-field
  request is out of scope and must fail loudly, not degrade.
- Tests at `f ≥ 1e5 Hz`, asserting `D/λ > 1` explicitly.
- Peak `= N·A` to rtol 1e-6 **at broadside only**.
- Sign convention pinned at ≥ 50 beamwidths off-axis, asserting the wrong sign fails.
- Peak-to-background ratio `~√N`; compare the background against `√(Nπ)/2`.

## Claims classification

The far-field reduction is **Category B** (our derivation), resting on A-8 and ADR-0003's B-1.
It does not promote or demote any existing claim. The sub-wavelength finding sharpens **B-3**:
the aperture requirement is not merely large, it is unreachable at any GW-plausible frequency
for apertures of this scale.

## Reversal condition

If a configuration ever places the target inside the array's Fraunhofer distance — which for a
12.4 km aperture at 1 MHz means closer than ~1.0e6 m — this decision fails along with ADR-0003's
common-`n̂` premise. Reversing requires a new ADR deriving the per-element projection rule, and
must show, with a two-element prototype in the style of SPIKE-4.4, what the sum of tensors
projected along differing directions physically means. Do not resolve it inside an
implementation.
