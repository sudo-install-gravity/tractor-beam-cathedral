# Physics Framework

First-principles derivation of what `gwtb` computes. A contributor should be able to audit the
foundations from this document alone, without reading the code.

**Status: complete and fully sourced (2026-08-10, T-12.5).** Every equation below carries a
citation whose exact number a reader can check, and every Category B claim in
[`CLAIMS.md`](CLAIMS.md) has a derivation here together with a limiting case that reduces it to
a Category A result — §10 indexes both. **No `[UNVERIFIED]` markers remain.**

This document is the *argument*; [`INDEX.md`](INDEX.md) is the *registry*. Equation-level
provenance, per-function validation status, and the assumption ledger live there.

Verification substituted **open-access sources for textbooks**. Maggiore and MTW equation numbers
could not be confirmed without the physical books, and a citation a contributor cannot check is
not a citation — a real constraint for a project meant to outlive its founders. Primary sources:

- **[B]** Blanchet, L., *Living Rev. Relativ.* **17**:2 (2014), arXiv:1310.1528
- **[FH]** Flanagan, É.É. & Hughes, S.A., *New J. Phys.* **7**:204 (2005), arXiv:gr-qc/0501041

⚠️ [FH] eqs. (4.41)–(4.42) contain typos we verified numerically — see
[`ERRATA.md`](ERRATA.md). The derivations we depend on ([FH] 4.17–4.23) are sound.

---

## 0. Conventions

To be fixed at first implementation and never changed silently:

- **Metric signature:** −+++ (MTW convention)
- **Index convention:** Latin `i,j,k` are spatial (1–3); Greek `μ,ν` are spacetime (0–3);
  repeated indices summed
- **Quadrupole:** `Q_ij` denotes the **reduced (trace-free)** moment throughout. Where a source
  uses the full moment `I_ij`, the conversion is noted at the point of use
- **Units:** SI internally. Strain is carried in scaled representation (see §7)

---

## 1. Why linearized gravity is the correct tool here

The strains in this problem are of order h ~ 10⁻⁴⁰. Full numerical relativity — Einstein
Toolkit, GRChombo, SpECTRE — solves the strong-field 3+1 evolution of spacetime near compact
objects, a regime this project never enters.

Working to linear order is therefore not an approximation of convenience. It is exact for our
purposes, and it buys the property the entire project depends on:

> **Superposition holds exactly.**

Without exact linearity, "phased array" would be meaningless — the fields of separate elements
could not be added. This is why the array formalism of §5 is legitimate. See
[`adr/0001-linearized-gr.md`](adr/0001-linearized-gr.md).

Write the metric as `g_μν = η_μν + h_μν` with `|h_μν| ≪ 1`, and define the trace-reversed
perturbation `h̄_μν = h_μν − ½ η_μν h`. In harmonic gauge the field equation becomes a wave
equation with the retarded solution:

```
h̄^μν(t, x) = (4G/c⁴) ∫ T^μν(t − |x − x'|/c, x') / |x − x'| d³x'
```

*Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 1 — **VERIFIED** 2026-07-26*

---

## 2. Why the leading radiation is quadrupolar — and why this constrains the whole design

Expanding the retarded integral in multipoles:

- **Mass monopole** — total mass-energy, conserved. `d²M/dt² = 0`. **No radiation.**
- **Mass dipole** — `d_i = ∫ρ x_i d³x` is the center of mass. Its second derivative is
  `dP_i/dt`, the net external force. For an isolated system momentum is conserved, so
  **no radiation.**
- **Mass quadrupole** — first non-vanishing term.

*Follows from momentum conservation; multipole structure per Blanchet,
Living Rev. Relativ. 17:2 (2014), eq. 3 — **VERIFIED** 2026-07-26*

**This is the single most important constraint on the project.** The kickoff specification says
we need not care where the accelerating force comes from. Physically, we must: the reaction is
exactly what cancels the dipole. Two regimes:

| Regime | Momentum | Leading term | Physical? |
|---|---|---|---|
| Reaction mass inside the model | Conserved | Quadrupole | **Yes** |
| External agent pushes the spheres | Not conserved | Dipole (~10¹⁰ × larger) | **No** — violates ∂_μT^μν = 0 |

`gwtb` computes both. The momentum-conserving quadrupole is the default and the only mode
permitted for headline results. The external-reservoir mode exists as a diagnostic and stamps
every output `UNPHYSICAL`. See `src/gwtb/source/conservation.py`.

The linearized field equations are, strictly, *inconsistent* with a non-conserved source — the
Bianchi identity forces ∂_μT^μν = 0. The external-reservoir mode is therefore not an
approximation but a deliberate fiction, retained only because the specification asked for it.

### The quadrupole formula

```
h_ij^TT(t, r) = (2G / c⁴ r) · Λ_ij,kl(n̂) · d²Q_kl/dt² |_(t − r/c)

Q_ij = ∫ ρ(x) (x_i x_j − ⅓ δ_ij |x|²) d³x
```

Luminosity:

```
L_GW = (G / 5c⁵) ⟨ d³Q_ij/dt³ · d³Q_ij/dt³ ⟩
```

*Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eqs. 2 (strain), 3 (moment),
4 (luminosity); TT projector at Flanagan & Hughes, New J. Phys. 7:204 (2005),
eq. 4.22 — **VERIFIED** 2026-07-26*

### 2.1 Analytic derivatives of the quadrupole moment (derived)

For point masses, `rho(x,t) = sum_A m_A delta^3(x - x_A(t))`, Blanchet eq. (3) becomes
`Q_ij = sum_A m_A (x_i x_j - (1/3) delta_ij |x|^2)`. Differentiating in time:

```
Qdd_ij  = sum_A m_A ( a_i x_j + 2 v_i v_j + x_i a_j )
          - (2/3) delta_ij sum_A m_A ( v.v + x.a )

Qddd_ij = sum_A m_A ( j_i x_j + 3 a_i v_j + 3 v_i a_j + x_i j_j )
          - (2/3) delta_ij sum_A m_A ( 3 v.a + x.j )
```

