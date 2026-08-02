# Codebase Index

Maintained by the `indexer` agent. This is the central knowledge store for the project — the
defense against future archaeology. A contributor arriving decades from now should be able to
audit the foundations from here without reverse-engineering the code.

**Last updated:** 2026-07-27 (Sonnet batch, 24/25 tasks — T-4.1/4.2/4.6, T-5.5–5.8, T-6.1–6.4/6.7,
T-8.5, T-9.1–9.4, T-11.1, T-3.8, T-7.4/7.5, T-2.10)

**Updated 2026-07-31:** added T-6.8 (`propagate()`, EQ-024) and T-11.2 (`field_grid`,
EQ-025), including the `field_grid` light-crossing-time scope restriction in the Assumption
Ledger.

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
| EQ-024 | Batched per-source retarded-time superposition over a grid of field points and times | [B] eq. 2 (same formulation as EQ-020, batched) | `propagate/retarded.py:propagate` | `tests/unit/test_retarded.py` | DERIVED |
| EQ-025 | TT-strain superposition kernel, single evaluated `q_ddot` per source shared across a field-point grid | [B] eq. 2, applied under the light-crossing-time restriction noted in the function docstring and the Assumption Ledger | `core/backend.py:field_grid`, `_field_grid_loop` | `tests/unit/test_backend.py` | DERIVED |
| EQ-026 | Linear (Braginsky–Thorne) memory `Δh_ij^TT = (4G/c⁴r) Λ_ij,kl Δ[Σ_A M_A v^k v^l]` | Favata, *Class. Quantum Grav.* 27:084036 (2010), arXiv:1003.3486, eq. 10k — **non-relativistic limit**: the printed equation carries a per-body Lorentz factor `1/√(1−v²)` *and* a beaming factor `1/(1−v·N)`, both dropped here (→1 at `v/c ~ 1e-5`). Favata writes the projection `[…]^TT`, not `Λ_ij,kl` | `source/memory.py:linear_memory` | `tests/unit/test_memory.py`, `tests/benchmarks/test_memory.py` | VERIFIED (in the stated limit) |
| EQ-027 | Tidal-induced quadrupole `Q_ij = −(2/3)(k₂R⁵/G) E_ij` | Hinderer, *ApJ* 677:1216 (2008), arXiv:0711.2420, eq. 4 (`Q_ij = −λE_ij`) and eq. 5 (`k₂ = (3/2)GλR⁻⁵`). Source states `c=G=1` generally but **prints eq. 5 with G explicit**, so the SI form needs no hand-reinserted factor | `bodies/elastic.py:induced_quadrupole` | `tests/unit/test_elastic.py` | VERIFIED |
| EQ-028 | Rigidity-dependent Love number `k₂ = (3/2)/(1+μ̃)`, `μ̃ = 19μ/(2ρgR)` | Cheng, Lee & Peale, *Icarus* 233:242 (2014), arXiv:1402.0625, eq. 8 and eq. 9. Traces to Munk & MacDonald (1960) §5.6 and Peale (1973); the arXiv reproduction is cited because its equation numbers are checkable | `bodies/elastic.py:love_number_k2` | `tests/unit/test_elastic.py` | VERIFIED |
| EQ-029 | Array focusing phase law `φ_a(f) = 2πf(R_a/c − t_focus)` | [B] eq. 2 (retarded-time relation `t_ret = t − R/c`), **inverted per element** — the inversion is this project's own construction; no GW reference gives an array focusing phase law. Polarization-independent: it concerns propagation delay, not spin-2 structure | `array/focus.py:focal_phases` | `tests/unit/test_focus.py` | DERIVED |
| EQ-030 | Cancellation-free range difference `R_a − R_ref = (\|q_a\|² − 2 s·q_a)/(R_a + R_ref)` | This project's own derivation, eq. n/a — an algebraic identity, not a physics equation. Load-bearing: the direct difference of two ~1e12 m ranges is **identically zero** in float64 at 40 AU, destroying 100% of the signal | `array/focus.py:_differential_range`, `core/backend.py:split_phase` | `tests/unit/test_focus.py`, `tests/unit/test_split_phase.py` | DERIVED |
| EQ-032 | Focused far-field superposition `H_ij(x) = superpose_tt(elements, exp(+i φ_a,f), λ_f, x)` | [ADR-0006](adr/0006-focused-field-far-field-regime.md), eq. n/a — a **composition** of EQ-029 with `superpose_tt`, introducing no new equation. Sign convention `exp(+iφ)` matches `superpose_tt`'s `exp(+i k·r_n)`, pinned empirically at 50 beamwidths off-axis | `array/focus.py:focused_phasor`, `focused_field` | `tests/unit/test_focused_field.py` | DERIVED |
| EQ-033 | Airy −3 dB spot size `w = (2x_h/π) λr/D = 1.0290 λr/D`, `x_h = 1.6163399` solving `2J₁(x)/x = 1/√2` | Airy pattern `[2J₁(v)/v]²` for a uniformly-illuminated circular aperture (Born & Wolf §8.5.2), **cited by its reproducible root** rather than an equation number this project could not confirm; corroborated by Thorne & Blandford, *Modern Classical Physics* ch. 8, `ρ_FWHM = 1.61633 z/(kR)`. ⚠️ **Not 1.22** (Rayleigh first null, +19%) | `array/focus.py:spot_size`, `FWHM_COEFFICIENT` | `tests/unit/test_spot_size.py` | VERIFIED |
| EQ-031 | Split-phase factorization `exp(iφ_a) = exp(iφ_ref)·exp(iΔφ_a)` | This project's own construction, eq. n/a — phasors multiply, so the large common phase and the small residual are never *added*. See the Assumption Ledger row on absolute-phase representability | `core/backend.py:SplitPhase.phasor`, `split_phase` | `tests/unit/test_split_phase.py` | DERIVED |
| EQ-034 | Uniform-sphere `l=2` finite-size form factor `F₂(kR) = 1 − 5(kR)²/98`; general `l`: `1 − (kR)²(l+3)/[2(2l+3)(l+5)]` | [ADR-0007](adr/0007-uniform-sphere-quadrupole-form-factor.md), eq. 3 — this project's own derivation. **No numbered equation for the *result* exists in any accessible source**; Thorne, *Rev. Mod. Phys.* 52:299 (1980) is the likely primary source but is paywalled and its numbering is unconfirmed, so it is deliberately *not* cited with an equation number. The derivation's *input* is citable — **DLMF 10.53.1** (dlmf.nist.gov/10.53, open access, numbered), transcribed and checked in exact rational arithmetic for `l = 0…6` — so the uncited step is narrowly the elementary integration of that series against a uniform-ball radial weight. Verified additionally by three independent numerical routes (far-field retarded phase integral to **1.7e-12**; exact retarded Green's function to 1.4e-8; point-mass lattice), none evaluating a spherical Bessel function, plus an independent `code-reviewer` re-derivation. ⚠️ **`sin(kR)/(kR)` (1/6) is spin-1 `l=0` antenna machinery and `3j₁(kR)/(kR)` (1/10) is the total-mass monopole** — both are wrong here | `bodies/multipole.py:finite_size_correction` | `tests/unit/test_multipole.py` | DERIVED |

**Citations verified 2026-07-26** for all Sprint 1 equations (EQ-001–007); **2026-07-27** for
the Sprint 4/5/9/6/11/3/8/2 additions above (EQ-008–023). Sources are open access with
checkable equation numbers except where flagged (EQ-014, EQ-019 in-paper numbers, EQ-021,
EQ-023 unnumbered display, EQ-034 no equation number exists — see ADR-0007):

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
| `core/backend.py` | Array-API shim (numpy / numba) | **live** — `get_backend`, `Backend` (T-11.1; no citation requirement, infrastructure only); `field_grid`, `_field_grid_loop` (T-11.2; Numba-JIT-compilable TT-strain superposition over a field-point grid, one already-evaluated `q_ddot` per source shared across the whole grid — see Assumption Ledger for the light-crossing-time restriction this imposes); `SplitPhase`, `split_phase` (T-11.3; FP64 reference phase + FP32-safe differential — use `.phasor()`, **not** `.recombine()`, which is irreducibly lossy at astronomical range) | `source/quadrupole` (via caller-supplied `q_ddots`), `core/validation` |
| `bodies/sphere.py` | Rigid uniform sphere; mass/inertia; rotational-oblateness quadrupole | **live** — `Sphere` (dataclass: `radius`, `density`, `.mass`, `.moment_of_inertia`, `.self_quadrupole()`), `oblateness_quadrupole` (T-4.1/4.2/4.6) | `constants` |
| `bodies/elastic.py` | Love-number deformation; breaks R/ρ degeneracy | **live** — `love_number_k2`, `induced_quadrupole` (T-4.3). **This is where the rigid model's mass/radius/density degeneracy breaks**: `Q ∝ R⁵` explicitly and `ρ` enters through `μ̃`, so equal-mass spheres are no longer radiatively identical (asserted against T-4.2 in `test_elastic.py`) | `sphere`, `constants`, `core/validation` |
| `bodies/multipole.py` | Mass multipole moments and derivatives | **live** — `quadrupole_moment`, `_second_derivative`, `_third_derivative` | `constants` |
| `kinematics/profiles.py` | Finite-maneuver acceleration profiles | **live** — `AccelerationProfile` (base), helpers `_finish`, `_prepare_time` | — |
| `kinematics/oscillators.py` | Prime-frequency multi-tone drive synthesis | **live** — `first_n_primes`, `prime_frequencies`, `recurrence_period`, `PrimeOscillatorDrive` (T-9.1–9.4; DSP/kinematic module, exempt from citation-CI) | `profiles`, `core/validation` |
| `source/quadrupole.py` | Quadrupole radiation, luminosity, and maneuver waveforms | **live** — `strain_tt`, `luminosity`, `waveform_from_profile` (T-3.8, adds symmetric two-body maneuver modeling) | `multipole`, `tt_projection`, `bodies/sphere`, `kinematics/profiles` |
| `source/multipole_rad.py` | Higher multipoles; dipole term (flagged) | *(Sprint 2, not yet implemented)* | `multipole` |
| `source/memory.py` | Linear GW memory from finite maneuvers | **live** — `linear_memory` (T-3.7; non-relativistic limit of Favata eq. 10k). Cross-validated against the independent quadrupole route to machine precision — see ADR-0004 | `tt_projection`, `constants`, `core/validation` |
| `source/conservation.py` | ∂_μT^μν audit; `UNPHYSICAL` stamping | **live** — `audit`, `ConservationReport` (T-2.1); `StampedResult`, `StampStrippedError`, `UNPHYSICAL_STAMP` (T-2.2). Two layers: `audit` *detects* non-conservation, `StampedResult` *propagates* that verdict through arithmetic so it cannot be laundered. See ADR-0005 for why it is a wrapper and not an `ndarray` subclass | `core/validation` |
| `propagate/tt_projection.py` | Transverse-traceless projector | **live** — `tt_projector`, `apply_tt`, `transverse_projector` | — |
| `propagate/polarization.py` | Spin-2 basis; e^(2iψ) rotation | *(Sprint 5, not yet implemented)* | `tt_projection` |
| `propagate/retarded.py` | Per-source retarded-time field evaluation | **live** — `PointSource` (dataclass), `field_at` (T-6.7; retards each source individually — see module docstring on why a shared array-centroid retardation would be wrong), `propagate` (T-6.8; batches `field_at` over field points × times, shape `(M, T, 3, 3)`) | `source/quadrupole`, `core/constants` |
| `array/geometry.py` | Element placement | **live** — `linear_array`, `planar_array`, `sparse_array` (T-5.5–5.7) | — |
| `array/beamform.py` | Scalar array factor, steering, beamwidth/sidelobes, tapering | **live** — `array_factor`, `steering_phases`, `beamwidth_3db`, `peak_sidelobe_level`, `taper` (T-6.1–6.4). **Explicitly the spin-1/scalar baseline** — see module docstring warning; the spin-2 tensor superposition `superpose_tt` (T-6.5) is not yet implemented | `geometry`; tensor superposition (not yet built) will depend on `polarization` |
| `array/grating.py` | Grating-lobe and spacing constraints | **live** — `max_spacing`, `has_grating_lobes` (T-5.8) | `geometry` |
| `array/focus.py` | Spatiotemporal focusing | **live** — `focal_phases` (T-9.5), `focused_phasor`/`focused_field` (T-9.6), `spot_size`/`FWHM_COEFFICIENT` (T-10.1). Far-field only per [ADR-0006](adr/0006-focused-field-far-field-regime.md); near-field requests raise. `focus_trajectory` (T-9.7) and `dwell_time` (T-10.3) **not yet implemented** | `beamform`, `geometry`, `kinematics/oscillators`, `constants`, `core/validation` |
| `target/geodesic.py` | Geodesic deviation at the target | *(Sprint 8, not yet implemented)* | `tt_projection` |
| `target/coupling.py` | Non-GW comparison channel: gravity tractor | **live** — `channel_gravity_tractor` (T-8.5; other two momentum-transfer channels from the module's original scope not yet implemented) | `constants` |
| `target/deflection.py` | Orbit propagation; Δv → miss distance | *(Sprint 8, not yet implemented)* | `coupling` |
| `ledger/gap_report.py` | Feasibility ledger | **live** — `GapMetric`, `GapReport`, `GapMetric.from_stamped` (T-2.6). **Schema is FROZEN**: `name, achieved, required, units, source_module, provenance` is a contract every epic writes to; `test_gap_report.py` pins the field set *and order* so a breaking change fails loudly. **Use `from_stamped()`** for any value originating as a `StampedResult` — the plain constructor would compile while discarding the stamp | `source/conservation` (for `UNPHYSICAL_STAMP`, `StampedResult`) |
| `viz/patterns.py` | Beam-pattern visualization (polar + 3D) | **live** — `plot_pattern_polar`, `plot_pattern_3d` (T-7.4/7.5; headless `Agg` backend; reimplements array-factor math vectorized for full-grid rendering rather than calling `beamform.array_factor` per point — kept numerically consistent by shared test coverage, not by a shared code path) | `array/beamform` (mathematically, not by import) |
| `viz/*` (other) | Field slices, volumetric rendering | *(Sprint 7, not yet implemented)* | — |
| `core/validation.py` | ADR-0002 shape/dtype/unit-vector guards | **live** — `as_masses`, `as_body_array`, `as_tensor_3x3`, `as_unit_vector`, `as_float64` | — |

✅ **Resolved 2026-07-31.** The note that previously stood here flagged `superpose_tt` (T-6.5)
as a forward reference to unbuilt code. **T-6.5 and T-6.6 have since landed** — `superpose_tt`
and `mismatch_loss` are live in `array/beamform.py`, per ADR-0003. The standing caution still
holds and is not withdrawn: `array_factor`, `steering_phases`, `beamwidth_3db`,
`peak_sidelobe_level` and `taper` remain the **scalar spin-1 baseline**, and only
`superpose_tt`/`mismatch_loss` carry spin-2 physics. Do not read the former as gravitational
radiation (CLAUDE.md rule 4).

⚠️ **`array/focus.py` is only partially built.** `focal_phases` (T-9.5) exists; the field
evaluation `focused_field` (T-9.6, `opus`, **critical path**) does not.

✅ **The design tension is resolved.** `superpose_tt` assumes the far field — one common
observation direction, raising inside the Fraunhofer distance — so it was not obvious that T-9.6
could use it. **SPIKE-9.6 measured the margin and it can:** the angular spread of per-element
directions at 40 AU is 1.03e-9 rad against ADR-0003's 5.0e-2 rad alignment budget, a **2.4e7×
margin**, so ADR-0003's reversal condition is not triggered. See
[ADR-0006](adr/0006-focused-field-far-field-regime.md). T-9.6 is now Definition-of-Ready, and
its backlog entry carries four measured traps that each produce a *passing but meaningless*
test — read them before writing the tests, not after.

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
| `field_grid` shares one already-evaluated `q_ddot` per source across an entire field-point grid, rather than recomputing retarded time per point (unlike `propagate`/`field_at`) | `core/backend.py:field_grid`, `_field_grid_loop` | Grid's light-crossing time (extent / `c`) is negligible compared to the timescale on which each source's `q_ddot` varies (e.g. ≪ `c/ω` for an oscillating drive) | **Diverges from the per-point-retarded `propagate()` result once the grid spans a non-negligible light-crossing time** — demonstrated by the regression test `tests/unit/test_backend.py::test_field_grid_single_slice_diverges_when_grid_light_crossing_time_is_not_negligible`. Use `propagate()`/`field_at()` instead of `field_grid` whenever the grid extent is comparable to or larger than a wavelength of the drive |
| **Linear memory is the non-relativistic limit** — the per-body Lorentz factor `1/√(1−v²/c²)` *and* the relativistic beaming factor `1/(1−v·N)` of Favata eq. 10k are both dropped | `source/memory.py:linear_memory` | `v/c ≪ 1`; at this project's `v/c ~ 1e-5` both factors differ from 1 at the ~1e-10 level | Fails for relativistic ejecta or any configuration approaching `v ~ c`. Note the beaming factor is absent from BACKLOG's statement of the formula too, so this is not merely a restatement of the spec — it is a correction to it |
| **Static (adiabatic) tidal response** — the body is assumed to reach equilibrium deformation instantaneously relative to the drive | `bodies/elastic.py:induced_quadrupole`, `love_number_k2` | Drive period ≫ the body's internal elastic response time | **Fails as the drive frequency approaches the body's internal oscillation modes**, exactly the high-frequency regime this project is most interested in. No frequency-dependent (complex `k₂`) treatment exists here yet |
| **Homogeneous, incompressible Kelvin sphere** — `k₂ = (3/2)/(1+μ̃)` assumes uniform density, incompressibility, and hydrostatic equilibrium | `bodies/elastic.py:love_number_k2` | Monolithic, undifferentiated bodies | **Breaks for differentiated, porous, or rubble-pile asteroids** — i.e. a large fraction of real deflection targets. The function cannot detect this from its arguments; the caller must |
| **The reference aperture is sub-wavelength below ~100 kHz** — the 12.4 km planar array spans `D/λ = 0.041` at the nominal 1 kHz drive | SPIKE-9.6 / [ADR-0006](adr/0006-focused-field-far-field-regime.md) §"Four traps" 1 | Only above ~100 kHz (`D/λ > 1`) does the array have a beam at all | **Below that it is a point source, not an array**: no directivity, no steering, no focusing. Every weighting — including uniform `w = 1` — returns exactly `N`, so any array-behaviour test written at 1 kHz passes with the logic deleted. Assert `D/λ > 1` in such tests. This also sharpens B-3: the aperture requirement is not merely large but unreachable at GW-plausible frequencies for apertures of this scale |
| **`focused_field` is a far-field construction; near-field focusing is out of scope** | [ADR-0006](adr/0006-focused-field-far-field-regime.md); enforced by `superpose_tt`'s existing Fraunhofer guard | `R ≫ 2D²/λ` — at 40 AU, `R/R_Fraunhofer = 5.9e6` even at 1 MHz | Inside the Fraunhofer distance (< ~1.0e6 m for a 12.4 km aperture at 1 MHz) ADR-0003's common-`n̂` premise fails along with this decision. `superpose_tt` raises rather than degrading; **propagate that error, do not catch it**. Reversing requires a new ADR deriving the per-element projection rule |
| **Focusing is degenerate with steering at 40 AU** — the wavefront sag across a 12.4 km aperture at 40 AU is ~3.2e-6 m, giving a total focusing phase of ~6.7e-11 rad at 1 kHz | `array/focus.py` module docstring; `tests/unit/test_focus.py::test_focusing_is_degenerate_with_steering_at_40_au` | Never, at target range: `R/R_Fraunhofer ~ 5.9e9` at 1 kHz | **This is a wall, not a limitation of the code** (CLAUDE.md rule 5). At 40 AU a "focal point" is indistinguishable from a steering direction at infinity — you cannot focus, only steer. It is the same diffraction wall T-10.2 states as `D/λ ≳ 6e9`. If a change makes this spread large at 40 AU, suspect the change |
| **Absolute propagation phase is not representable, in float64 either** — at 40 AU / 1 kHz the absolute phase is ~1.25e8 rad, where float64's spacing (~1.5e-8 rad) is ~340× *larger* than the entire per-element differential (~4.4e-11 rad) | `core/backend.py:SplitPhase.recombine` docstring; `tests/unit/test_split_phase.py::test_absolute_phase_defeats_float64_too_not_only_float32` | — | **The reference/differential split is not an FP32 optimisation; it is the only way to obtain the number at all.** Any code that forms `k·R_a` per element and subtracts gets exactly zero — in float64. Use `SplitPhase.phasor()`, never `.recombine()`. float32 is worse still: its spacing at that magnitude is **8 rad**, wider than a full cycle |
| **The ledger can record unphysical provenance, but only if the caller uses `GapMetric.from_stamped`** — the plain constructor takes a bare `float` and will silently accept a `.value`-unwrapped number | `ledger/gap_report.py:GapMetric.from_stamped`; module docstring "Freeze amended 2026-07-31" | Any row whose `achieved` originates from a `StampedResult` | Found as a **Critical** review finding on the day the schema was frozen: with no `provenance` field, a caller was *forced* to unwrap to `.value`, turning a ~10^10× mass-dipole artifact into a row that clears its requirement by ten orders of magnitude. Closed by the sixth field. The residual risk is ergonomic, not structural — nothing prevents a future author calling the plain constructor with an unwrapped value, so review any new ledger call site for `.value` |
| `StampedResult` raises on non-ufunc NumPy entry points (`np.concatenate`, `np.stack`) rather than propagating the stamp through them | `source/conservation.py:StampedResult.__array__`; ADR-0005 | Any code path that coerces a stamped result to a bare array | Deliberately unsolved: `__array_function__` support should be added against a real use case, not speculatively. Raising is the safe failure — it cannot silently drop the stamp — but it does mean stamped results will not drop into arbitrary NumPy code |
| **The finite-size form factor assumes a *volume-filling* `l=2` radial profile** — `δρ` uniform on `[0, R]`, giving `1 − 5(kR)²/98` | `bodies/multipole.py:finite_size_correction`; [ADR-0007](adr/0007-uniform-sphere-quadrupole-form-factor.md) eq. 3 vs eq. 5 | The body's quadrupole is distributed through its volume | **A body that acquires its quadrupole by deforming its *surface* has `δρ ∝ δ(r−R)` and `1 − (kR)²/14` instead — 40% larger.** That is exactly the incompressible tidal (`elastic.py:induced_quadrupole`, T-4.3) and rotational (`sphere.py:oblateness_quadrupole`, T-4.6) case, so this correction **must not be applied to either without re-deriving**. Both cases are legitimately "the uniform sphere"; the phrase does not determine the answer. A future source quoting `1/14` is *not* a confirmation of EQ-034 — it confirms the other one |
| **ADR-0006's cited prototypes were never committed** — `scratchpad/spike_9_6.py`, `spike_9_6b.py` — because `scratchpad/` was untracked until 2026-08-02 | [ADR-0006](adr/0006-focused-field-far-field-regime.md) "Context" | Found while writing [ADR-0007](adr/0007-uniform-sphere-quadrupole-form-factor.md) 2026-08-02 | **Resolved the same day.** A fresh `scratchpad/spike_9_6.py` regenerates every ADR-0006 figure (angular spread, margin, `D/λ` table, sign-convention table, Rayleigh background) from current production code and the geometry already pinned in `tests/unit/test_focused_field.py`; all reproduce, including the peak-to-background ratio of 8.75 against the naive `√N = 8.00`. Recorded rather than silently fixed, per rule 8 — absence of a reproducible prototype in an accepted ADR is itself a finding in a project that optimizes for auditability |
| **The finite-size correction is a leading-order truncation and goes negative** at `kR = √(98/5)`, i.e. `R/λ = 0.7046` | `bodies/multipole.py:finite_size_correction`; `tests/unit/test_multipole.py::test_finite_size_correction_validity_floor_is_recorded` | `R/λ ≪ 0.1`; departure from unity is 2.0142% already at `R/λ = 0.1` | A wall, not a bug (rule 5). The series `1 − 5(kR)²/98` returns *negative* form factors past the crossing and is meaningless well before it. T-4.7 adds the structured out-of-regime warning at `R/λ > 0.1`. **Do not "fix" the sign** — the fix is to stop calling it out of regime. The exact closed form (ADR-0007 eq. 4) is *not* a remedy: it is cancellation-limited below `kR ≈ 0.05` and is less accurate than the series in the regime that matters |

---

## 4. Validation Status

A benchmark that has not run since the code it validates last changed is **stale**, not
passing.

| Benchmark | Validates | Status |
|---|---|---|
| Circular binary (h₊, h×, L) | EQ-005, EQ-006, EQ-007 | **PASSING** rtol 1e-6 |
| Hulse–Taylor PSR B1913+16 period decay (T-12.2) | EQ-006 (extension) | **Not implemented — now unblocked (2026-08-02).** Citation resolved: Kowalska, Bulik, Belczyński, Dominik & Gondek-Rósińska, A&A 527:A70 (2011), arXiv:1010.0511, eq. (1) [⟨da/dt⟩] and eq. (3) [⟨de/dt⟩] — open-access, peer-reviewed, coefficients confirmed algebraically to match the 73/24, 37/96, 121/304 form. Blanchet arXiv:1310.1528 turned out **not** to contain this formula at all (quasi-circular inspiral only); Caltech's Peters (1964) PDF is permanently `ECONNREFUSED` from this environment — cite Kowalska et al., not "Peters 1964 eq. 5.6/5.7," whose own numbering remains unverified. PSR B1913+16 system parameters separately verified via arXiv:1606.04581 (Weisberg & Huang 2016) |
| Spinning rod power | EQ-006 | Not implemented (T-2.8) |
| **Dipole cancellation** | Momentum conservation (decision 1) | **PASSING** — ratio < 1e-12 over 20 seeded configs, plus a positive control > 1e-3. *OQ-1 resolved: the dipole does cancel as expected.* |
| **Linear memory vs. independent quadrupole route (T-3.7)** | EQ-026, EQ-022 | **PASSING** — `tests/benchmarks/test_memory.py`. Reproduces the settled post-maneuver value of `waveform_from_profile` **bit-for-bit on-axis** (0.0 difference, as ADR-0004 predicted before the code existed), and to 1 ULP for oblique observation directions. The oblique refinement is recorded in ADR-0004 |
| Linear memory (hyperbolic scattering, T-3.9) | EQ-026 | Not implemented — `sonnet-low`, now unblocked by T-3.7 |
| Love-number deformation (T-4.3) | EQ-027, EQ-028 | **PASSING** — `tests/unit/test_elastic.py`, including the explicit contrast against T-4.2's degeneracy assertion |
| **Finite-size form factor (T-4.5 / SPIKE-4.5)** | EQ-034 | **PASSING** — `tests/unit/test_multipole.py`. Checked against the exact closed form (ADR-0007 eq. 4, via `scipy.special.sici`) with the *discarded series tail* asserted rather than a flat tolerance, so the test is sensitive to the `(kR)²` coefficient itself. **Mutation-tested:** replacing `5/98` with `1/6`, `1/10`, `1/14`, a sign flip, a 0.1% nudge, or even a **0.001% nudge** each fails 4–5 tests. Note the "tends to unity" test is *not* what catches them — it passes for every wrong coefficient except the sign flip; `test_finite_size_correction_coefficient_is_exactly_5_over_98` is the load-bearing pin. Regression guards name both wrong form factors explicitly (rule 4). Independent numerical verification lives in `scratchpad/spike_4_5.py`, not in the suite — it takes ~20 s and its results are recorded in ADR-0007 |
| Focal phase solution (T-9.5) | EQ-029, EQ-030 | **PASSING** — `tests/unit/test_focus.py`, verified against 60-digit `decimal` reference ranges rather than the implementation's own float64 arithmetic |
| Split-phase decomposition (T-11.3) | EQ-030, EQ-031 | **PASSING** — `tests/unit/test_split_phase.py`, including the required demonstration that naive FP32 **fails** the same check, and the stronger finding that naive float64 does too |
| `UNPHYSICAL` stamp propagation (T-2.2) | — (governance, no equation) | **PASSING** — `tests/unit/test_stamped_result.py`, 36 tests covering arithmetic, slicing, `str()`, JSON, and refusal of `np.asarray`/`np.array`/`out=` |
| Ledger schema round-trip and stable rendering (T-2.6) | — (schema, no equation) | **PASSING** — `tests/unit/test_gap_report.py`, field set and order pinned against the freeze |
| Array factor vs. reference (T-6.9) | EQ-016 | **PASSING** — via closed-form analytic uniform-array reference, **not** `arraytool` as originally specified (see flag in §1 above; `arraytool` unavailable offline) |
| Spatiotemporal focusing / mode-locking (T-9.6) | EQ-032 | **PASSING** — `tests/unit/test_focused_field.py`. Each of ADR-0006's four traps is guarded by name, including an explicit assertion that the test frequency leaves the aperture super-wavelength, and a sign-convention test at 50 beamwidths where the two conventions actually differ |
| Focal spot size (T-10.1) | EQ-033 | **PASSING** — `tests/unit/test_spot_size.py`. Coefficient verified **twice independently**: re-solved from `2J₁(x)/x = 1/√2` with `scipy.optimize.brentq`, and measured from the simulated diffraction pattern of a filled circular aperture (agreeing to rtol 1e-2) |
| Diffraction limit `w ≈ λr/D` (T-10.2) | EQ-033 | Not implemented — now unblocked (T-10.1 complete). `sonnet-low`. The frequency-independence of `D/λ ≳ 6.16e9` for a 1 km spot at 40 AU is already asserted in `test_spot_size.py`; T-10.2 should extend it to a numerically-propagated field rather than the closed form |
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
| Batched propagation over field points × times (T-6.8) | EQ-024 | **PASSING** — `tests/unit/test_retarded.py` |
| Numba field-grid kernel, incl. light-crossing-time breakdown regression (T-11.2) | EQ-025 | **PASSING** — `tests/unit/test_backend.py`, including `test_field_grid_single_slice_diverges_when_grid_light_crossing_time_is_not_negligible` |
| Gravity-tractor channel (T-8.5) | EQ-023 | **PASSING** — `tests/unit/test_coupling.py`, worked example checked against source paper Fig. 2 |
| Beam-pattern plots (T-7.4/7.5) | — (visualization, no numbered equation) | **PASSING** — `tests/unit/test_patterns.py` |
| ADR-0002 convention enforcement (T-2.10) | Shape/dtype/unit-vector guards project-wide | **PASSING** — `tests/unit/test_conventions.py`, extended to cover all modules added this batch (`sphere`, `retarded`, `quadrupole.waveform_from_profile`) |

**Resolved 2026-07-31.** The note that stood here flagged "1 of 25 assigned batch tasks not
completed this pass," unidentified. It has been reconciled against `BACKLOG.md`'s ✅ markers,
which are now the single source of truth and are read directly by `tools/schedule.py`. The
count is **66 of 116 complete**; run `python tools/schedule.py --status` for the live figure
rather than trusting any number written into this file.

**Updated 2026-08-02.** Of the three tasks formerly blocked, two are now closed: T-12.2
(OQ-6, Kowalska et al. supplied checkable equation numbers) and T-4.5 (OQ-7, closed by
SPIKE-4.5 / ADR-0007 as a **Category B derivation** — the citation was never found, and
the decision was to proceed without one on numerical evidence). Landing T-4.5 also freed
T-4.7, T-4.8 and T-4.9. **One task remains blocked:** T-2.9 (repo made public), which is
machine-readable in its `deps` field so the scheduler excludes it *and names the reason*.
Run `python tools/schedule.py --status` for live counts rather than trusting this note.

---

## 5. Open Questions

| ID | Question | Context |
|---|---|---|
| ~~OQ-1~~ | **RESOLVED 2026-07-26** — the dipole cancels to <1e-12 relative in momentum-conserving configurations, confirming decision 1. | |
| OQ-1 (orig) | Does the dipole term cancel numerically to the precision we expect in a momentum-conserving two-body configuration? | Validates the project's central physics framing (decision 1). Scheduled Sprint 1 — pulled forward from Sprint 2 because a surprise here reframes everything downstream |
| OQ-2 | How is polarization-mismatch loss correctly formulated for spin-2 array elements of differing orientation? | No external reference implementation exists. `SPIKE-4.4` (Sprint 2) attacks this early because it sits on the critical path. **Still open** — `array/beamform.py` this batch is explicitly the spin-1 scalar baseline that this spike's answer must reduce to, not an answer itself |
| OQ-3 | At what R/λ does the long-wavelength quadrupole approximation fail badly enough to matter? | Determines whether `bodies/` finite-size corrections are a refinement or a requirement. **Partially answered 2026-08-02** by EQ-034 / [ADR-0007](adr/0007-uniform-sphere-quadrupole-form-factor.md): the quadrupole form factor departs from unity by 1% at `R/λ = 0.0705` and 2.0142% at `R/λ = 0.1`, and the leading-order series is meaningless past `R/λ ≈ 0.7`. What that *costs* in deflection terms is still open — T-4.8's sensitivity study is the remaining half |
| ~~OQ-7~~ | **RESOLVED 2026-08-02 — as a negative answer.** SPIKE-4.5 → [ADR-0007](adr/0007-uniform-sphere-quadrupole-form-factor.md). **No citable numbered equation exists in any accessible source**, so the question as posed has no answer; it is closed by *deciding to proceed without one*. `F₂(kR) = 1 − 5(kR)²/98` is adopted as **Category B** (our derivation, EQ-034), verified by three independent numerical routes rather than by citation — the strongest agreeing to `1.7e-12`. Both originally-proposed form factors were confirmed wrong (`1/6` is spin-1 `l=0`; `1/10` is the total-mass monopole). Thorne 1980 remains paywalled and its equation number is **still unconfirmed and deliberately not cited**. Promotion to Category A requires a numbered equation *that states the volume-filling radial profile explicitly* — see the ADR's reversal condition. Unblocked T-4.5, T-4.7, T-4.8, T-4.9 |
| OQ-4 | Is a sparse (non-filled) array viable given the 6×10⁹-wavelength aperture requirement? | Sparse arrays relax element count but raise sidelobes — directly opposed to requirement 6's single-point focus. `array/geometry.py:sparse_array` (this batch) supplies a reproducible layout to test against, but does not itself resolve the question — no sidelobe/viability analysis has been run on it yet |
| OQ-5 | Does the near-zone gradient channel (Lu & Love) scale to anything useful at 40 AU? | If not, conjecture C-4 has no candidate mechanism. `target/coupling.py:channel_gravity_tractor` (this batch) implements the comparison channel itself but does not resolve OQ-5's point-mass-approximation caveat — see Assumption Ledger |
| ~~OQ-6~~ | **RESOLVED 2026-08-02** — see BACKLOG.md T-12.2. Kowalska et al., A&A 527:A70 (2011), arXiv:1010.0511, eq. (1)/(3) supplies a checkable, open-access equation for the eccentric-orbit decay coefficients; the original Peters (1964) equation numbers remain unverified and are not cited directly. | |

---

## Maintenance rules

- Never let the Equation Registry drift from the code. A citation in a docstring but not the
  registry gets added; a registry row pointing at a function that no longer exists gets
  **flagged loudly**, not deleted. A vanished equation is a finding.
- Cross-link to `CLAIMS.md` categories so the two documents cannot disagree.
- Prefer flagging over fixing. When index and code disagree, report the disagreement and let a
  human or a task decide which is wrong.
