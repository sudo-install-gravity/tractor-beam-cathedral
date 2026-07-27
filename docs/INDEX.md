# Codebase Index

Maintained by the `indexer` agent. This is the central knowledge store for the project — the
defense against future archaeology. A contributor arriving decades from now should be able to
audit the foundations from here without reverse-engineering the code.

**Last updated:** 2026-07-27 (Sonnet batch, 24/25 tasks — T-4.1/4.2/4.6, T-5.5–5.8, T-6.1–6.4/6.7,
T-8.5, T-9.1–9.4, T-11.1, T-3.8, T-7.4/7.5, T-2.10)

---

## 1. Equation Registry

One row per implemented equation. `Status` mirrors the categories in
[`CLAIMS.md`](CLAIMS.md): `VERIFIED` (citation confirmed by `researcher`), `DERIVED` (our
extension of a cited result), `CONJECTURE` (not yet grounded).

| ID | Equation | Source + eq. no. | Implemented in | Tested by | Status |
|----|----------|------------------|----------------|-----------|--------|
| EQ-001 | Trace-free quadrupole `Q_ij` | [B] eq. 3 | `bodies/multipole.py:quadrupole_moment` | `tests/unit/test_multipole.py` | VERIFIED |
| EQ-002 | Analytic `Q̈_ij` | [B] eq. 3, differentiated | `bodies/multipole.py:quadrupole_second_derivative` | `tests/unit/test_multipole.py` | DERIVED |
| EQ-003 | Analytic `Q⃛_ij` | [B] eq. 3, differentiated | `bodies/multipole.py:quadrupole_third_derivative` | `tests/unit/test_multipole.py` | DERIVED |
| EQ-004 | TT projector `Λ_ij,kl` | [FH] eq. 4.22 (proj. at 4.20) | `propagate/tt_projection.py:tt_projector`, `apply_tt` | `tests/unit/test_tt_projection.py` | VERIFIED |
| EQ-005 | Quadrupole strain `h_ij^TT` | [B] eq. 2 | `source/quadrupole.py:strain_tt` | `tests/benchmarks/test_binary.py` | VERIFIED |
| EQ-006 | GW luminosity `F` | [B] eq. 4 | `source/quadrupole.py:luminosity` | `tests/benchmarks/test_binary.py` | VERIFIED |
| EQ-007 | Circular-binary amplitude | [FH] eq. 4.43 | *(benchmark only)* | `tests/benchmarks/test_binary.py` | VERIFIED |
| EQ-008 | Sphere mass `M = (4/3)πR³ρ` | Fitzpatrick, *Newtonian Dynamics*, eq. 1361 | `bodies/sphere.py:Sphere.mass` | `tests/unit/test_sphere.py` | VERIFIED |
| EQ-009 | Sphere moment of inertia `I = (2/5)MR²` | Fitzpatrick, *Newtonian Dynamics*, eq. 1361 | `bodies/sphere.py:Sphere.moment_of_inertia` | `tests/unit/test_sphere.py` | VERIFIED |
| EQ-010 | Sphere self-quadrupole (vanishes at own centroid) | [B] eq. 3, evaluated at `x=0` | `bodies/sphere.py:Sphere.self_quadrupole` | `tests/unit/test_sphere.py` | DERIVED |
| EQ-011 | Maclaurin-spheroid slow-rotation flattening `ε=(5/4)m` | Fitzpatrick, *Theoretical Fluid Mechanics*, eq. 2.130 | `bodies/sphere.py:oblateness_quadrupole` | `tests/unit/test_sphere.py` | VERIFIED |
| EQ-012 | Rotational-oblateness quadrupole `Q_zz ≈ -(1/3)Ω²R⁵/G` | This project's own derivation from EQ-011 + uniform-ellipsoid inertia + ADR-0002 §6 trace-free convention | `bodies/sphere.py:oblateness_quadrupole` | `tests/unit/test_sphere.py` | DERIVED |
| EQ-013 | Array-factor element-position convention | Orfanidis, *EM Waves and Antennas*, ch. 19, eq. 19.4.1 | `array/geometry.py:linear_array`, `planar_array` | `tests/unit/test_geometry.py` | VERIFIED |
| EQ-014 | Sparse/thinned uniform-disk array layout | This project's own construction, eq. n/a (no external equation exists; Orfanidis ch. 19 discusses sparse arrays only qualitatively) | `array/geometry.py:sparse_array` | `tests/unit/test_geometry.py` | CONJECTURE |
| EQ-015 | No-grating-lobe spacing bound | Orfanidis, *EM Waves and Antennas*, ch. 19, eq. 19.9.6 (converted from array-axis to broadside scan-angle convention — see module docstring, a flagged axis-convention trap) | `array/grating.py:max_spacing`, `has_grating_lobes` | `tests/unit/test_grating.py` | VERIFIED |
| EQ-016 | Scalar array factor `AF = Σ wₙ exp(i k·rₙ)` | Orfanidis, *EM Waves and Antennas*, ch. 19, eq. 19.4.1 | `array/beamform.py:array_factor`, `steering_phases` | `tests/unit/test_beamform.py`, `tests/benchmarks/test_array_factor.py` | VERIFIED |
| EQ-017 | 3 dB beamwidth `θ₃dB ≈ 0.886λ/(Nd)` | Orfanidis, *EM Waves and Antennas*, ch. 19, eq. 19.7.6 | `array/beamform.py:beamwidth_3db` | `tests/unit/test_beamform.py` | VERIFIED |
| EQ-018 | Peak sidelobe level (uniform array, −13.2 dB) | Orfanidis, *EM Waves and Antennas*, ch. 19, eq. 19.7.6 (derived region between 19.7.6 and 19.8.1) | `array/beamform.py:peak_sidelobe_level` | `tests/unit/test_beamform.py` | VERIFIED |
| EQ-019 | Dolph-Chebyshev / Taylor amplitude tapers | Dolph, *Proc. IRE* 34(6), 335 (1946); Taylor, *IRE Trans. Antennas Propag.* 3(1), 16 (1955) — in-paper eq. numbers unconfirmed, implemented via `scipy.signal.windows` | `array/beamform.py:taper` | `tests/unit/test_beamform.py` | VERIFIED (construction); eq. numbers themselves UNVERIFIED — flag if used for a numeric claim beyond SciPy's own docs |
| EQ-020 | Per-source retarded-time superposition `h_ij(x,t) = Σ strain_tt(...)` | [B] eq. 2, applied per-source at its own retarded time | `propagate/retarded.py:field_at`, `PointSource` | `tests/unit/test_retarded.py` | DERIVED |
| EQ-021 | Prime-frequency comb / recurrence period `LCM(k_i)/g` | This project's own construction, eq. n/a — kinematic/DSP design choice, exempt from citation-CI (BACKLOG T-9.2) | `kinematics/oscillators.py:first_n_primes`, `prime_frequencies`, `recurrence_period`, `PrimeOscillatorDrive` | `tests/unit/test_oscillators.py` | CONJECTURE (design choice, not a physics claim) |
| EQ-022 | Symmetric two-body momentum-conserving maneuver waveform | [B] eq. 3 (quadrupole 2nd derivative), applied to this project's own symmetric-two-body modeling choice (see Assumption Ledger) | `source/quadrupole.py:waveform_from_profile` | `tests/unit/test_waveform_from_profile.py` | DERIVED |
| EQ-023 | Gravity-tractor Newtonian point-mass thrust `F = GMm/d²` | Schweickart, Chapman, Durda & Hut, B612 Foundation White Paper 042, arXiv:physics/0608157 (2006), p.2 §II (unnumbered display eq., restates Lu & Love, *Nature* 438, 177 (2005)); worked example checked against Fig. 2 (p.9) | `target/coupling.py:channel_gravity_tractor` | `tests/unit/test_coupling.py` | VERIFIED (content); eq. is unnumbered in the source — see Assumption Ledger note on point-mass approximation |