Claim **B-6** in [`CLAIMS.md`](CLAIMS.md).

> **Reducing limit → A-3.** For an equal-mass circular binary, the luminosity assembled from
> this `Q⃛` via [B] eq. (4) must reproduce the independently-known closed form
> `L = (32/5)(G/c⁵) μ²a⁴ω⁶`. It does, to **4.1e-16** — an exact algebraic identity, so the
> agreement tests the derivation rather than a discretization.

**Validation (2026-07-26).** Both confirmed on an equal-mass circular binary. `Qdd` agrees with a
central difference to 2.5e-6. `Qddd` agrees to 8.0e-7 at optimal step `h = 1e-3`; more decisively,
the luminosity built from `Qddd` via eq. (4) reproduces the independent closed form
`L = (32/5)(G/c^5) mu^2 a^4 omega^6` to **4.1e-16** — an exact algebraic identity, which is far
stronger evidence than any finite-difference comparison.

**Why finite differences are forbidden here — measured.** Third-derivative central differences are
roundoff-dominated as `eps/h^3`. Relative error against the analytic form:

| step `h` | 1e-6 | 1e-5 | 1e-4 | **1e-3** | 1e-2 | 1e-1 |
|---|---|---|---|---|---|---|
| rel. err | 1.1e+2 | 1.1e-1 | 5.3e-5 | **8.0e-7** | 6.9e-5 | 6.9e-3 |

The classic U-curve: roundoff dominates below `h ~ 1e-4`, truncation above. At `h = 1e-6` the
finite difference is wrong by a factor of 100. This is the concrete justification for the
analytic-derivative rule in [`../CLAUDE.md`](../CLAUDE.md) and `code-reviewer.md`.

**Implementation note:** the luminosity needs the *third* time derivative. Finite differencing
at that order amplifies noise catastrophically, so `Q̈` and `Q⃛` are computed **analytically**
from positions, velocities, and accelerations. Never numerically.

---

## 3. Spherical bodies: the degeneracy that shapes the API

The trace-free quadrupole moment of a spherically symmetric body **about its own center is
exactly zero**. All the mass distribution's angular structure cancels.

So for a *rigid uniform* sphere, the only quadrupole is that of its center-of-mass position:

```
Q_ij = M (x_i x_j − ⅓ δ_ij |x|²),        M = (4/3)πR³ρ
```

**Consequence:** radius and density enter only through `M`. A UI exposing R and ρ as
independent knobs, on this model, would be exposing knobs that do nothing. The degeneracy is
broken only by:

1. **Elastic deformation under acceleration** — a real sphere deforms, acquiring an induced
   quadrupole set by its Love number k₂ and rigidity μ. *This is where R and ρ genuinely
   separate.*
2. **Finite-size retardation** — when R/λ is not small, the long-wavelength expansion fails and
   higher multipoles enter.
3. **Rotational oblateness** — spin flattening produces a static quadrupole available for
   modulation.

### 3.1 Derivation of the degeneracy (claim B-2)

Split each mass element's position into the body's center of mass and an offset,
`x = x_c + y`, and let the density be **any** function of `|y|` alone — the result below needs
radial symmetry, not uniformity. Three terms appear in `Q_ij`:

**Self term.** Using the angular average `∫dΩ n̂_i n̂_j = (4π/3) δ_ij`,

```
∫ ρ(|y|) y_i y_j d³y = ⅓ δ_ij ∫ ρ(|y|) |y|² d³y
```

so the trace-free combination cancels **identically**:

```
Q_ij^self = ⅓ δ_ij ∫ρ|y|² d³y  −  ⅓ δ_ij ∫ρ|y|² d³y  =  0
```

**Cross terms.** `∝ ∫ ρ(|y|) y_i d³y = 0`, by the definition of the center of mass.

**What survives** is the parallel-axis term alone:

```
Q_ij = M (x_c,i x_c,j − ⅓ δ_ij |x_c|²),        M = ∫ρ d³y = (4/3)πR³ρ  (uniform)
```

The internal structure has dropped out exactly. Radius and density reach the radiation **only**
through the product `M`, which is claim B-2.

> **Reducing limit → A-2.** Substituted into [B] eq. 2, a rigid radial body radiates *exactly*
> as a point mass of the same `M` on the same trajectory — i.e. it reduces to the point-mass
> quadrupole of A-2/B-6 with no correction term at any order in `R`. This is the sharpest
> possible form of the reduction: not "approaches", but "equals".
>
> **Measured** (R2–R6 campaign, 2026-08-03): holding `M` fixed and varying `R` over two decades,
> the rigid model's radiation differs by **identically 0.0** at all nine radii, while the elastic
> model over the same span varies by 7.6e4–2.1e5×. The degeneracy and its breaking are visible
> in the same experiment.

**The three breaking mechanisms, and where each is derived.** All three are now implemented and
validated, so B-2 is complete rather than a scoping statement:

| Mechanism | Breaks degeneracy via | Where |
|---|---|---|
| Elastic deformation | `Q ∝ k₂R⁵`, density through `μ̃ = 19μ/(2ρgR)` | `bodies/elastic.py`, EQ-027/EQ-028 |
| Finite-size retardation | **radius only** — the form factor is geometric, `ρ` does not enter | claim B-7, [ADR-0007](adr/0007-uniform-sphere-quadrupole-form-factor.md) |
| Rotational oblateness | spin flattening, a static quadrupole available for modulation | `bodies/` oblateness (T-4.6) |

⚠️ B-7's form factor `1 − 5(kR)²/98` is derived for a **volume-filling** `l=2` profile. A
*surface* profile gives `1 − (kR)²/14`, 40% larger, so it must **not** be carried over to the
elastic or oblateness mechanisms without re-deriving.

---

## 4. Finite maneuvers and memory

A "finite maneuver" is a non-impulsive acceleration profile: smooth, bounded, of finite
duration. Two consequences.

