# ADR 0007 — The uniform-sphere `l = 2` finite-size form factor is `1 − 5(kR)²/98`

- **Status:** Accepted
- **Date:** 2026-08-02
- **Sprint:** 4 (SPIKE-4.5)
- **Discharges:** the missing citation that made T-4.5 not Definition-of-Ready
- **Claim category:** **B** (our derivation) — see "Citation status" below

## Context

T-4.5 needs `finite_size_correction(sphere, wavelength)`: the leading correction, in
`R/λ`, to the mass-quadrupole radiation of a body whose size is not negligible against
the wavelength.

A `researcher` pass on 2026-07-31 returned **UNVERIFIED** and, in doing so, found that
the task's own premise was wrong. Both form factors named in the original backlog entry
are **the wrong multipole order**:

- **`j₀(kR) = sin(kR)/(kR)`**, leading term `1 − (kR)²/6`, is the `l = 0`
  plane-wave phase average — the sinc pattern of antenna and acoustics array theory.
  This is **spin-1 machinery imported into a spin-2 problem**, precisely the trap
  `CLAUDE.md` rule 4 exists to catch. It must never be used for a mass quadrupole.
- **`3 j₁(kR)/(kR)`**, leading term `1 − (kR)²/10`, *is* the correct closed-form
  Fourier transform of a uniform sphere's density — but that is the **total-mass
  monopole** (`l = 0`) form factor, not the quadrupole. (This ADR's own machinery
  reproduces it exactly at `l = 0`, which is one of the checks below.)

Neither error is visible from the formula alone. Both are smooth, both → 1 as `R/λ → 0`,
and both would satisfy T-4.5's originally-written acceptance criterion. Only the
coefficient distinguishes them: `1/6` vs `1/10` vs the correct `5/98 ≈ 1/19.6`.

Prototype: `scratchpad/spike_4_5.py` — not production code, but **committed
deliberately**, unlike previous spikes'. This decision's entire justification is
numerical; if the script that produced the numbers is not in the repo, the evidence is
unreproducible and the Category B admission is unauditable. Run it with
`.venv\Scripts\python.exe scratchpad\spike_4_5.py` (~20 s); it prints `CONFIRMED` or
`MISMATCH` and re-derives every figure quoted below.

> **Finding, noticed while writing this ADR — since fixed.** [ADR-0006](0006-focused-field-far-field-regime.md)
> cited `scratchpad/spike_9_6.py` and `spike_9_6b.py`, but neither was ever committed —
> `scratchpad/` was untracked until this ADR. Those were **dangling references**, recorded
> here rather than quietly ignored per `CLAUDE.md` rule 8. Resolved 2026-08-02: a fresh
> `scratchpad/spike_9_6.py` now reproduces every figure ADR-0006 states from current
> production code, and is annotated there directly.

## Decision

**Use `F₂(kR) = 1 − 5(kR)²/98`, recorded here as this project's own derivation.**

### The framework

The exact radiative source multipole replaces the long-wavelength radial weight `r^l`
with the `j_l(kr_<)` factor of the outgoing Green's-function partial-wave expansion:

> **(eq. 1)**  `I_l^exact = [(2l+1)!! / k^l] ∫ j_l(kr) ρ_l(r) r² dr`

which reduces to `∫ ρ_l(r) r^{l+2} dr` as `kr → 0`, since `j_l(x) → x^l/(2l+1)!!`.

### The general result

For a body whose **`l`-pole radial profile is uniform on `[0, R]`**, substitute the
small-argument series for `j_l` into eq. 1 and divide by its long-wavelength limit. The
series is **citable**:

> `j_n(z) = z^n Σ_k (−z²/2)^k / [k! (2n+2k+1)!!]`
> — **DLMF 10.53.1** (https://dlmf.nist.gov/10.53), open access, numbered, checkable.

`scratchpad/spike_4_5.py` transcribes DLMF 10.53.1 literally and asserts it equals the
factored form used in the derivation, in exact rational arithmetic, for `l = 0…6`. So the
*input* to this derivation rests on a numbered equation a stranger can open; only the
specialization to a uniform ball is ours. Then:

> **(eq. 2)**  `F_l(kR) = 1 − (kR)² (l+3) / [2(2l+3)(l+5)] + O((kR)⁴)`

### The quadrupole case — what T-4.5 implements

At `l = 2`: `(l+3) = 5`, `2(2l+3)(l+5) = 2 · 7 · 7 = 98`.

> **(eq. 3)**  `F₂(kR) = 1 − 5(kR)²/98`,  `5/98 = 0.051020408163265…`

with higher terms `+ 5(kR)⁴/4536 − 5(kR)⁶/365904 …` (exact rationals), and the exact
closed form

> **(eq. 4)**  `F₂(x) = 75 [ 3 Si(x) + x cos x − 4 sin x ] / x⁵`

**T-4.5 implements eq. 3, the leading correction, as specified.** Eq. 4 is recorded
because it is the independent reference the unit tests check eq. 3 against — but it is
**cancellation-limited below `kR ≈ 0.05`** (a difference of `O(x)` terms producing
`O(x⁵)`), losing ~5 digits per decade. Do not "improve" the implementation by switching
to eq. 4; it is *less* accurate in exactly the regime the function is used in.

## Verification

Three routes, in increasing order of independence. The point of the last two is that
they share **no machinery** with the derivation — no spherical Bessel function is
evaluated anywhere in them.

| # | Method | Result for the `(kR)²` coefficient | Rel. error vs `5/98` |
|---|---|---|---|
| A | Exact rational series from **DLMF 10.53.1**, `fractions.Fraction`, no floating point | `5/98` **exactly**, for `l = 0…6` | 0 (exact) |
| A′ | Independent re-derivation by `code-reviewer` (2026-08-02), from the DLMF series and from the `Si` closed form separately | `5/98`; `x⁴`, `x⁶` coefficients confirmed **exactly** `5/4536`, `−5/365904` | 0 (exact) |
| B | Closed form eq. 4 vs direct quadrature of `j₂` | agrees to `4.4e-9` absolute in `F₂` | `3.4e-6` (cancellation-limited) |
| **C** | **Far-field retarded phase integral over a uniform ball, 2-D Gauss–Legendre, no Bessel functions** | `0.051020408163352` | **`1.7e-12`** |
| **D** | **Exact retarded Green's function `exp(ikD)/D` at *finite* distance, no far-field approximation, no Bessel functions** | `0.051020408875146` | **`1.4e-8`** |
| D′ | Literal point-mass lattice (up to 1.44e6 masses), full retarded kernel | `0.05102` | `~5e-5` (O(h) staircase) |

Check A also reproduces the **known** `l = 0` answer `1 − (kR)²/10`, i.e. the
`3j₁(kR)/(kR)` monopole form factor, which is an external anchor on the machinery: the
same expansion that yields `5/98` at `l = 2` yields a textbook-checkable result at
`l = 0`.

**On check D's residual.** It is `~2e-8` relative, larger than check C's. That residual
was diagnosed, not assumed:

- It is **flat in observation distance** (`7.1e-10` at `k·r_obs = 10`, `40` and `200`
  alike), so it is not a near-field effect — the physics does not change across that
  range.
- It **grows with quadrature order** (`7e-10 → 1e-9 → 3e-9` at 200/300/500 nodes),
  which no truncation error does. More nodes means more summands and more float64
  accumulation, with nothing left to resolve.
- `Im(F₂)`, which must vanish analytically, sits at `3e-10` and supplies a
  self-contained noise floor; the real-part deviation is ~3× it.

So the residual is float64 accumulation in the quadrature-plus-interpolation chain, not
a physical disagreement. Check C, which needs no interpolation step, pins the value to
`1.7e-12`.

## The radial profile is load-bearing — "uniform sphere" is ambiguous

**This is the finding most likely to cause a wrong result downstream.**

Eq. 2 assumes the `l`-pole mass distribution is **volume-filling**: `δρ` uniform on
`[0, R]`. A body that is uniform in density but acquires its quadrupole by **deforming
its surface** has `δρ ∝ δ(r − R)` instead, and a different answer:

> **(eq. 5)**  `F₂^surface(kR) = 15 j₂(kR)/(kR)² = 1 − (kR)²/14`

`1/14 = 0.0714285…` against `5/98 = 0.0510204…` — the surface case is **40% larger**.
(Independently confirmed by the same phase-integral method as check C, to `3.7e-13`.)

Both are "the uniform sphere". They are not interchangeable. Concretely:

- ✅ `finite_size_correction` (eq. 3) applies to a **volume-filling** `l = 2` profile.
- ❌ It must **not** be applied to `bodies/elastic.py:induced_quadrupole` (T-4.3, tidal
  Love-number deformation) or `bodies/sphere.py:oblateness_quadrupole` (T-4.6,
  Maclaurin flattening) without re-deriving. Both are incompressible-body deformations,
  i.e. **surface** profiles, for which eq. 5 is the right factor.

This is recorded in the assumption ledger. It is a wall, not a bug (`CLAUDE.md` rule 5).

## Recomputed acceptance criterion

T-4.5's original AC — "departs from unity by >1% when `R/λ > 0.1`" — was written against
the wrong form factor. With `k = 2π/λ`, so `kR = 2π(R/λ)`:

| `R/λ` | `kR` | `5(kR)²/98` | departure |
|---|---|---|---|
| 0.01 | 0.0628318530718 | 0.000201420 | 0.0201% |
| 0.05 | 0.3141592653590 | 0.005035512 | 0.5036% |
| **0.070460897** | 0.4427188724 | 0.010000000 | **1% exactly** |
| **0.1** | **0.6283185307180** | **0.020142050** | **2.0142%** |
| 0.2 | 1.2566370614360 | 0.080568199 | 8.0568% |

The old AC is *satisfied* but badly understated: the departure at `R/λ = 0.1` is
**2.0142%**, not "greater than 1%". The corrected AC asserts the actual value.

**Validity floor.** Eq. 3 is a truncated series, and `1 − 5(kR)²/98` goes **negative**
at `kR = √(98/5) = 4.4271887`, i.e. `R/λ = 0.7046`. It is a leading-order correction and
is meaningless well before that. T-4.7 adds the `R/λ > 0.1` warning; this ADR records
the hard floor.

## What T-4.5 must now implement

Definition of Ready is satisfied by this ADR. The task is:

- `finite_size_correction(sphere: Sphere, wavelength: float) -> float` in
  `src/gwtb/bodies/multipole.py`, returning eq. 3.
- Cite this ADR, **eq. 3** — not a fabricated external equation number.
- Tests: `→ 1` as `R/λ → 0`; the departure at `R/λ = 0.1` equals `0.020142050` (not
  merely "> 1%"); agreement with the exact closed form eq. 4 in its valid range.
- **A regression test naming both wrong form factors**, asserting the returned value is
  inconsistent with `1 − (kR)²/6` and `1 − (kR)²/10`. Given rule 4's risk class, a
  future contributor "fixing" this back to a sinc is the failure mode to guard by name.

## Citation status

**No numbered equation for eq. 2 or eq. 3 was found in any accessible source.** Searches
across the open-access literature (2026-07-31 `researcher` pass; a further bounded pass
2026-08-02) returned nothing citable. Thorne, *Rev. Mod. Phys.* **52**:299 (1980) remains
the likely original primary source for eq. 1's framework, but it is paywalled and its
equation numbering is **unconfirmed** — it is therefore *not* cited with an equation
number here, and must not be. Per `CLAUDE.md` rule 1, a guessed equation number is worse
than none.

What *is* cited, and verified: the series input, **DLMF 10.53.1** (open access, numbered,
transcribed and checked in exact rational arithmetic by the prototype). The uncited step
is therefore narrower than "the whole result" — it is specifically the **integration of
that series against a uniform-ball radial weight**, which is elementary. That is the gap
a future source needs to close.

Note that check D verifies eq. 1's framework *empirically*: it integrates the retarded
Green's function directly and recovers the same coefficient, so the framework does not
rest on an uncited assertion either.

## Reversal condition

**To promote this to Category A**, someone must produce a numbered equation, in a source
a stranger can open, for either eq. 2 or eq. 3 — with the **volume-filling radial
profile** stated explicitly. A source giving `1 − (kR)²/14` is *not* a confirmation of
this ADR; it is the surface-profile case (eq. 5) and confirms something else.

**This decision fails** if the volume-filling premise is wrong for the caller's body —
which is exactly the elastic/oblateness case above. Reversing for those callers means
deriving their profile's own form factor, not editing this constant.

If a numerical check ever disagrees with `5/98` beyond the floors recorded above, the
derivation is wrong and T-4.5 must be re-blocked, not patched.