**Citations verified 2026-07-26** for all Sprint 1 equations (EQ-001–007); **2026-07-27** for
the Sprint 4/5/9/6/11/3/8/2 additions above (EQ-008–023). Sources are open access with
checkable equation numbers except where flagged (EQ-014, EQ-019 in-paper numbers, EQ-021,
EQ-023 unnumbered display):

- **[B]** Blanchet, *Living Rev. Relativ.* **17**:2 (2014), arXiv:1310.1528
- **[FH]** Flanagan & Hughes, *New J. Phys.* **7**:204 (2005), arXiv:gr-qc/0501041
- **Fitzpatrick** Richard Fitzpatrick, *Newtonian Dynamics* and *Theoretical Fluid Mechanics*
  (open-access lecture notes, farside.ph.utexas.edu) — used only where the exact equation
  number is confirmable on the linked page.
- **Orfanidis** S. J. Orfanidis, *Electromagnetic Waves and Antennas* (open-access,
  www.ece.rutgers.edu/~orfanidi/ewa), ch. 19 "Antenna Arrays" — this is a **spin-1 (scalar EM
  antenna) reference by construction**; see CLAUDE.md rule 4 and `array/beamform.py`'s own
  docstring, which explicitly flags itself as the scalar baseline, not gravitational-radiation
  physics. Never cite it for a spin-2 tensor result.