**Spectral content is set by profile smoothness.** This is the same mathematics as radar pulse
shaping: a bang-bang acceleration profile is a rectangular window (−13 dB sidelobes); a
raised-cosine profile is a Hann window. The acceleration profile *is* the transmit pulse shape.

**Linear memory.** A body that accelerates from rest to velocity **v** and stops leaves a
permanent strain offset — the waveform does not return to zero:

```
Δh_ij^TT = (4G / c⁴ r) · Λ_ij,kl · Δ[ Σ_A M_A v_A^k v_A^l ]     (non-relativistic)
```

*Source: Favata, M., Class. Quantum Grav. **27**:084036 (2010), arXiv:1003.3486, eq. (10k) —
**VERIFIED** 2026-07-31 (EQ-026), in the non-relativistic limit stated below*

**What was dropped, and why.** Favata's eq. (10k) is the full Liénard–Wiechert result and carries
two relativistic factors per body: the Lorentz factor `1/√(1−v²/c²)` **and** a beaming factor
`1/(1−v·N̂)`. Both are dropped above. At this project's velocities (`v/c ~ 1e-5`) each differs
from 1 at the ~1e-10 level. Favata also writes the projection as `[…]^TT` where we write
`Λ_ij,kl`; these are the same operation. The dropped beaming factor was **absent from this
project's own original specification of the formula too**, so recording it corrects the spec, not
merely the code — see the assumption ledger in [`INDEX.md`](INDEX.md).

**Historical provenance, not citation.** Zel'dovich & Polnarev (1974) and Braginsky & Thorne,
*Nature* **327**:123 (1987) are where this effect enters the literature, and the memory term is
still commonly called Braginsky–Thorne. The 1987 paper is a *Nature* letter with **no numbered
equations** and therefore does not meet this project's citation bar (rule 1); it is retained in
the reference list as provenance only. Cite Favata.

This is the characteristic signature of a finite maneuver and is directly what the kickoff
specification's requirement 2 asks for.

---

## 5. Phased arrays for a spin-2 field

The standard array factor, identical in form to the radar case:

```
AF(n̂) = Σ_n w_n exp[ i ( k · r_n + φ_n ) ],    k = (2π/λ) n̂
```

with the familiar constraints:

```
Grating-lobe-free:   d ≤ λ / (1 + |sin θ_max|)
Beamwidth (uniform): θ_3dB ≈ 0.886 λ / (N d)
```

*Source: Orfanidis, S.J., **Electromagnetic Waves and Antennas** (open access,
www.ece.rutgers.edu/~orfanidi/ewa), ch. 19 — array factor **eq. (19.4.1)**; grating-lobe bound
**eq. (19.9.6)**; 3 dB beamwidth **eq. (19.7.6)**. **VERIFIED** (EQ-016, EQ-015, EQ-017)*

Orfanidis replaces the Balanis chapter reference this section previously carried: a chapter is
not a citation (rule 1), and Balanis's equation numbers could not be confirmed without the book.
Orfanidis is open access, so a contributor in 2075 can still check these three numbers.

⚠️ **Axis-convention trap — a real one, flagged by `researcher`.** Orfanidis eq. (19.9.6) is
written `d < λ / (1 + |cos φ₀|)`, with `φ₀` measured **from the array axis**. `gwtb` measures the
scan angle from **broadside**, the complementary angle, so `cos φ₀ = sin θ_scan`. The form printed
above is that substitution and nothing more — not a re-derivation, and not an independent result.
See `array/grating.py`'s module docstring.

⚠️ **All three are spin-1 results, and they are used here only as the scalar baseline** —
element *geometry* and *phasing*, never polarization. Everything about how the radiated field
actually combines is below, and is spin-2.

### Where radar intuition breaks

This is the project's genuine research contribution, and its highest-risk area.

| Property | EM (spin-1) | GW (spin-2) |
|---|---|---|
| Polarization rotation about propagation axis | e^(iψ) | **e^(2iψ)** |
| Angle between polarization states | 90° | **45°** |
| Element pattern | dipole | **quadrupole** |
| Superposed quantity | scalar amplitude (per pol.) | **tensor h_ij after TT projection** |

Quadrupole element patterns:

```
Rotating quadrupole:  h₊ ∝ (1 + cos²θ)/2 ,  h× ∝ cos θ
Linear oscillation:   h₊ ∝ sin²θ
```

**Consequence:** array gain is *not* simply N². Elements of differing orientation suffer
polarization-mismatch loss, and superposition must be performed on the TT-projected tensor
along the common observation direction — never on scalar amplitudes.

Any code adapted from antenna, radar, or acoustics libraries implements the spin-1 column of
that table and will produce plausible, wrong numbers.

### 5.1 Derivation of spin-2 array synthesis (claim B-1)

Full record: [ADR-0003](adr/0003-spin2-superposition.md) (SPIKE-4.4), amended 2026-08-03.

