# ADR 0009 — The magnitude wall's "wall vanishes" configuration requires a superluminal source

- **Status:** Open finding — external review, not yet triaged by `researcher`/`code-reviewer`
- **Date:** 2026-08-17
- **Sprint:** N/A — external review, not sprint-scoped
- **Discharges:** nothing yet. Raises **OQ-8** (see `docs/INDEX.md` §5). No task currently
  depends on this; it should block nothing by itself, but it should not be silently
  reproduced in the manuscript either — see "Consequences" below.
- **Claims classification:** bears on **C-2** (the magnitude gap) via `docs/paper/campaign/R5.json`'s
  `emission_across_scoping_set`, and on **C-1** (the transducer problem's scope). No claim
  in `docs/CLAIMS.md` is demoted by this ADR — it identifies that one scoping *example* used
  to illustrate C-2 is invalid, not that C-2's derivation (B-9, B-5) is wrong.

## Context

`docs/PHYSICS.md` §8 and `docs/paper/campaign/R5.json` report, as this project's most
counterintuitive finding, that the magnitude wall's sign flips for one configuration in the
scoping set:

| Configuration | `v_tip = πfL` | `v/c` | Luminosity | Gap (decades) |
|---|---|---|---|---|
| 10 t rod, 10 m, 1 kHz | 3.14×10⁴ m/s | 1.05×10⁻⁴ | 7.5×10⁻²⁰ W | +29.25 |
| 10⁹ kg, 1 km, 1 kHz | 3.14×10⁶ m/s | **1.05×10⁻²** (PHYSICS.md's own figure) | 7.5×10⁻² W | +11.25 |
| **10⁹ kg, 1 km, 1 MHz** | **3.14×10⁹ m/s** | **≈10.5** | 7.5×10¹⁶ W | **−6.75** |

The third row is quoted in `README.md`, `docs/CLAIMS.md` (C-2), and the manuscript as the
case where "one wall does not bind" — the headline that the emission gap is not a single
number but a range, −6.75 to +29.25 decades.

**That row requires the rod tip to move at roughly ten times the speed of light.** The
formula used to compute it, `P = (2/45)(G/c⁵) M² L⁴ ω⁶` (`docs/PHYSICS.md` §8,
`tests/benchmarks/test_spinning_rod.py`), is the non-relativistic, leading-order quadrupole
approximation — it is derived (§2 of `PHYSICS.md`) from a slow-motion, weak-field expansion
that assumes `v/c ≪ 1` throughout. Nothing in the codebase checks that assumption before
evaluating the formula.

## Derivation

The rod's mass points sit at radius `L/2` from the spin axis (`docs/PHYSICS.md` §8's own
model: a rigid rod of length `L` spinning about its center at angular rate `ω`), so the
material speed at the tip is

```
v_tip = ω · (L/2) = π f L
```

**Crossover to `v = c`.** Solving `π f L = c` for `L = 1000 m`:

```
f_c = c / (π L) = 2.99792458e8 / (π · 1000) ≈ 95,414 Hz  ≈ 95.4 kHz
```

Above ~95 kHz, this configuration is not an engineering difficulty — it is kinematically
impossible for any material object, independent of what drives it.

**Crossover to where the naive formula predicts the gap closes.** `P ∝ ω⁶` at fixed `M, L`.
Anchoring on the project's own tabulated `P(1 kHz) = 0.075 W`
(`docs/paper/campaign/R5.json`) and required luminosity `L_req ≈ 1.330×10¹⁰ W` (same file,
`ledger_rows[1].required`):

```
f_req = 1 kHz · (L_req / P(1 kHz))^(1/6)
      = 1000 · (1.330e10 / 0.075)^(1/6)
      = 1000 · (1.773e11)^(1/6)
      ≈ 1000 · 74.9
      ≈ 74,900 Hz  ≈ 74.9 kHz
```

At that frequency, `v_tip/c = π(74,900)(1000)/c ≈ 0.785`. **The naive formula's own
gap-closing point sits at `v/c ≈ 0.78`** — deep in a regime where the discarded
post-Newtonian correction terms (formally of order `v²/c² ≈ 0.6` here) are comparable to
the leading term the formula keeps, so the leading-quadrupole truncation is not
trustworthy there even before the harder `v > c` line at 95.4 kHz is crossed. The quoted
1 MHz example, at `v/c ≈ 10.5`, is an order of magnitude past both thresholds.

**Reproduce:** the only inputs are `L = 1000 m` (given), `f` (given per row), and the two
values `P(1 kHz) = 0.075 W` and `required = 1.330e10 W` already printed in
`docs/paper/campaign/R5.json`. No code in this repository needs to be run to check this
arithmetic — that is deliberate, matching this project's own preference for self-auditable
claims (cf. A-9).

## Why this was not caught by the existing walls

It sits inside the *emission* row's own scoping table, not downstream of it. The project's
diffraction and coupling walls (§8, §6.1) are evaluated independently of frequency choice
and correctly still bind at 1 MHz (8.16 and 14.0 decades respectively per R5/R6). The
emission number itself, though, is computed by extrapolating a slow-motion formula to a
frequency chosen specifically because `ω⁶` scaling makes it numerically favorable — without
re-checking that the formula's own `v ≪ c` precondition still holds at that frequency. Rule
5 ("a wall is a finding, not a bug; a change that removes one is presumed defective until
proven otherwise") was written for exactly this shape of failure, but it wasn't applied
here because the "change" is a choice of scoping parameter, not a code edit — nothing in
the review process currently treats a frequency selection as needing the same scrutiny as a
diff.

## A related, likely more binding gap: no material-strength ceiling exists anywhere in the model

Independent of the relativity point, no module in `src/gwtb/` bounds `(M, R, ω)` against
material tensile/yield strength. `bodies/elastic.py`'s "material strength" enters only as an
input to a *linear elastic deformation* (Love-number) calculation — how much a body bends
under load — never as a failure ceiling on how much load it can take before disintegrating.

Order-of-magnitude: holding a rotating/oscillating body of radius `R` together against
`a ~ ω²R` requires internal stress `σ ~ ρω²R²`, bounded by material strength (~10⁸–10⁹ Pa
for the best engineering materials). For the "1 kHz" row above — already flagged as safely
non-relativistic (`v/c ≈ 0.01`, i.e. a tip speed of ~3,000 km/s) — no known solid material
survives centripetal/oscillatory stress at that speed intact. **This suggests the entire
high-frequency end of the `ω⁶` lever the project leans on hardest ("frequency is the
dominant lever by ~36 decades between 1 Hz and 1 MHz," `README.md`) may be structurally
unreachable well before it is even kinematically forbidden**, which would make this a
fourth wall, prior to diffraction/coupling/magnitude, currently absent from the feasibility
ledger. This part of the finding is qualitative — it depends on source geometry
(cross-section, not just `M` and `L`) that isn't pinned down enough here for a precise
number, so it is recorded as a candidate follow-up (see OQ-8) rather than a derived result.

## Consequences

- **`docs/CLAIMS.md` C-2** should carry a caveat that the `−6.75` decade end of the emission
  range in `R5.json` is computed outside the source formula's non-relativistic validity
  domain, alongside the coupling/diffraction caveats already there.
- **`docs/paper/campaign/R5.json`'s `investigation.why_it_does_not_imply_feasibility`**
  currently attributes the 1 MHz row's unreality entirely to *"the TRANSDUCER problem is
  out of scope by charter (conjecture C-1)"* — framing it as an open engineering question.
  For frequencies above ~95.4 kHz that characterization is wrong: it is a closed kinematic
  impossibility (special relativity), not an unsolved actuator problem, and the manuscript
  should not present it as the latter.
- **The R8 432-cell tradespace campaign** (`docs/paper/campaign/R8.json`) should be audited
  for any other cell with `v/c` approaching or exceeding 1 under the same rod/oscillator
  kinematics — nothing in the current pipeline would flag one.
- **A `v < c` (and, more conservatively, `v/c ≪ 1`) guard** on the source kinematics inputs
  would be a natural addition to `core/validation.py` or the point where scoping tables are
  generated, so this class of error fails loudly rather than producing a plausible-looking
  number.
- This does **not** undermine B-1 through B-9's derivations, the Hulse–Taylor benchmark, or
  the diffraction/coupling walls — none of those depend on the high-frequency corner of the
  scoping table.

## Reversal condition

This finding is wrong if either: (a) the rod/oscillator kinematic model in
`tests/benchmarks/test_spinning_rod.py` and `docs/PHYSICS.md` §8 does not in fact imply
`v_tip = πfL` for the quoted configurations (i.e., this ADR has mischaracterized the
model), or (b) `docs/paper/campaign/R5.json`'s own `P(1 kHz)` and `required` figures used
above are stale relative to the current ledger. Both are checkable directly against the
cited files without rerunning anything.

## Status of this ADR

Recorded as an **open finding**, not a decision — this project's convention (ADR-0008) for
a result that identifies a real gap without itself being the fix. Per the mandatory
workflow in `CLAUDE.md`, resolving it should go through `researcher` (to check whether a
relativistic or finite-size-retarded treatment already exists in the literature for this
regime) and `code-reviewer` before any code changes, and `indexer` afterward.