- **Dolph (1946) / Taylor (1955)** — cited via `scipy.signal.windows`; **in-paper equation
  numbers are unconfirmed** (EQ-019). Flag before treating a specific numbered equation from
  either paper as checked.
- **Schweickart, Chapman, Durda & Hut (2006)**, arXiv:physics/0608157 — gravity-tractor
  concept paper; its central formula is an **unnumbered display equation** (EQ-023), restating
  Lu & Love 2005. Treat "eq. n/a" as the accurate citation, not a defect to fix.

**Textbook citations were rejected during verification** for Sprint 1 (Maggiore, MTW —
equation numbers unconfirmable without the physical books). Fitzpatrick's online lecture notes
were accepted for Sprint 4 because the exact equation number is visible and checkable at the
linked URL — this is the same open-access-checkability bar, not an exception to it.

⚠️ **[FH] eqs. (4.41) and (4.42) contain typos.** See [`ERRATA.md`](ERRATA.md) ERR-001/ERR-002.
The derivations we rely on ([FH] 4.17–4.23) are correct; only the worked binary example is
affected.

⚠️ **Benchmark substitution, flagged per CLAUDE.md "make absence loud":**
`tests/benchmarks/test_array_factor.py` (T-6.9) was specified to compare against `arraytool`
output; `arraytool` is not installable in this offline environment (see CLAUDE.md
"Environment note"). It instead compares against the closed-form analytic uniform-linear-array
factor. Recorded here, not silently substituted — re-run against real `arraytool` output if/when
network access is available.

---

## 2. Module Map