**Step 1 — the sum is a vector sum in a 2-D polarization space, not a scalar sum.** For `N`
elements observed along a common `n̂`, superposition (exact, by §1's linearity) gives

```
h_ij^TT(n̂) = Σ_n Λ_ij,kl(n̂) · h_kl^(n) · e^(iφ_n)
```

After TT projection the field has exactly two degrees of freedom, spanned by `e⁺` and `e^×`
([FH] eq. 4.22; components extracted per [B] eqs. 69a–69b). So the sum lives in that plane:

```
(h₊, h_×)_total = Σ_n A_n · (cos 2ψ_n, sin 2ψ_n) · e^(iφ_n)
```

**Step 2 — the factor of 2 is the entire content of the claim.** Writing `h ≡ h₊ − i h_×`, a
rotation by `ψ` about the line of sight acts as `h → h e^(2iψ)` (A-5, Mashhoon & Rahvar eq. 4).
Two elements whose orientations differ by `Δψ` therefore combine with

```
mismatch factor = cos(2Δψ)        — not cos(Δψ)
```

Three consequences, each of which contradicts the spin-1 intuition rather than merely refining it:

| `Δψ` | Spin-2 (correct): `cos(2Δψ)` | Spin-1 (what a radar library would give): `cos(Δψ)` |
|---|---|---|
| 45° | `cos 90° = 0` — **polarization-orthogonal, no interference** | `cos 45° = 0.71`, still substantially coherent |
| 90° | `cos 180° = −1` — **complete destructive cancellation** | `cos 90° = 0` — orthogonal, so powers add *incoherently* to 2× one element |
| any | period **180°** in `ψ` | period 360° |

Read the two columns as mismatch *amplitude* factors. The 90° row is the one that bites: where
EM intuition promises twice the power of a single element, the spin-2 field gives **zero**.

**Step 3 — gain and tolerance.** `|Σ|² = N²|A|²` requires every `ψ_n` equal: **array gain is N²
only for co-oriented elements.** For independent orientation errors of standard deviation `σ`,

```
⟨P⟩/P_max = exp(−4σ²) + (1 − exp(−4σ²))/N
```

The `exp(−4σ²)` is the **`N → ∞` limit**; the second term is an exact, *positive* finite-`N`
bias, so a real array does marginally **better** than the law. The `4σ²` — rather than spin-1's
`σ²` — is the `2ψ` of step 2 entering squared: the relevant phase error is `2σ`, so the
alignment tolerance is **exactly 2× tighter than spin-1**. 1% loss at **σ = 2.87°**.

> **Reducing limit → A-8 and A-5.** Setting all `ψ_n` equal collapses the tensor sum term-for-term
> onto the scalar array factor of A-8 (EQ-016, Orfanidis eq. 19.4.1): the polarization structure
> factors out and the geometry/phasing is recovered unchanged. Independently, the `ψ`-dependence
> reduces to A-5's `e^(2iψ)` rotation law by construction.
>
> **Validated.** Two-element prototype reproduces the hand-derived analytic TT form to **1e-14**
> across nine orientations, and the period in `ψ` is confirmed to be 180°, not 360°
> ([ADR-0003](adr/0003-spin2-superposition.md); committed as
> `test_tt_projection_matches_the_analytic_closed_form` and its production-path counterpart).
> The R2–R6 campaign (2026-08-03) then found `cos(2Δψ)` **exact and N-independent** — max
> deviation 4.5e-14 over `N ∈ {2, 16, 64, 100, 1000}` — with the 90° cancellation complete to
> 3.75e-33 against spin-1's predicted 0.5, and the `exp(−4σ²)` law fitting **201× better** than
> `exp(−σ²)`.

**Provenance caveat on the finite-`N` term.** The random-phasor *skeleton* has a precedent:
D'Addario, L.R., *IPN Progress Report* 42-175, JPL/Caltech (2008), eq. 5, which is algebraically
identical to the expression above. That source is scalar/spin-1 and a technical report, so it
supports the **N-dependence only**. The spin-2 content — that the phase error is `2ψ`, giving
`exp(−4σ²)` — is this project's own derivation and stays in Category B. (Ruze, *Proc. IEEE* 54:633
(1966), proposed as the precedent by `code-reviewer`, gives the `N → ∞` limit **only**; verified
false as a source for the finite-`N` form.)

---

## 6. What a gravitational wave does to an asteroid

Geodesic deviation between nearby free particles:

```
d²ξ_i/dt² = ½ (d²h_ij^TT/dt²) ξ_j
```

*Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 3.11 — **VERIFIED** 2026-08-03
(EQ-045), read directly at source: their eq. (3.11) is `d²Lⁱ/dt² = ½ (d²h^TT_ij/dt²) Lʲ`,
matching the formula above term for term*

[FH] derive it from the geodesic deviation equation (their eq. 3.7) specialized to the linearized
TT-gauge Riemann tensor (their eq. 2.21), in the local proper reference frame of one of the two
masses. The replaced "MTW §37.2" was a chapter reference — not a citation under rule 1, and
unconfirmable without the book. This one was **re-verified independently** in 2026-08-08 (T-13.7)
by a `researcher` pass deliberately not shown the existing reading; it agreed exactly.

Note the gauge subtlety this formula hides: in the TT gauge a free-falling mass sits at **fixed
coordinate position**, so it is the ruler between the masses that changes, not the coordinates of
the masses. The observed displacement follows by time-integration.

**This is a tidal strain, not a net force.** To leading order a GW does not accelerate a free
body's center of mass; it stretches and squeezes it. Net momentum transfer requires *absorption*
of GW energy, and an asteroid's GW absorption cross-section is negligible.

`gwtb` therefore models three coupling channels and reports all three side by side, rather than
assuming radiated power converts to thrust:

1. **Tidal strain** — real, computable, the honest headline number.
2. **Absorption thrust** — momentum flux × absorption cross-section. Expected to be
   vanishingly small; the tool says so quantitatively rather than omitting it.
3. **Near-zone gravitational gradient** — the Lu & Love (2005) gravity tractor mechanism. The
   one gravity-based deflection method that demonstrably works, and therefore the benchmark
   any exotic proposal must beat.

### 6.1 Why radiative coupling cannot compete with the near zone (claim B-5)

Campaign R6 **measured** this ratio at 1.3×10⁻³¹. A measurement is not a derivation, so what
follows is the mechanism — why the sign of the inequality is structural and not a property of the
particular configuration that happened to be run.

**Step 1 — both channels fall as `1/d²`, so distance cancels exactly.** Put a radiating source of
luminosity `L` and a Newtonian attractor of mass `M_s` at the same distance `d` from a target of
mass `M_t` and absorption cross-section `σ`:

```
F_rad  = [ L / (4π d² c) ] · σ          (momentum flux F = P/c, times cross-section)
F_near = G M_s M_t / d²                  (A-10, EQ-023)

F_rad / F_near = L σ / (4π c G M_s M_t)        ← d has cancelled
```

**You cannot fix the radiative channel by moving.** Closing the range helps both channels by
exactly the same factor. This is the same structural cancellation that produces claim B-9, and it
has the same character: an algebraic identity, not a tendency.

