# Physics Framework

First-principles derivation of what `gwtb` computes. A contributor should be able to audit the
foundations from this document alone, without reading the code.

**Status: skeleton.** Equations are recorded with their intended sources; each is marked
`[UNVERIFIED]` until the `researcher` agent confirms the exact equation number and conventions.
Nothing here is implemented yet.

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

*Source: MTW ch. 18 / Maggiore Vol. 1 ch. 1 — `[UNVERIFIED]`*

---

## 2. Why the leading radiation is quadrupolar — and why this constrains the whole design

Expanding the retarded integral in multipoles:

- **Mass monopole** — total mass-energy, conserved. `d²M/dt² = 0`. **No radiation.**
- **Mass dipole** — `d_i = ∫ρ x_i d³x` is the center of mass. Its second derivative is
  `dP_i/dt`, the net external force. For an isolated system momentum is conserved, so
  **no radiation.**
- **Mass quadrupole** — first non-vanishing term.

*Source: MTW §36.1 / Maggiore Vol. 1 §3.3 — `[UNVERIFIED]`*

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

*Source: Maggiore Vol. 1 ch. 3 — `[UNVERIFIED]`*

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

*Claim B-2 in [`CLAIMS.md`](CLAIMS.md). Derivation pending.*

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

*Source: Zel'dovich & Polnarev (1974); Braginsky & Thorne, Nature 327:123 (1987) — `[UNVERIFIED]`*

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

*Source: Balanis, Antenna Theory ch. 6 — `[UNVERIFIED]`*

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

*Claim B-1 in [`CLAIMS.md`](CLAIMS.md). Derivation pending.*

---

## 6. What a gravitational wave does to an asteroid

Geodesic deviation between nearby free particles:

```
d²ξ_i/dt² = ½ (d²h_ij^TT/dt²) ξ_j
```

*Source: MTW §37.2 — `[UNVERIFIED]`*

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
D/λ ≳ r/w = (40 AU)/(1 km) = 6 × 10⁹
```

Six billion wavelengths, **at any frequency**. Raising frequency does not relax the ratio — it
shrinks the physical size that ratio corresponds to (1.2×10⁷ AU at 1 Hz; ~12 AU at 1 MHz).
Currently the hardest wall.

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

**Transducer.** Out of scope by charter (conjecture C-1).

---

## 9. On prime frequencies

Requirement 6 asks for drive frequencies at prime numbers of hertz, so that constructive
interference occurs at a single point rather than as a propagating wavefront.

The underlying intuition is sound and has a well-established analogue: summing N mutually
incommensurate frequencies whose phases coincide at exactly one space-time point is
**mode-locking** — the same physics as a mode-locked laser or pulse-compression radar. Peak
amplitude is N·A at the focus against ~√N·A elsewhere.

Two honest qualifications:

**Primes are not magic in themselves.** What matters is a large least common multiple, so the
pattern does not recur. Distinct primes maximize LCM for a given frequency budget, which is a
real and good reason to choose them. The first ten primes (2…29 Hz) give a recurrence period of
Π pᵢ = 6.47×10⁹ s ≈ **205 years** — the interference pattern does not repeat within a human
lifetime.

**Temporal focusing buys peak amplitude, not spot size.** Gravitational waves are non-dispersive
in vacuum, so the focus is a converging-then-diverging pulse rather than a stationary hot spot,
and its transverse extent remains diffraction-limited per §8.

Because the incommensurability mechanism works identically at any band, the prime *unit* is a
free parameter in `gwtb` (primes × 1 Hz, × 1 kHz, × 1 MHz, …). Given the ω⁶ scaling, this is
the largest single design lever in the system.

*Claim B-4 in [`CLAIMS.md`](CLAIMS.md). Derivation pending.*

---

## References

- Misner, C.W., Thorne, K.S. & Wheeler, J.A., *Gravitation* (Freeman, 1973)
- Maggiore, M., *Gravitational Waves, Vol. 1: Theory and Experiments* (Oxford, 2008)
- Poisson, E. & Will, C.M., *Gravity: Newtonian, Post-Newtonian, Relativistic* (Cambridge, 2014)
- Balanis, C.A., *Antenna Theory: Analysis and Design*, 4th ed. (Wiley, 2016)
- Goodman, J.W., *Introduction to Fourier Optics*, 3rd ed. (Roberts, 2005)
- Zel'dovich, Ya.B. & Polnarev, A.G., *Sov. Astron.* **18**:17 (1974)
- Braginsky, V.B. & Thorne, K.S., *Nature* **327**:123 (1987)
- Grishchuk, L.P. & Sazhin, M.V., *Sov. Phys. JETP* **38**(2):215 (1974)
- Lu, E.T. & Love, S.G., "Gravitational tractor for towing asteroids," *Nature* **438**:177 (2005)