| Module | Purpose | Public API | Depends on |
|---|---|---|---|
| `core/constants.py` | Physical constants with sources | **live** — `G`, `c`, `AU`, `M_SUN`, `PARSEC`, `G_OVER_C4/5`, `TARGET_RANGE` | — |
| `core/units.py` | Scaled strain representation | **live** — `StrainScale` | `constants` |
| `core/backend.py` | Array-API shim (numpy / numba) | **live** — `get_backend`, `Backend` (T-11.1; no citation requirement, infrastructure only). Downstream kernels that actually use a non-numpy backend are T-11.2+, not yet built | — |
| `bodies/sphere.py` | Rigid uniform sphere; mass/inertia; rotational-oblateness quadrupole | **live** — `Sphere` (dataclass: `radius`, `density`, `.mass`, `.moment_of_inertia`, `.self_quadrupole()`), `oblateness_quadrupole` (T-4.1/4.2/4.6) | `constants` |
| `bodies/elastic.py` | Love-number deformation; breaks R/ρ degeneracy | *(Sprint 4, not yet implemented)* | `sphere` |
| `bodies/multipole.py` | Mass multipole moments and derivatives | **live** — `quadrupole_moment`, `_second_derivative`, `_third_derivative` | `constants` |
| `kinematics/profiles.py` | Finite-maneuver acceleration profiles | **live** — `AccelerationProfile` (base), helpers `_finish`, `_prepare_time` | — |
| `kinematics/oscillators.py` | Prime-frequency multi-tone drive synthesis | **live** — `first_n_primes`, `prime_frequencies`, `recurrence_period`, `PrimeOscillatorDrive` (T-9.1–9.4; DSP/kinematic module, exempt from citation-CI) | `profiles`, `core/validation` |
| `source/quadrupole.py` | Quadrupole radiation, luminosity, and maneuver waveforms | **live** — `strain_tt`, `luminosity`, `waveform_from_profile` (T-3.8, adds symmetric two-body maneuver modeling) | `multipole`, `tt_projection`, `bodies/sphere`, `kinematics/profiles` |
| `source/multipole_rad.py` | Higher multipoles; dipole term (flagged) | *(Sprint 2, not yet implemented)* | `multipole` |
| `source/memory.py` | Linear GW memory from finite maneuvers | *(Sprint 3, not yet implemented)* | `quadrupole` |
| `source/conservation.py` | ∂_μT^μν audit; `UNPHYSICAL` stamping | *(Sprint 2, not yet implemented)* | — |
| `propagate/tt_projection.py` | Transverse-traceless projector | **live** — `tt_projector`, `apply_tt`, `transverse_projector` | — |
| `propagate/polarization.py` | Spin-2 basis; e^(2iψ) rotation | *(Sprint 5, not yet implemented)* | `tt_projection` |
| `propagate/retarded.py` | Per-source retarded-time field evaluation | **live** — `PointSource` (dataclass), `field_at` (T-6.7; retards each source individually — see module docstring on why a shared array-centroid retardation would be wrong) | `source/quadrupole`, `core/constants` |
| `array/geometry.py` | Element placement | **live** — `linear_array`, `planar_array`, `sparse_array` (T-5.5–5.7) | — |
| `array/beamform.py` | Scalar array factor, steering, beamwidth/sidelobes, tapering | **live** — `array_factor`, `steering_phases`, `beamwidth_3db`, `peak_sidelobe_level`, `taper` (T-6.1–6.4). **Explicitly the spin-1/scalar baseline** — see module docstring warning; the spin-2 tensor superposition `superpose_tt` (T-6.5) is not yet implemented | `geometry`; tensor superposition (not yet built) will depend on `polarization` |
| `array/grating.py` | Grating-lobe and spacing constraints | **live** — `max_spacing`, `has_grating_lobes` (T-5.8) | `geometry` |
| `array/focus.py` | Spatiotemporal focusing | *(Sprint 9, not yet implemented)* | `beamform` |
| `target/geodesic.py` | Geodesic deviation at the target | *(Sprint 8, not yet implemented)* | `tt_projection` |
| `target/coupling.py` | Non-GW comparison channel: gravity tractor | **live** — `channel_gravity_tractor` (T-8.5; other two momentum-transfer channels from the module's original scope not yet implemented) | `constants` |
| `target/deflection.py` | Orbit propagation; Δv → miss distance | *(Sprint 8, not yet implemented)* | `coupling` |
| `ledger/gap_report.py` | Feasibility ledger | *(Sprint 2, not yet implemented)* | most modules |
| `viz/patterns.py` | Beam-pattern visualization (polar + 3D) | **live** — `plot_pattern_polar`, `plot_pattern_3d` (T-7.4/7.5; headless `Agg` backend; reimplements array-factor math vectorized for full-grid rendering rather than calling `beamform.array_factor` per point — kept numerically consistent by shared test coverage, not by a shared code path) | `array/beamform` (mathematically, not by import) |
| `viz/*` (other) | Field slices, volumetric rendering | *(Sprint 7, not yet implemented)* | — |
| `core/validation.py` | ADR-0002 shape/dtype/unit-vector guards | **live** — `as_masses`, `as_body_array`, `as_tensor_3x3`, `as_unit_vector`, `as_float64` | — |

⚠️ **`array/beamform.py` docstring names a function `superpose_tt` (T-6.5, spin-2 tensor
superposition) as "not yet implemented."** No such function exists anywhere in `array/` at
time of writing. This is correctly flagged in the module itself as a forward reference, not a
vanished-equation finding — but it means **T-6.5 and T-6.6 (spin-2 superposition, the
project's highest-risk bug class per CLAUDE.md rule 4) remain unbuilt and are `opus`-tier**;
do not let the scalar `beamform.py` module be mistaken for that work being done.

---

## 3. Assumption Ledger

**The most valuable section in this index.** Several approximations here hold across most of
the parameter space and fail at its edges — and this project's interesting configurations live
near those edges.

| Assumption | Asserted in | Valid when | Breaks down at |
|---|---|---|---|
| Weak field / linearized gravity | Whole framework | h ≪ 1 | Never violated here (h ~ 10⁻⁴⁰). Safe. |
| Superposition is exact | All array math | Linear regime | Same as above. This is *why* the phased-array approach is legitimate. |
| Far zone (r ≫ λ) | Quadrupole formula, array factor | r/λ ≫ 1 | At 40 AU: r/λ ≈ 2×10⁴ at 1 Hz. Safe at target range; **violated near the array** |
| Long wavelength (R ≪ λ) | Quadrupole approximation | Source size ≪ λ | **Violated for large spheres at high frequency.** Motivates `bodies/` finite-size corrections |
| Slow motion (v ≪ c) | Quadrupole formula, memory | v/c ≪ 1 | Assumed throughout; must be checked per configuration |
| Momentum conservation | Default source mode | Reaction mass in model | **Deliberately violated** in external-reservoir mode; outputs stamped `UNPHYSICAL` |
| Non-dispersive propagation | Focusing analysis | Vacuum GR | Holds in vacuum. Means a temporal focus propagates rather than standing still |
| FP64 sufficient for phase | All field evaluation | — | Adequate to ~10¹⁰ wavelengths. FP32 is **not**; see `PHYSICS.md` §7 |
| Rigid point-mass sphere (no self-quadrupole) | `bodies/sphere.py:Sphere.self_quadrupole` | Rigid, undeformed, non-spinning body; only trajectory radiates | Breaks down once the body deforms (elastic, T-4.3, not yet built) or spins (see next row) |
| Slow-rotation Maclaurin-spheroid flattening (`ε ≪ 1`, i.e. `m = Ω²R³/(GM) ≪ 1`) | `bodies/sphere.py:oblateness_quadrupole` | Spin well below breakup/bifurcation rate | At `m` approaching the Maclaurin sequence's bifurcation point (~0.1875) the leading-order `ε=(5/4)m` formula and this project's own leading-order `Q_zz` conversion both fail; neither is valid near breakup spin |
| Rigid long-wavelength model: radiation depends only on mass and trajectory, not radius/density | `source/quadrupole.py:waveform_from_profile` | `R ≪ λ` (see far-field row above) | Same breakdown as the long-wavelength row; large fast-spinning asteroids at high drive frequency need the T-4.3/4.5 corrections before this holds |
| **Symmetric two-body momentum-conserving maneuver model** — a single accelerating sphere is *represented* as two `body.mass/2` point masses at `±x(t)` along a fixed axis, purely to keep the center of mass fixed and avoid an uncancelled mass dipole | `source/quadrupole.py:waveform_from_profile` | Whenever a single-body finite maneuver is modeled as a radiating source | This is a **modeling choice, not a measurement of a real single accelerating asteroid** — a real single accelerating body pushed by an external force (e.g. thruster) is not momentum-conserving and its true radiation is dominated by the (roughly 10¹⁰×) mass-dipole term per CLAUDE.md rule 2, not this quadrupole. Never present this function's output as the radiation of a *literal* single accelerating asteroid without flagging the substitution |
| Sparse-array layout is uniform-random-in-disk, not physically motivated | `array/geometry.py:sparse_array` | Only as a reproducible construction to probe OQ-4 (sidelobe behavior of thinned arrays) | Not a claim about an optimal or realistic sparse layout — no equation exists to check it against (EQ-014, CONJECTURE) |
| Grating-lobe bound uses broadside scan-angle convention, algebraically converted from Orfanidis's array-axis convention | `array/grating.py` module docstring | Anywhere `max_spacing`/`has_grating_lobes` is called with `scan_angle_max` measured from broadside (the project's standing convention) | If a future caller passes an array-axis-referenced angle instead, the `cos(phi0) = sin(theta_scan)` substitution silently gives the wrong bound — flagged explicitly by `researcher` as a real trap |
| Scalar (spin-1-style) beamforming baseline | `array/beamform.py` (entire module) | As a classical-array-theory reference to validate the not-yet-built spin-2 tensor superposition against, for co-oriented elements | **Must never be read as gravitational-radiation physics directly** — the module's own docstring insists on this. Using its output as a final science result rather than a baseline check would reintroduce the spin-1/spin-2 bug class (CLAUDE.md rule 4) |
| Gravity-tractor treats both tractor and asteroid as point masses | `target/coupling.py:channel_gravity_tractor` | Separation large relative to both bodies' physical extent | Source paper's own worked example uses `separation ~ 1.5 × asteroid_radius` — the point-mass approximation is **not validated by the source at the separations of practical interest**. Ledger note requested explicitly in the module docstring (BACKLOG T-8.5, OQ-5); no quantitative bound has been derived here yet |
| `viz/patterns.py` reimplements the array-factor math vectorized rather than importing `array/beamform.array_factor` | `viz/patterns.py:_array_factor_magnitude` | Kept consistent only by shared test coverage across both modules | If `beamform.array_factor`'s definition (e.g. its wavevector sign convention) ever changes, `patterns.py` will silently diverge unless its own tests are re-run — there is no import-level coupling to catch it |

---

## 4. Validation Status

A benchmark that has not run since the code it validates last changed is **stale**, not
passing.

| Benchmark | Validates | Status |
|---|---|---|
| Circular binary (h₊, h×, L) | EQ-005, EQ-006, EQ-007 | **PASSING** rtol 1e-6 |
| Hulse–Taylor PSR B1913+16 period decay (T-12.2) | EQ-006 (extension) | **BLOCKED, not Ready** — see BACKLOG.md line 772. Needs the Peters (1964) eccentric-orbit decay formula with a pinned, checkable equation number. Two `researcher` passes failed to fetch a primary source (Caltech PDF `ECONNREFUSED`; Blanchet arXiv:1310.1528 PDF text unparseable for this specific equation). PSR B1913+16 system parameters are separately verified via arXiv:1606.04581 (Weisberg & Huang 2016), but implementing the decay-rate formula itself without a pinned eq. number would violate citation discipline (CLAUDE.md rule 1). Escalate to a spike before implementing — **do not implement from memory in the meantime** |
| Spinning rod power | EQ-006 | Not implemented (T-2.8) |
| **Dipole cancellation** | Momentum conservation (decision 1) | **PASSING** — ratio < 1e-12 over 20 seeded configs, plus a positive control > 1e-3. *OQ-1 resolved: the dipole does cancel as expected.* |
| Linear memory (hyperbolic scattering) | `source/memory.py` | Not implemented |
| Array factor vs. reference (T-6.9) | EQ-016 | **PASSING** — via closed-form analytic uniform-array reference, **not** `arraytool` as originally specified (see flag in §1 above; `arraytool` unavailable offline) |
| Diffraction limit `w ≈ λr/D` | `array/focus.py` | Not implemented |
| Energy conservation over distant sphere (T-12.3) | EQ-006 | Not implemented, deps T-6.8 unimplemented |
| Sphere mass/inertia/self-quadrupole (T-4.1/4.2) | EQ-008–010 | **PASSING** — `tests/unit/test_sphere.py` |
| Rotational-oblateness quadrupole (T-4.6) | EQ-011, EQ-012 | **PASSING** — `tests/unit/test_sphere.py` |
| Array geometries (T-5.5–5.7) | EQ-013, EQ-014 | **PASSING** — `tests/unit/test_geometry.py` |
| Grating-lobe bound (T-5.8) | EQ-015 | **PASSING** — `tests/unit/test_grating.py` |
| Beamforming: array factor, steering, beamwidth, sidelobes, taper (T-6.1–6.4) | EQ-016–019 | **PASSING** — `tests/unit/test_beamform.py` |
| Per-source retarded field (T-6.7) | EQ-020 | **PASSING** — `tests/unit/test_retarded.py` (includes the acceptance test distinguishing per-element vs. array-centroid retardation) |
| Prime-oscillator drive (T-9.1–9.4) | EQ-021 | **PASSING** — `tests/unit/test_oscillators.py` |
| Maneuver waveform, symmetric two-body (T-3.8) | EQ-022 | **PASSING** — `tests/unit/test_waveform_from_profile.py` |
| Backend shim (T-11.1) | — (infrastructure, no equation) | **PASSING** — `tests/unit/test_backend.py` |
| Gravity-tractor channel (T-8.5) | EQ-023 | **PASSING** — `tests/unit/test_coupling.py`, worked example checked against source paper Fig. 2 |
| Beam-pattern plots (T-7.4/7.5) | — (visualization, no numbered equation) | **PASSING** — `tests/unit/test_patterns.py` |
| ADR-0002 convention enforcement (T-2.10) | Shape/dtype/unit-vector guards project-wide | **PASSING** — `tests/unit/test_conventions.py`, extended to cover all modules added this batch (`sphere`, `retarded`, `quadrupole.waveform_from_profile`) |

**1 of 25 assigned batch tasks not completed this pass** (per the human's report — task not
specified further; **flagged, not silently dropped**. Confirm which task against
`docs/BACKLOG.md`'s ✅ markers before the next session, since this index cannot itself
determine which one is outstanding without that cross-check).

---

## 5. Open Questions

| ID | Question | Context |
|---|---|---|
| ~~OQ-1~~ | **RESOLVED 2026-07-26** — the dipole cancels to <1e-12 relative in momentum-conserving configurations, confirming decision 1. | |
| OQ-1 (orig) | Does the dipole term cancel numerically to the precision we expect in a momentum-conserving two-body configuration? | Validates the project's central physics framing (decision 1). Scheduled Sprint 1 — pulled forward from Sprint 2 because a surprise here reframes everything downstream |
| OQ-2 | How is polarization-mismatch loss correctly formulated for spin-2 array elements of differing orientation? | No external reference implementation exists. `SPIKE-4.4` (Sprint 2) attacks this early because it sits on the critical path. **Still open** — `array/beamform.py` this batch is explicitly the spin-1 scalar baseline that this spike's answer must reduce to, not an answer itself |
| OQ-3 | At what R/λ does the long-wavelength quadrupole approximation fail badly enough to matter? | Determines whether `bodies/` finite-size corrections are a refinement or a requirement |
| OQ-4 | Is a sparse (non-filled) array viable given the 6×10⁹-wavelength aperture requirement? | Sparse arrays relax element count but raise sidelobes — directly opposed to requirement 6's single-point focus. `array/geometry.py:sparse_array` (this batch) supplies a reproducible layout to test against, but does not itself resolve the question — no sidelobe/viability analysis has been run on it yet |
| OQ-5 | Does the near-zone gradient channel (Lu & Love) scale to anything useful at 40 AU? | If not, conjecture C-4 has no candidate mechanism. `target/coupling.py:channel_gravity_tractor` (this batch) implements the comparison channel itself but does not resolve OQ-5's point-mass-approximation caveat — see Assumption Ledger |
| OQ-6 (new) | What equation number pins the Peters (1964) eccentric-orbit GW decay formula to an openly checkable primary source? | Blocks T-12.2 (Hulse–Taylor benchmark). Two `researcher` passes failed (Caltech PDF connection refused; Blanchet PDF text unparseable for this equation). Needs a spike with different network/library access, or a from-scratch derivation from already-cited multipole formulas |

---

## Maintenance rules

- Never let the Equation Registry drift from the code. A citation in a docstring but not the
  registry gets added; a registry row pointing at a function that no longer exists gets
  **flagged loudly**, not deleted. A vanished equation is a finding.
- Cross-link to `CLAIMS.md` categories so the two documents cannot disagree.
- Prefer flagging over fixing. When index and code disagree, report the disagreement and let a
  human or a task decide which is wrong.