**Step 2 — the surviving ratio is `(v/c)⁶`-suppressed.** Substituting the quadrupole luminosity
for a source of mass `M_s`, size `L_s`, and internal speed `v = L_s ω` — `L ~ (G/c⁵) M_s² L_s⁴ ω⁶`
(§2, §8) — the `G` cancels too, and

```
F_rad / F_near  ~  ( σ / 4πL_s² ) · ( M_s / M_t ) · (v/c)⁶
```

Three dimensionless factors, of which the third decides the outcome. **Radiative coupling is
sixth order in `v/c` relative to the near-zone channel.** The reason is countable: `G/c⁵` from the
quadrupole formula, one more `1/c` from `F = P/c`, against the near zone's single power of `G` and
no powers of `1/c` at all. No non-relativistic engineering closes six orders in `v/c` — for the
1 km / 1 kHz rod of §8, `v/c ≈ 1.05×10⁻²` and `(v/c)⁶ ≈ 1.3×10⁻¹²`.

**Step 3 — checked against the measurement, term by term.** R6 compares a radiator at 40 AU
against a 2×10⁴ kg tractor parked 750 m from the asteroid. Decomposing its result:

| Factor | Value |
|---|---|
| Mechanism ratio `Lσ/(4πcG M_s M_t)` (same distance) | 8.367×10⁻¹² |
| Geometric penalty `(750 m / 40 AU)²` | 1.571×10⁻²⁰ |
| **Product** | **1.3143×10⁻³¹** |
| R6's measured `radiative / near-zone` | **1.3143×10⁻³¹** |

Agreement to 3.3×10⁻¹⁶ — floating-point, i.e. the decomposition is exact rather than fitted.
**Most of R6's 31 decades is the geometry of the comparison, not the mechanism**: a tractor flies
to the asteroid while the array stays home. Even stripped of that advantage and compared at equal
distance, the radiative channel still loses by 11 decades; and if the *same* 10⁹ kg body both
radiates and attracts, the same-distance ratio is 1.68×10⁻¹⁶.

*(Reproduce: `tools/run_campaign.py R6`; configuration in `docs/paper/campaign/R6.json`.)*

> **Reducing limit → A-6 and A-10.** As `v/c → 0` at fixed `M_s`, `M_t`, `d`, the ratio → 0 and
> the total coupling reduces to the pure gravity-tractor force `F = GM_sM_t/d²` of A-10 —
> Lu & Love's mechanism, unmodified. That is exactly what A-6 asserts from the other direction: a
> passing GW produces tidal strain, not net center-of-mass acceleration, so in the
> non-relativistic limit the radiative contribution to deflection vanishes and the near-zone term
> is the whole answer.
>
> **Pre-registered falsifier** (R6): *radiative coupling exceeding the near-zone channel at any
> modelled configuration.* It did not fire. Verdict CONFIRMED.

⚠️ **This is a wall, not a bug** (rule 5). B-5 being derived does not make the coupling gap
smaller — it makes it *structural*, which is worse. It is the reason C-4 stays open: A-6 closes
the radiative route, and whether any near-zone alternative scales is still unknown.

---

## 7. Numerical considerations that are physics, not engineering

**Strain magnitude.** h ~ 10⁻⁴⁰ is *subnormal* in IEEE binary32 (smallest normal ≈ 1.18×10⁻³⁸).
All strain is carried in scaled representation (`gwtb.core.units`).

**Phase precision.** Over 40 AU at 1 MHz the accumulated phase is ~2×10¹⁰ wavelengths.
Representing that to useful accuracy requires FP64; binary32's ~10⁻⁷ relative precision cannot.

**The split-phase escape.** Differential path length *across an aperture* scales with aperture
size D, not range r. Computing reference geometry in FP64 and only the differential phase in
FP32 is accurate to ~10⁻⁵ rad for D = 10 km at 40 AU — the standard technique in radio
interferometry and radar correlators. Authorized only in explicitly marked kernels.

---

## 8. The walls

Quantified rather than hidden. Each is a tracked row in the feasibility ledger.

**Diffraction.** Focusing to spot `w` at range `r` requires `D ≳ λr/w`, i.e. aperture measured
in wavelengths:

```
D/λ ≥ 1.029 · r/w = 1.029 × (40 AU)/(1 km) = 6.2 × 10⁹
```

Six billion wavelengths, **at any frequency**. Raising frequency does not relax the ratio — it
shrinks the physical size that ratio corresponds to (1.23×10⁷ AU at 1 Hz; 1.23×10⁴ AU at 1 kHz;
12.3 AU at 1 MHz). Currently the hardest wall.

### 8.1 Derivation of the aperture wall (claim B-3)

The wall is the **algebraic inverse of A-9**, and the coefficient is not decorative. A-9 gives
the −3 dB transverse extent of a uniformly-illuminated circular aperture as

```
w = (2x_h/π) · λr/D = 1.029 · λr/D,    x_h = 1.6163399 solving 2J₁(x)/x = 1/√2
```

Solving for the aperture and dividing by `λ` gives the boxed relation above. The frequency
independence is then immediate: `λ` cancels from both sides, leaving a pure ratio of the range to
the spot size. **`r/w` is the wall; `λ` only sets what that ratio costs in metres.**

⚠️ **Not 1.22.** That is the Rayleigh first-null criterion, a two-source *resolution* limit, not
the −3 dB width. Substituting it would understate the required aperture by 19% — the single
easiest silent error in this section.

> **Reducing limit → A-9.** Constructing an aperture of exactly the derived `D` and passing it
> back through the implementation must return the spot size you asked for. It does, to **zero
> relative error**: `spot_size(D = 1.8459×10¹⁵ m, λ = c/1 kHz, r = 40 AU) = 1000.000000 m`. The
> wall and A-9 are the same statement solved for different unknowns, which is the strongest form
> this reduction can take.
>
> **Corroborated from the other side** (2026-07-31, ADR-0006): the reference aperture
> (`planar_array(8, 8, 1250 m, 1250 m)`, giving `D = 12374.4 m`) sits at
> `r/R_Fraunhofer = 5.86×10⁹` at 1 kHz, with `R_Fraunhofer = 2D²/λ`, and the entire focusing phase
> correction across it is `2πf·D²/(8rc) = 6.70×10⁻¹¹ rad` — **focusing is numerically degenerate
> with steering** at this range
> (`test_focus.py::test_focusing_is_degenerate_with_steering_at_40_au`). Two independent routes,
> the same ~6×10⁹ wall.

**"Numerically degenerate" is meant literally.** The wavefront sag across that aperture is
`D²/(8r) = 3.199×10⁻⁶ m`, while one float64 ULP at 40 AU is `9.77×10⁻⁴ m`. The Fresnel correction
sits **300× below the smallest representable difference in the range itself**: differencing the
per-element ranges directly returns exactly `0.0`. The phase figures above are therefore the
*analytic* `D²/(8r)`, not a measurement — `focal_phases` reports `6.57×10⁻¹¹ rad` here, and that
2% offset is quantization noise rather than a better number. Anything that must resolve focusing
at this range has to be derived analytically and never differenced, which is §2.1's
finite-difference lesson arriving from a different direction.

**The sharper statement.** At the nominal 1 kHz drive that same 12.4 km aperture spans
`D/λ = 0.041` — **sub-wavelength**. There is no beam at all, not merely a poorly-focused one. The
aperture requirement is not "large"; it is unreachable at any GW-plausible frequency for apertures
of this scale, which is why C-3 remains an open conjecture rather than an engineering target.

**Coupling.** §6 — GWs produce strain, not force.

**Magnitude.** For a spinning rod, `P = (2/45)(G/c⁵) M² L⁴ ω⁶`. The ω⁶ scaling makes frequency
the dominant lever by an enormous margin: ~10³⁶ between 1 Hz and 1 MHz operation. Scoping
figures:

| Configuration | P_GW | Momentum flux P/c |
|---|---|---|
| 10 t rod, 10 m, 1 kHz | 7.5×10⁻²⁰ W | 2.5×10⁻²⁸ N |
| 10⁹ kg, 1 km, 1 kHz | 7.5×10⁻² W | 2.5×10⁻¹⁰ N |
| 10⁹ kg, 1 km, 1 MHz | 7.5×10¹⁶ W | 2.5×10⁸ N |

For comparison: a 1 km asteroid (1.4×10¹² kg) needs ~1.4×10¹⁰ N·s for 0.01 m/s — about 43 N
sustained over 10 years. DART delivered ~1.2×10⁷ N·s.

⚠️ **Unreviewed finding, 2026-08-17** ([ADR-0009](adr/0009-magnitude-wall-relativistic-validity.md),
OQ-8): the last row's rod-tip speed is `v = πfL ≈ 3.14×10⁹ m/s ≈ 10.5c` — this formula's own
`v ≪ c` precondition (§2) fails an order of magnitude before this configuration, with the
`v = c` crossover at `f ≈ 95.4 kHz` for `L = 1 km`. Not yet triaged.

**Transducer.** Out of scope by charter (conjecture C-1).

---

## 9. On prime frequencies

Requirement 6 asks for drive frequencies at prime numbers of hertz, so that constructive
interference occurs at a single point rather than as a propagating wavefront.

The underlying intuition is sound and has a well-established analogue: summing N mutually
incommensurate frequencies whose phases coincide at exactly one space-time point is
**mode-locking** — the same physics as a mode-locked laser or pulse-compression radar. Peak
amplitude is N·A at the focus, against a background that §9.1 derives precisely (it is
`0.886√N·A`, not `√N·A`).

Because the incommensurability mechanism works identically at any band, the prime *unit* is a
free parameter in `gwtb` (primes × 1 Hz, × 1 kHz, × 1 MHz, …). Given the ω⁶ scaling, this is
the largest single design lever in the system.

Two honest qualifications, both derived below: **primes are not magic in themselves** — what
matters is a large least common multiple — and **temporal focusing buys peak amplitude, not spot
size.**

### 9.1 Derivation of the prime-comb focus (claim B-4)

**Peak.** At the focus every tone is by construction at zero phase, so `N` unit tones add
coherently: amplitude `N·A`. Away from it the phases are effectively independent and uniformly
distributed, making the sum a 2-D random walk of `N` unit steps — a Rayleigh-distributed
magnitude.

**Background — and a correction to the claim as originally stated.** The Rayleigh *mean* is

```
⟨|Σ|⟩ = √(Nπ)/2 ≈ 0.886 √N       — not √N
```

It is the **peak-to-background ratio** that scales as `√N`, not the background itself. This
0.886 factor is not a rounding detail: the campaign independently reproduced the 12.6% offset
from naive `√N` that ADR-0006 had warned of, matching the Rayleigh-corrected `1.128√N` to 3.1%.

**Recurrence.** Express the tones as integer multiples of a common unit, `f_i = k_i·g`. All
return to zero phase together after `LCM(k_i)/g`. For **distinct primes** the `k_i` are pairwise
coprime, so `LCM = Π k_i` — the product, which is the largest LCM obtainable from a given
frequency budget. *This, and only this, is what primes buy.* They are not otherwise magic; the
requirement is a large LCM, and distinct primes maximize it.

The first ten primes at 1 Hz give `Π pᵢ = 6 469 693 230 s = 205.0 yr`
(`test_recurrence_period_first_10_primes_exact`, rel 1e-12) — the pattern does not repeat within
a human lifetime. The period scales inversely with the unit, so a 1 kHz comb recurs in ~75 days
and a 1 MHz comb in ~1.8 hours: **the frequency lever of §8 and the recurrence period trade
directly against each other.**

> **Reducing limit → A-8.** At `N = 1` the comb collapses to a single tone: peak `= N·A = A`, no
> background to speak of, recurrence period `= 1/f` — the ordinary period. The spatial pattern
> reverts term-for-term to the monochromatic array factor of A-8 (EQ-016), which is the
> single-frequency case the prime construction generalizes.
>
> **Validated** (T-9.6, then R2–R6 2026-08-03): peak `N·A` confirmed at broadside to rtol 1e-6;
> peak-to-background confirmed to scale as `√N` across `N ∈ {16, 64, 100}` with a log–log slope of
> **0.983**. B-4 is fully derived, not partial — the recurrence-period half was closed by T-9.8.

⚠️ **Temporal focusing buys peak amplitude, not spot size.** GWs are non-dispersive in vacuum, so
the focus is a converging-then-diverging pulse rather than a stationary hot spot, and its
transverse extent stays diffraction-limited by §8.1. B-4 does not weaken B-3.

---

## 10. Category B ledger — every derived claim and its reducing limit

[`CLAIMS.md`](CLAIMS.md) requires that each Category B claim "show its derivation in
`PHYSICS.md` and be validated against a limiting case that reduces to Category A." This section
is the index that makes that requirement checkable in one place, and covers **all nine** claims —
not only the B-1…B-5 that existed when T-12.5 was written.

| Claim | Derivation | Reduces to | The limit taken |
|---|---|---|---|
| **B-1** spin-2 array synthesis | §5.1 | A-5, A-8 | All `ψ_n` equal → tensor sum collapses onto the scalar array factor |
| **B-2** mass/radius/density degeneracy | §3.1 | A-2 | Rigid radial body radiates *exactly* as a point mass of equal `M` |
| **B-3** aperture wall `D/λ ≥ 1.029 r/w` | §8.1 | A-9 | Round-trips through `spot_size` to zero relative error |
| **B-4** prime spatiotemporal focus | §9.1 | A-8 | `N = 1` → single tone, ordinary period, monochromatic array factor |
| **B-5** radiative coupling negligible | §6.1 | A-6, A-10 | `v/c → 0` → ratio → 0, leaving the pure gravity-tractor force |
| **B-6** analytic `Q̈`, `Q⃛` | §2.1 | A-3 | Circular binary → closed-form `L = (32/5)(G/c⁵)μ²a⁴ω⁶`, to 4.1e-16 |
| **B-7** finite-size form factor | §10.1 | A-3 | `kR → 0` → `F₂ → 1`, the long-wavelength point quadrupole |
| **B-8** gravitational-focusing miss criterion | §10.2 | elementary two-body mechanics ⚠️ **not a Category A row** | `v∞ ≫ v_esc` → `b_req → R⊕`, the unfocused geometric cross-section |
| **B-9** required luminosity independent of detection distance | §10.3 | A-13, B-8 | `d² ` cancels term-for-term; recovers A-13's `Δv ∝ 1/t` |

### 10.1 Finite-size retardation form factor (claim B-7)

Full record: [ADR-0007](adr/0007-uniform-sphere-quadrupole-form-factor.md), EQ-034, SPIKE-4.5.

Retaining the next order in the long-wavelength expansion of the source integral for a
**volume-filling** `l`-pole radial profile gives

```
F_l(kR) = 1 − (kR)² (l+3) / [ 2(2l+3)(l+5) ] + O((kR)⁴)
F₂(kR) = 1 − 5(kR)²/98                            (l = 2, the mass quadrupole)
```

> **Reducing limit → A-3.** As `kR → 0`, `F₂ → 1` and the quadrupole reverts to the
> point-source form of A-3/B-6. The departure reaches 2.0142% at `R/λ = 0.1`.

⚠️ **Validity floor.** This is a truncated leading-order series, and `1 − 5(kR)²/98` goes
**negative** at `kR = √(98/5) = 4.4272`, i.e. `R/λ = 0.7046`. It must not be evaluated at or
beyond that radius — the sign change is an artifact of the truncation, not physics.

**Admitted to Category B without a citation, deliberately.** No numbered equation for this result
exists in any accessible source (Thorne 1980 is paywalled and its numbering unconfirmed, so it is
cited *without* an equation number, per rule 1). It rests instead on three independent numerical
routes, the strongest agreeing to **1.7e-12**, none of which evaluates a spherical Bessel
function — and the same machinery reproduces the externally-checkable `l=0` result `3j₁(kR)/(kR)`.
Both originally-proposed form factors were confirmed **wrong**: `1/6` is spin-1 `l=0` antenna
machinery (rule 4's trap, nearly implemented as GW physics) and `1/10` is the total-mass monopole.

⚠️ The radial profile is load-bearing: a *surface* profile gives `1 − (kR)²/14`, **40% larger**.
See the warning in §3.1.

### 10.2 Gravitational-focusing miss criterion (claim B-8)

For an unperturbed hyperbolic encounter with Earth, conservation of angular momentum and energy
between infinity and closest approach give

```
angular momentum:   v∞ · b = v_peri · R⊕
energy:             v_peri² = v∞² + v_esc²,      v_esc = √(2GM⊕/R⊕)
```

Eliminating `v_peri` and solving for the impact parameter that just grazes the surface:

```
b_req = R⊕ √( 1 + v_esc²/v∞² )
```

> **Reducing limit.** For `v∞ ≫ v_esc` the square root → 1 and `b_req → R⊕`: a fast object is not
> focused, and the target is simply Earth's geometric disc. Focusing matters exactly where
> intuition says it should — slow encounters.

**Also admitted without a citation, deliberately** — same treatment as B-7. This is elementary
two-body mechanics, but no open source with a citable equation *number* for this exact
combination was found across four documented search attempts (Sprint 14 header,
[`BACKLOG.md`](BACKLOG.md)). A failed citation search recorded as the decision beats a chapter
reference dressed up as one.

⚠️ **B-8 is the one Category B claim that does not reduce to a Category A row**, because no
Category A row states elementary two-body mechanics. [`CLAIMS.md`](CLAIMS.md) previously papered
over this by naming A-6 — the *geodesic-deviation* claim, which concerns GW tidal strain and has
no bearing on a hyperbolic Earth encounter. Corrected 2026-08-10 (T-12.5) and recorded rather
than silently swapped. The honest statement is that the registry's promotion rule has a gap here,
not that B-8 has a reduction it does not have. B-9 inherits the same gap through its dependence
on `b_req`.

### 10.3 Required luminosity is independent of detection distance (claim B-9)

The headline structural result of the deflection tradespace (`target/tradespace.py`, paper §R8).
Chaining the couplings fixed by D-14.2/14.4/14.5 — lead time from radial closing, thrust duration
equal to lead time, absorption sized at the source–target distance:

```
t     = d / v∞                              (lead time from detection distance)
F_req = m · b_req / (k t²)                  (k = 3 secular, 1 impulsive floor)
L_req = F_req · 4π d² c / σ                 (inverting the absorption channel)

⇒  L_req = 4π c · m · b_req · v∞² / (k σ)   ← every d has cancelled
```

Detecting an object **farther away buys a longer lead time and therefore a smaller required force
and Δv — but not a smaller required luminosity.** The inverse-square dilution over the longer path
exactly offsets what the extra time buys. This is the same cancellation structure as B-5 step 1,
and like it, an algebraic identity rather than a fitted tendency.

> **Reducing limit → A-13 and B-8.** `b_req` is B-8's criterion unchanged, and the `1/t²` with
> `k = 3` reproduces A-13's secular `Δv ∝ 1/t` scaling — the relation is built from them and
> collapses back to them.
>
> **Validated:** the 432-cell R8 campaign measured a maximum spread of **3.6×10⁻¹⁵ decades**
> against a pre-registered falsifier bound of 10⁻⁹ decades — eleven orders of magnitude of
> margin, consistent with an identity rather than a measurement. Asserted in
> `tests/unit/test_tradespace.py`, not merely claimed here.

⚠️ **This closes no gap.** The best case anywhere in the 432-cell grid is still short by **29.0
decades**. B-9 tells you that one obvious lever — detect earlier — does not move the requirement
at all, which narrows the search space rather than widening it.

---

## References

**Cited above, with checkable equation numbers.** These are load-bearing; each is open access or
otherwise verifiable without a library.

- **[B]** Blanchet, L., *Living Rev. Relativ.* **17**:2 (2014), arXiv:1310.1528 — eqs. 1, 2, 3, 4,
  69a–69b
- **[FH]** Flanagan, É.É. & Hughes, S.A., *New J. Phys.* **7**:204 (2005), arXiv:gr-qc/0501041 —
  eqs. 3.11, 4.22 *(see [`ERRATA.md`](ERRATA.md) for two verified typos in eqs. 4.41–4.42)*
- Mashhoon, B. & Rahvar, S., *Universe* **9**:6 (2023), arXiv:2211.01691, eq. 4 — the e^(2iψ)
  spin-2 rotation law (A-5)
- Favata, M., *Class. Quantum Grav.* **27**:084036 (2010), arXiv:1003.3486, eq. 10k — linear
  memory (A-7)
- Orfanidis, S.J., *Electromagnetic Waves and Antennas* (open access), ch. 19, eqs. 19.4.1,
  19.7.6, 19.9.6 — scalar array baseline (A-8) ⚠️ spin-1
- Hinderer, T., *ApJ* **677**:1216 (2008), arXiv:0711.2420, eqs. 4–5; Cheng, Lee & Peale,
  *Icarus* **233**:242 (2014), arXiv:1402.0625, eqs. 8–9 — elastic deformation (§3.1)
- Schweickart, Chapman, Durda & Hut, arXiv:physics/0608157 (2006), p.2 — gravity-tractor thrust
  (unnumbered display equation; restates Lu & Love)
- Lu, E.T. & Love, S.G., "Gravitational tractor for towing asteroids," *Nature* **438**:177 (2005)
  — A-10
- Izzo, D., AAS 05-141 (2005), eqs. 2–3 — secular `Δv ∝ 1/t` scaling (A-13)
- D'Addario, L.R., *IPN Progress Report* **42-175**, JPL/Caltech (2008), eq. 5 — finite-`N`
  random-phasor skeleton only ⚠️ spin-1, not peer-reviewed (§5.1)
- Thorne, K.S. & Blandford, R.D., *Modern Classical Physics* ch. 8 (open-access Caltech ph136
  notes) — corroborates the Airy −3 dB width `ρ_FWHM = 1.61633 z/(kR)` (A-9)

**Historical provenance only — cited by name, never as authority for a number.** None of these
carries an equation number this project could confirm; rule 1 excludes them as citations.

- Zel'dovich, Ya.B. & Polnarev, A.G., *Sov. Astron.* **18**:17 (1974); Braginsky, V.B. & Thorne,
  K.S., *Nature* **327**:123 (1987) — where memory enters the literature; **cite Favata** (§4)
- Misner, C.W., Thorne, K.S. & Wheeler, J.A., *Gravitation* (Freeman, 1973) — previously cited for
  §37.2 (geodesic deviation) and §35–36 (spin-2); **both replaced with numbered open sources**
- Balanis, C.A., *Antenna Theory: Analysis and Design*, 4th ed. (Wiley, 2016) — previously cited
  for ch. 6; **replaced by Orfanidis** (§5)
- Maggiore, M., *Gravitational Waves, Vol. 1* (Oxford, 2008); Poisson, E. & Will, C.M., *Gravity*
  (Cambridge, 2014); Goodman, J.W., *Introduction to Fourier Optics*, 3rd ed. (Roberts, 2005);
  Born, M. & Wolf, E., *Principles of Optics* §8.5.2 — standard treatments; equation numbers
  unconfirmed, so A-9 is cited by its reproducible root instead
- Grishchuk, L.P. & Sazhin, M.V., *Sov. Phys. JETP* **38**(2):215 (1974) — the credible prior art
  on deliberately engineered gravitational radiation, per the epistemic firewall in
  [`CLAIMS.md`](CLAIMS.md)
