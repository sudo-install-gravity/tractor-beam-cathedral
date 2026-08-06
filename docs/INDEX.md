# Codebase Index

Maintained by the `indexer` agent. This is the central knowledge store for the project — the
defense against future archaeology. A contributor arriving decades from now should be able to
audit the foundations from here without reverse-engineering the code.

**Last updated:** 2026-07-27 (Sonnet batch, 24/25 tasks — T-4.1/4.2/4.6, T-5.5–5.8, T-6.1–6.4/6.7,
T-8.5, T-9.1–9.4, T-11.1, T-3.8, T-7.4/7.5, T-2.10)

**Updated 2026-07-31:** added T-6.8 (`propagate()`, EQ-024) and T-11.2 (`field_grid`,
EQ-025), including the `field_grid` light-crossing-time scope restriction in the Assumption
Ledger.

**Updated 2026-08-02 (`indexer` reconciliation pass):** §1 and §2 were reconciled against
the code after a **large accumulated drift** was found — see the drift note at the end of
§1. Added **EQ-035–EQ-053** (19 rows) for public, citation-carrying functions that had
landed without a registry row, and rewrote eleven §2 Module Map rows. **None of the new
rows is marked `VERIFIED`**; the registry holds no verification record for them.

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
| EQ-035 | Spin-2 polarization basis `(e₊, e_×)` transverse to `n̂` | **[B] eq. 69a-69b** | `propagate/polarization.py:polarization_basis` (T-5.1) | `tests/unit/test_polarization.py` | ✅ **VERIFIED 2026-08-03, citation replaced.** Blanchet introduces unit polarization vectors `P`, `Q` transverse to `N` (`N_iN_j + P_iP_j + Q_iQ_j = δ_ij`) and defines `h₊ = ½(P_iP_j − Q_iQ_j)H^TT_ij` (69a), `h_× = ½(P_iQ_j + P_jQ_i)H^TT_ij` (69b) — the bracketed tensors **are** `e₊`, `e_×`. Frame-covariant in `N`, as the implementation is. *Previously cited [FH] eq. 2.22, which reads `h^TT_xx = −h^TT_yy ≡ h₊`: the polarization **scalars** in a z-aligned frame, not the basis tensors, and not covariant. Found while correcting EQ-040 — same paper, adjacent defect.* Pinned by `test_decompose_reproduces_blanchet_69a_69b_written_out`, which transcribes both equations by hand |
| EQ-036 | Rotating-quadrupole element pattern `h₊ ∝ (1+cos²θ)/2`, `h_× ∝ cosθ` | [B] eq. 2 (VERIFIED at EQ-005), applied to the circular-orbit quadrupole of [B] eq. 3 | `propagate/polarization.py:element_pattern_rotating` (T-5.4) | `tests/unit/test_polarization.py` | DERIVED (docstring self-declares claim category B; cross-checked in-code against `quadrupole_second_derivative` + `apply_tt`) |
| EQ-037 | Linear-quadrupole element pattern `h₊ ∝ sin²θ`, `h_× = 0` | [B] eq. 2 (VERIFIED at EQ-005), applied to a single-axis quadrupole of [B] eq. 3 | `propagate/polarization.py:element_pattern_linear` (T-5.4) | `tests/unit/test_polarization.py` | DERIVED (docstring self-declares claim category B; verified in-code to 1e-9 against `apply_tt`) |
| EQ-038 | TT tensor → polarization scalars, `(h₊, h_×) = ½ e_A : h_ij` | **[B] eq. 69a-69b** — this function **is** eqs. 69a/69b evaluated | `propagate/polarization.py:decompose` (T-5.2) | `tests/unit/test_polarization.py` | DERIVED — ✅ **underlying citation now checked (2026-08-03).** [FH] eq. 2.22/2.23 do define exactly this scalar⇄tensor correspondence (`h^TT_xx = −h^TT_yy ≡ h₊`, `h^TT_xy ≡ h_×`), so this row is sound — but it should cite **2.22 *and* 2.23**, since `h_×` comes from 2.23. See EQ-035 for the part of that paper's §2.2 that does *not* say what was claimed |
| EQ-039 | Polarization scalars → TT tensor, `h_ij = h₊e₊ + h_×e_×` | **[B] eq. 69a-69b** — the **inverse** of eqs. 69a/69b, unique on the TT subspace by `e_A : e_B = 2δ_AB`; the inversion is ours | `propagate/polarization.py:recompose` (T-5.2) | `tests/unit/test_polarization.py` | DERIVED — ✅ **underlying citation now checked (2026-08-03).** [FH] eq. 2.22/2.23 do define exactly this scalar⇄tensor correspondence (`h^TT_xx = −h^TT_yy ≡ h₊`, `h^TT_xy ≡ h_×`), so this row is sound — but it should cite **2.22 *and* 2.23**, since `h_×` comes from 2.23. See EQ-035 for the part of that paper's §2.2 that does *not* say what was claimed |
| EQ-040 | Spin-2 polarization rotation, period π not 2π: `h₊′ = h₊cos2ψ + h_×sin2ψ`, `h_×′ = −h₊sin2ψ + h_×cos2ψ` | **Mashhoon, B. & Rahvar, S., *Universe* 9:6 (2023), arXiv:2211.01691, eq. 4** (open access, CC BY 4.0) | `propagate/polarization.py:rotate_polarization` (T-5.3) | `tests/unit/test_polarization.py` | **VERIFIED 2026-08-03** — ✅ **the suspicion below was correct and the citation was wrong.** [FH] eq. 4.22 is the **TT projector** (the same equation EQ-004 cites, correctly), and the rotation law appears **nowhere** in that paper — it shows the 45° relationship only qualitatively in its Figure 1, with no equation. Mashhoon & Rahvar eq. 4 matches the implementation term for term. Confirmed by direct fetch, not taken on an agent's report. CLAIMS.md **A-5** was mis-cited the same day (to "MTW §35–36", a chapter reference) and now carries this source too |
| EQ-041 | Mass dipole moment `d_i = Σ_A m_A x_A,i` | [FH] eq. 4.30 | `source/multipole_rad.py:dipole_moment` (T-2.3) | `tests/unit/test_multipole_rad.py` | **VERIFIED 2026-08-03** — read directly: [FH] eq. 4.30 is `M₁ ≡ ∫ρxⁱd³x = MLⁱ`, the mass dipole. The docstring already documented the continuum→point-mass substitution honestly |
| EQ-042 | Analytic dipole second derivative `d̈_i = Σ_A m_A a_A,i = dP_i/dt` | [FH] eq. 4.35, **differentiated once** | `source/multipole_rad.py:dipole_second_derivative` (T-2.3) | `tests/unit/test_multipole_rad.py` | **DERIVED 2026-08-03 — citation corrected in scope.** Read directly: [FH] eq. 4.35 is `dM₁/dt = ∫ρvⁱd³x = Pⁱ`, the **first** derivative. This function returns the **second**, so the source is that equation differentiated once — not a statement of `d̈` itself. Reclassified VERIFIED→DERIVED, matching EQ-002/EQ-003 which cite [B] eq. 3 differentiated. The function's own prose was already accurate; only the `Source:` line overstated |
| EQ-043 | Mass-dipole strain diagnostic: `e_i = (G/c⁴)d̈_i`, `h_ij = Λ_ij,kl(n̂)(e_k e_l − ⅓δ_kl e·e)` | This project's own construction, eq. n/a — no established multipole-radiation reference applies to a momentum-non-conserving source | `source/multipole_rad.py:dipole_strain` (T-2.4) | `tests/unit/test_multipole_rad.py` | DERIVED — 🚨 **output is ALWAYS stamped `UNPHYSICAL` regardless of input. Never read as a physical result; never strip the stamp (CLAUDE.md rule 2). This is the ~10¹⁰× artifact the stamping machinery exists to contain** |
| EQ-044 | Trace-free (STF) mass octupole `Q_ijk`, `l = 3` | [B] eq. 123a, **Newtonian point-mass limit** | `bodies/multipole.py:octupole_moment` (T-2.5) | `tests/unit/test_multipole.py` | **DERIVED 2026-08-03 — citation corrected in scope.** Read directly: [B] eq. 123a is **Theorem 6**, the general STF multipole `I_L(u)` of a *post-Newtonian* source — a finite-part-regularized integral with `1/c²` and `1/c⁴` terms. It states far more than this function implements, which is its Newtonian point-mass limit. Framework cited, specialization ours (cf. EQ-034/DLMF). ⚠️ **[B] eq. 302a is likewise the 2.5PN circular-orbit octupole**, not a Newtonian expression; only its **leading term** `I_ijk = −νm∆x⟨ijk⟩` is the Newtonian two-body octupole, and that reduction is confirmed algebraically. ✅ **The cross-check now runs** — `test_octupole_reproduces_blanchet_two_body_newtonian_octupole`, five mass ratios, rtol 1e-12; see §4 |
| EQ-045 | Geodesic-deviation acceleration `ξ̈_i = ½ ḧ_ij^TT ξ_j` | [FH] eq. 3.11 | `target/geodesic.py:deviation_acceleration` (T-8.1) | `tests/unit/test_geodesic.py` | **VERIFIED 2026-08-03** — read directly: [FH] eq. 3.11 is `d²Lⁱ/dt² = ½ (d²h^TT_ij/dt²) Lʲ`, matching the implementation exactly. (`target/` is exempt from citation-**CI**, but that exemption is about CI enforcement, not registry completeness — this is the mechanism every coupling channel acts through, so it is registered deliberately) |
| EQ-046 | Per-element quadrupole radiator model (position + `Q̈_ij`) | [ADR-0003](adr/0003-spin2-superposition.md), eq. 1 — the per-element term of the superposition sum | `array/beamform.py:QuadrupoleElement` (T-6.5) | `tests/unit/test_superposition.py` | DERIVED |
| EQ-047 | **Spin-2 tensor array superposition** `h_ij(n̂) = Σ_n Λ_ij,kl(n̂) Q^(n)_kl w_n exp(i k·r_n)` | [B] eq. 2 (VERIFIED at EQ-005) per element, superposed per [ADR-0003](adr/0003-spin2-superposition.md) | `array/beamform.py:superpose_tt` (T-6.5) | `tests/unit/test_superposition.py` | DERIVED — ⚠️ **the project's highest-risk equation** (CLAUDE.md rule 4). Sums TT tensors along **one common `n̂`** and raises inside the Fraunhofer distance; discharges claim B-1 |
| EQ-048 | Spin-2 polarization-mismatch factor `cos(2Δψ)` | Derived in [ADR-0003](adr/0003-spin2-superposition.md) (claim B-1), from [B] eq. 2 | `array/beamform.py:mismatch_loss` (T-6.6) | `tests/unit/test_superposition.py` | DERIVED — ⚠️ **maximal at 45°, not 90°; elements 90° apart CANCEL where spin-1 intuition predicts 2× power** |
| EQ-049 | Mode-locked focus trajectory `R(t) = R_focus + c(t − t_focus)` | [B] eq. 2 (retarded-time relation; corollary of EQ-029) | `array/focus.py:focus_trajectory` (T-9.7) | `tests/unit/test_focus_trajectory.py` | DERIVED |
| EQ-050 | Fourier time-bandwidth dwell time `τ = 1/B` | Elementary Fourier time-bandwidth reciprocity, eq. n/a — not a GW-specific claim | `array/focus.py:dwell_time` (T-10.3) | `tests/unit/test_focus_trajectory.py` | DERIVED |
| EQ-051 | Peak-to-sidelobe ratio for a steered array, `√N` random-array background | This project's own construction, eq. n/a — built from `array_factor` (EQ-016); the `√N` scaling is the identity used for T-9.6's background per [ADR-0006](adr/0006-focused-field-far-field-regime.md) | `array/focus.py:peak_to_sidelobe` (T-10.4) | `tests/unit/test_focus_trajectory.py` | DERIVED — ⚠️ ADR-0006 trap 4: the background **mean** is the Rayleigh value `√(Nπ)/2 ≈ 0.886√N`, not `√N`; it is the *ratio* that scales as `√N` |
| EQ-052 | Radiated-power frequency sweep (f⁶ corollary of quadrupole luminosity) | [B] eq. 4 (VERIFIED at EQ-006); the f⁶ scaling is a corollary for a sinusoidal drive, not a new equation | `array/focus.py:band_sweep` (T-10.5) | `tests/unit/test_focus_trajectory.py` | DERIVED |
| EQ-053 | Required-aperture trade surface `D(f) = FWHM_COEFFICIENT·(c/f)·r/w` | This project's own construction, eq. n/a — algebraic inversion of `spot_size` (EQ-033); introduces no new equation | `array/focus.py:trade_surface` (T-10.6) | `tests/unit/test_focus_trajectory.py` | DERIVED — this is the **diffraction wall** (claim B-3) in solved-for-D form; if a change makes it shrink, suspect the change (rule 5) |
| EQ-054 | Spin-2 array alignment tolerance, with its finite-`N` bias: `E[gain/N²] = exp(−4σ²) + (1−exp(−4σ²))/N` | [ADR-0003](adr/0003-spin2-superposition.md) §3 for the `exp(−4σ²)` law, **as amended 2026-08-03** for the bias term. **Finite-N skeleton is citable: D'Addario, L. R., *IPN Progress Report* 42-175, JPL/Caltech (2008), eq. 5** — `P/P_max = (1/N²)[N + N(N−1)e^(−σ₀²)] = (1/N)(1−e^(−σ₀²)) + e^(−σ₀²)`, algebraically identical to `μ² + (1−μ²)/N`; open access, verified 2026-08-03 by reading the PDF directly. ⚠️ **Ruze (1966) is NOT the precedent** — D'Addario's own eq. 6 is the `N → ∞` reduction it attributes to Ruze, so Ruze covers the limit only. The **spin-2 content stays ours** | *(no `src/` function — an ADR result asserted directly by test, as EQ-007 is)*; evidence in `scratchpad/spike_b1_alignment_bias.py` | `tests/unit/test_superposition.py` | DERIVED — ⚠️ **`exp(−4σ²)` alone is the `N → ∞` limit.** The bias is *positive*, so a finite array beats the bare law slightly; the σ ≤ 2.87° / 1% requirement is a statement about the limit and is asserted analytically. **Do not simplify the `1/N` term away** — at σ ≲ 5° no tolerance can detect its absence, which is why a named positive control guards it |

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

⚠️ **EQ-035–EQ-053 are NOT covered by the verification dates above.** They were added by the
2026-08-02 `indexer` pass from docstring citations already present in the code. The registry
holds **no verification record** for them — which is a statement about this file, not an
assertion that they were never checked: the mandatory workflow requires a `researcher` pass
*before* implementation, so some or all may well have been verified at the time and simply
never recorded here. Either way the gap is real and only a fresh `researcher` pass closes it.
Five rows rested on **equation numbers new to this registry** ([FH] 2.22, 3.11, 4.30, 4.35;
[B] 123a). **EQ-040 was flagged as the one to look at first — and it was wrong.** ✅ **Resolved
2026-08-03** by a batched `researcher` pass plus independent verification: [FH] eq. 4.22 is the
TT projector (EQ-004's citation, correct), the e^(2iψ) rotation law is **not in that paper at
all**, and EQ-040 now cites Mashhoon & Rahvar eq. 4. The same pass read [FH] eq. 2.22 directly,
which **partially vindicated** EQ-038/039 and **undercut** EQ-035 — see those rows.
✅ **Sweep completed 2026-08-03 — all remaining new equation numbers read at source.**
Both papers were downloaded and their text extracted locally rather than trusted to a summary,
because EQ-040 had just shown that a plausible equation number in the right paper can point at
the wrong equation. Outcome: **two verified exactly** — [FH] eq. 3.11 (EQ-045, geodesic
deviation) and [FH] eq. 4.30 (EQ-041, dipole moment) — and **two verified but overstated in
scope**, now reclassified VERIFIED→DERIVED: [FH] eq. 4.35 (EQ-042) is the *first* derivative
`dM₁/dt = P`, not the second; and [B] eq. 123a (EQ-044) is Theorem 6's general
*post-Newtonian* multipole, not the Newtonian point-mass octupole. Neither is a physics error —
in both cases the function's own prose was already accurate and only the `Source:` line
overreached. **Every equation number in this registry has now been read at its source**, except
where the row itself says otherwise (EQ-019 Dolph/Taylor, EQ-023's unnumbered display equation,
EQ-034's deliberately unnumbered Thorne, EQ-035 — see that row).

⚠️ **Registry/Module-Map drift found and reconciled, 2026-08-02 (`indexer` pass).** Seven live
modules (`source/multipole_rad.py`, `propagate/polarization.py`, `target/geodesic.py`,
`target/deflection.py`, `viz/slices.py`, `viz/volume.py`, `viz/export_vtk.py`) were still marked
*"not yet implemented"* in §2, and six more rows (`array/focus.py`, `array/beamform.py`,
`bodies/multipole.py`, `target/coupling.py`, `kinematics/profiles.py`, `core/backend.py`,
`viz/patterns.py`) omitted functions that had landed with citations. §1 was missing 19 rows.

**How it was caught, and why nothing caught it sooner.** By an `indexer` pass working from
`grep`-extracted `^def`/`^class`/`Source:` lines against the two documents. `check_citations.py`
passes throughout — it verifies a citation *exists in the docstring*, never that the registry
reflects it, so the entire drift was invisible to CI by construction. This is the failure mode
CLAUDE.md rule 8 names: nothing was wrong, nothing was reported, and the map quietly stopped
describing the territory.

**Two structural findings, recorded rather than fixed:**

1. **A correction was written but never applied.** The "✅ Resolved 2026-07-31" note below the
   §2 table states that the `array/beamform.py` row's stale `superpose_tt` claim was a forward
   reference to unbuilt code and that T-6.5/T-6.6 had landed — but **the row itself was never
   edited**, so the note and the row it corrected contradicted each other for at least one
   indexer cycle. A resolution note is not a substitute for the edit.
2. **The stale claim is also in the source code.** `src/gwtb/array/beamform.py`'s module
   docstring says `superpose_tt` is "not yet implemented" — 370 lines above its own definition.
   That is almost certainly the *origin* of the index drift, since an indexer trusting the module
   docstring would reproduce it. **Left uncorrected here deliberately** (this pass was scoped to
   documentation); it needs a one-line source edit under the normal workflow.

**Deliberately not registered:** `bodies/multipole.py:LongWavelengthAssumptionWarning`. Its
docstring cites `eq. n/a — a governance class, not a physics result`, the same category as
`core/backend.py:PrecisionError` and `target/coupling.py:CouplingResult`, neither of which has
or needs a row.

🚨 **Out of scope for this pass, and worse than what it fixed: §4 Validation Status is not
stale, it is ABSENT** for roughly 30 completed tasks — T-2.3/2.4/2.5, T-3.1–3.6, T-5.1–5.4,
**T-6.5/T-6.6**, T-7.1–7.3/7.6–7.8, T-8.1–8.4/8.6–8.8, T-9.7, T-10.3–10.7, T-11.4/11.5/11.7.
The tests exist and pass; only the rows are missing. **The most serious single gap is T-6.5/T-6.6
(EQ-047/EQ-048)** — the spin-2 tensor superposition, this project's highest-risk equation and
the discharge of claim B-1, has **no row in the validation table at all.** Per §4's own rule an
unvalidated benchmark is not passing; an *unlisted* one cannot even be checked for staleness.
This should be the next `indexer` task.

---

## 2. Module Map

| Module | Purpose | Public API | Depends on |
|---|---|---|---|
| `core/constants.py` | Physical constants with sources | **live** — `G`, `c`, `AU`, `M_SUN`, `PARSEC`, `G_OVER_C4/5`, `TARGET_RANGE` | — |
| `core/units.py` | Scaled strain representation | **live** — `StrainScale` | `constants` |
| `core/backend.py` | Array-API shim (numpy / numba) | **live** — `get_backend`, `Backend` (T-11.1; no citation requirement, infrastructure only); `field_grid`, `_field_grid_loop` (T-11.2; Numba-JIT-compilable TT-strain superposition over a field-point grid, one already-evaluated `q_ddot` per source shared across the whole grid — see Assumption Ledger for the light-crossing-time restriction this imposes); `SplitPhase`, `split_phase` (T-11.3; FP64 reference phase + FP32-safe differential — use `.phasor()`, **not** `.recombine()`, which is irreducibly lossy at astronomical range); `field_grid_split_phase` (T-11.4; NumPy/CuPy-agnostic per-element phasor kernel for the optional GPU backend); `assert_phase_precision`, `PrecisionError` (T-11.5; guards float32 phase outside `split_phase`'s own authorized differential term); `field_grid_chunked` (T-11.7; memory-bounded chunked evaluation of `field_grid`, identical to rtol 1e-12) | `core/constants`, `core/validation` (**not** `source/quadrupole` — `q_ddots` are caller-supplied, never imported) |
| `bodies/sphere.py` | Rigid uniform sphere; mass/inertia; rotational-oblateness quadrupole | **live** — `Sphere` (dataclass: `radius`, `density`, `.mass`, `.moment_of_inertia`, `.self_quadrupole()`), `oblateness_quadrupole` (T-4.1/4.2/4.6) | `constants` |
| `bodies/elastic.py` | Love-number deformation; breaks R/ρ degeneracy | **live** — `love_number_k2`, `induced_quadrupole` (T-4.3). **This is where the rigid model's mass/radius/density degeneracy breaks**: `Q ∝ R⁵` explicitly and `ρ` enters through `μ̃`, so equal-mass spheres are no longer radiatively identical (asserted against T-4.2 in `test_elastic.py`) | `sphere`, `constants`, `core/validation` |
| `bodies/multipole.py` | Mass multipole moments and derivatives; finite-size correction | **live** — `quadrupole_moment`, `quadrupole_second_derivative`, `quadrupole_third_derivative` (T-1.3–1.5 — ⚠️ the previous version of this row named these `_second_derivative`/`_third_derivative`, which have **never** been the actual names); `octupole_moment` (T-2.5, EQ-044 — ⚠️ **no caller anywhere in `src/`, and none planned. Decided 2026-08-03: retained deliberately, marked speculative, no caller to be built.** It is a mass *moment*, not a radiation channel; **the framework has no `l = 3` radiative path**. Higher multipoles were on the radar only for the long-wavelength breakdown of `PHYSICS.md` §3, and that question was answered instead by `finite_size_correction` (EQ-034/ADR-0007) — so this is a road not taken, not a missing feature. Guarded executably: `strain_tt` rejects a `(3,3,3)` input, asserted by `test_octupole_cannot_be_fed_to_the_quadrupole_radiation_path`); `finite_size_correction`, `LongWavelengthAssumptionWarning` (T-4.5/T-4.7, EQ-034, see [ADR-0007](adr/0007-uniform-sphere-quadrupole-form-factor.md)) | `bodies/sphere`, `core/validation` (**not** `core/constants`) |
| `kinematics/profiles.py` | Finite-maneuver acceleration profiles | **live** — `AccelerationProfile` (base, T-3.1), `BangBangProfile` (T-3.2), `SCurveProfile` (T-3.3), `QuinticProfile` (T-3.4), `RaisedCosineProfile` (T-3.5), `spectrum` (T-3.6, frequency-domain view); helpers `_finish`, `_prepare_time` | `core/validation` |
| `kinematics/oscillators.py` | Prime-frequency multi-tone drive synthesis | **live** — `first_n_primes`, `prime_frequencies`, `recurrence_period`, `PrimeOscillatorDrive` (T-9.1–9.4; DSP/kinematic module, exempt from citation-CI) | `profiles`, `core/validation` |
| `source/quadrupole.py` | Quadrupole radiation, luminosity, and maneuver waveforms | **live** — `strain_tt`, `luminosity`, `waveform_from_profile` (T-3.8, adds symmetric two-body maneuver modeling) | `multipole`, `tt_projection`, `bodies/sphere`, `kinematics/profiles` |
| `source/multipole_rad.py` | Mass dipole moment and derivative; flagged dipole-strain diagnostic | **live** — `dipole_moment`, `dipole_second_derivative` (T-2.3, EQ-041/042), `dipole_strain` (T-2.4, EQ-043). 🚨 **`dipole_strain` output is ALWAYS stamped `UNPHYSICAL` regardless of input** — this is the ~10¹⁰× mass-dipole artifact CLAUDE.md rule 2 exists to contain. Never strip the stamp; never read as a physical result | `core/constants`, `core/validation`, `propagate/tt_projection`, `source/conservation` (**not** `bodies/multipole`) |
| `source/memory.py` | Linear GW memory from finite maneuvers | **live** — `linear_memory` (T-3.7; non-relativistic limit of Favata eq. 10k). Cross-validated against the independent quadrupole route to machine precision — see ADR-0004 | `tt_projection`, `constants`, `core/validation` |
| `source/conservation.py` | ∂_μT^μν audit; `UNPHYSICAL` stamping | **live** — `audit`, `ConservationReport` (T-2.1); `StampedResult`, `StampStrippedError`, `UNPHYSICAL_STAMP` (T-2.2). Two layers: `audit` *detects* non-conservation, `StampedResult` *propagates* that verdict through arithmetic so it cannot be laundered. See ADR-0005 for why it is a wrapper and not an `ndarray` subclass | `core/validation` |
| `propagate/tt_projection.py` | Transverse-traceless projector | **live** — `tt_projector`, `apply_tt`, `transverse_projector` | — |
| `propagate/polarization.py` | Spin-2 polarization basis; e^(2iψ) rotation; TT decomposition/recomposition; quadrupole element patterns | **live** — `polarization_basis` (T-5.1, EQ-035), `decompose`/`recompose` (T-5.2, EQ-038/039), `rotate_polarization` (T-5.3, EQ-040), `element_pattern_rotating`/`element_pattern_linear` (T-5.4, EQ-036/037). ⚠️ **This module carries genuine spin-2 physics** — unlike `array/beamform.py`'s scalar functions, it must never be replaced by a spin-1 analogue (rule 4). Rotation period in ψ is **180°, not 360°** | `core/validation` (**not** `propagate/tt_projection` — referenced in docstrings, not imported) |
| `propagate/retarded.py` | Per-source retarded-time field evaluation | **live** — `PointSource` (dataclass), `field_at` (T-6.7; retards each source individually — see module docstring on why a shared array-centroid retardation would be wrong), `propagate` (T-6.8; batches `field_at` over field points × times, shape `(M, T, 3, 3)`) | `source/quadrupole`, `core/constants` |
| `array/geometry.py` | Element placement | **live** — `linear_array`, `planar_array`, `sparse_array` (T-5.5–5.7) | — |
| `array/beamform.py` | Scalar array factor, steering, beamwidth/sidelobes, tapering; **and** spin-2 tensor superposition | **live, and the module is deliberately two things at once** — (a) `array_factor`, `steering_phases`, `beamwidth_3db`, `peak_sidelobe_level`, `taper` (T-6.1–6.4, EQ-016–019) are the **spin-1/scalar baseline**, pure classical array theory, never to be read as gravitational radiation; (b) `QuadrupoleElement`, `superpose_tt`, `mismatch_loss` (T-6.5/6.6, EQ-046–048) carry the **spin-2 physics**, per [ADR-0003](adr/0003-spin2-superposition.md). ⚠️ **Keep the two halves distinct — this is rule 4's highest-risk boundary, and it runs through the middle of one file.** ⚠️ The module's own docstring still calls `superpose_tt` "not yet implemented" 370 lines above its definition; that source-level staleness is a known finding, see the drift note in §1 | `core/validation`, `propagate/tt_projection` (**not** `array/geometry`) |
| `array/grating.py` | Grating-lobe and spacing constraints | **live** — `max_spacing`, `has_grating_lobes` (T-5.8) | `geometry` |
| `array/focus.py` | Spatiotemporal focusing; focus kinematics; array trade studies | **live, complete** — `focal_phases` (T-9.5, EQ-029/030), `focused_phasor`/`focused_field` (T-9.6, EQ-032), `spot_size`/`FWHM_COEFFICIENT` (T-10.1, EQ-033), `focus_trajectory` (T-9.7, EQ-049), `dwell_time` (T-10.3, EQ-050), `peak_to_sidelobe` (T-10.4, EQ-051), `band_sweep` (T-10.5, EQ-052), `trade_surface` (T-10.6, EQ-053). The previous version of this row listed the last five as unimplemented. Far-field only per [ADR-0006](adr/0006-focused-field-far-field-regime.md); near-field requests **raise — propagate that error, do not catch it** | `array/beamform`, `core/constants`, `core/validation`, `kinematics/oscillators` (**not** `array/geometry`) |
| `target/geodesic.py` | Geodesic deviation at the target | **live** — `deviation_acceleration` (T-8.1, EQ-045). This is the mechanism every `target/coupling.py` channel acts through: a GW produces **tidal strain, not net force** | `core/validation` |
| `target/coupling.py` | All three coupling channels, reported side by side | **live** — `tidal_strain`/`channel_tidal` (T-8.2/8.3), `channel_absorption` (T-8.4), `channel_gravity_tractor` (T-8.5, EQ-023), `CouplingResult` (T-8.3), `channel_gravity_tractor_result`/`compare_channels` (T-8.6). **All three channels from the module's original scope are now live** — the previous version of this row said the other two were unimplemented. Reporting them side by side rather than assuming radiated power converts to thrust is the module's whole point | `core/constants`, `ledger/gap_report` |
| `target/deflection.py` | Impulse → Δv → miss distance | **live** — `delta_v` (T-8.7), `miss_distance` (T-8.8). **Deliberately uncited**: both are elementary Newtonian mechanics (impulse-momentum; linearized orbital displacement), not GW physics, so rule 1's numbered-equation requirement does not apply — the module docstring says so explicitly. Where a *number* is checked it is cited: `delta_v` reproduces DART's measured Dimorphos deflection (1.16e7 N·s on 4.3e9 kg → 2.7 mm/s) to **rtol 1e-2**, cited to Daly et al. 2023 | `core/constants` (**not** `target/coupling`) |
| `ledger/gap_report.py` | Feasibility ledger | **live** — `GapMetric`, `GapReport`, `GapMetric.from_stamped` (T-2.6), plus row-builder wrappers `emission_gap` (T-2.7), `aperture_gap` (T-5.9), `impulse_gap` (T-8.9), `focusing_gap` (T-10.8), `body_quadrupole_gap` (T-4.9). **Schema is FROZEN**: `name, achieved, required, units, source_module, provenance` is a contract every epic writes to; `test_gap_report.py` pins the field set *and order* so a breaking change fails loudly. **Use `from_stamped()`** for any value originating as a `StampedResult` — the plain constructor would compile while discarding the stamp | `source/conservation` (for `UNPHYSICAL_STAMP`, `StampedResult`) |
| `viz/patterns.py` | Beam-pattern visualization (polar + 3D) | **live** — `plot_pattern_polar`, `plot_pattern_3d` (T-7.4/7.5; headless `Agg` backend; reimplements array-factor math vectorized for full-grid rendering rather than calling `beamform.array_factor` per point — kept numerically consistent by shared test coverage, not by a shared code path); `plot_polarization_ellipse` (T-7.6); `plot_trade_surface` (T-10.7, renders `array/focus.py:trade_surface`) | `array/beamform` (mathematically, not by import) |
| `viz/slices.py` | 2D strain-field slice extraction, heatmaps, propagation animation | **live** — `FieldSlice`, `extract_slice`, `plot_strain_slice` (T-7.1/7.2), `animate_propagation` (T-7.3); headless `Agg` backend as in `patterns.py` | — (the caller supplies the `field` callable, e.g. `propagate/retarded.field_at`; no direct import) |
| `viz/volume.py` | 3D volumetric field rendering | **live** — `render_volume` (T-7.7). Optional `pyvista` dependency: **returns `None` with a message** when absent, does not raise | optional: `pyvista` |
| `viz/export_vtk.py` | ParaView/VTK `.vti` export | **live** — `export_field` (T-7.8). Optional `pyvista` dependency: **raises `RuntimeError`** when absent — note this deliberately differs from `render_volume`'s degrade-quietly path | optional: `pyvista` |
| `core/validation.py` | ADR-0002 shape/dtype/unit-vector guards | **live** — `as_masses`, `as_body_array`, `as_tensor_3x3`, `as_unit_vector`, `as_float64` | — |

✅ **Resolved 2026-07-31.** The note that previously stood here flagged `superpose_tt` (T-6.5)
as a forward reference to unbuilt code. **T-6.5 and T-6.6 have since landed** — `superpose_tt`
and `mismatch_loss` are live in `array/beamform.py`, per ADR-0003. The standing caution still
holds and is not withdrawn: `array_factor`, `steering_phases`, `beamwidth_3db`,
`peak_sidelobe_level` and `taper` remain the **scalar spin-1 baseline**, and only
`superpose_tt`/`mismatch_loss` carry spin-2 physics. Do not read the former as gravitational
radiation (CLAUDE.md rule 4).

> ⚠️ **Correction, 2026-08-02.** This note was written on 2026-07-31 but **the row it
> corrects was never actually edited** — the Module Map went on saying `superpose_tt` was
> "not yet implemented" for another two days, directly contradicting the paragraph above it.
> The row is fixed now. **A resolution note is not a substitute for the edit**; when
> resolving a stale entry, change the entry, then record that you changed it.

✅ **Resolved 2026-08-02 — `focused_field` exists, and so does everything else in that
module.** T-9.6 landed (with T-9.7 and T-10.3–10.6); `array/focus.py` is complete. The
paragraph below is **retained verbatim as the historical record of the state it describes**,
per the file's own convention — do not delete it. Note that the "✅ The design tension is
resolved" note two paragraphs down presupposes `focused_field` exists but never says so
outright, which is very likely why the false "does not" claim below survived unread.

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
| Long wavelength (R ≪ λ) | Quadrupole approximation | Source size ≪ λ | **Violated for large spheres at high frequency.** Motivates `bodies/` finite-size corrections. **Enforced at runtime** (T-4.7): `bodies/multipole.py:finite_size_correction` raises `LongWavelengthAssumptionWarning` at `R/λ ≥ 0.1`, naming this row |
| Slow motion (v ≪ c) | Quadrupole formula, memory | v/c ≪ 1 | Assumed throughout; must be checked per configuration |
| Momentum conservation | Default source mode | Reaction mass in model | **Deliberately violated** in external-reservoir mode; outputs stamped `UNPHYSICAL` |
| Non-dispersive propagation | Focusing analysis | Vacuum GR | Holds in vacuum. Means a temporal focus propagates rather than standing still |
| FP64 sufficient for phase | All field evaluation | — | Adequate to ~10¹⁰ wavelengths. FP32 is **not**; see `PHYSICS.md` §7 |
| Rigid point-mass sphere (no self-quadrupole) | `bodies/sphere.py:Sphere.self_quadrupole` | Rigid, undeformed, non-spinning body; only trajectory radiates | Breaks down once the body deforms (elastic — **T-4.3 is built**: `bodies/elastic.py`, EQ-027/028; the "not yet built" that stood here until 2026-08-02 was the same drift class as the §2 Module Map, found incidentally while fixing it) or spins (see next row) |
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
| **(R, ρ) sensitivity study (T-4.8)** | claim B-2 (both halves) | **PASSING** — `tests/benchmarks/test_body_sensitivity.py`. A 5-point sweep across two orders of magnitude in `R` at fixed `M`: rigid-model radiation stays at machine-zero (measured floor 1e-15, three orders tighter than the AC's 1e-12), elastic-model radiation varies by ~7.6e4–1.0e5× (eight orders above the AC's 1e-3) across steel/tungsten/osmium. A leaked R-dependent term as small as 1e-14 in the rigid path was confirmed to trip the floor check |
| **Finite-size form factor (T-4.5 / SPIKE-4.5)** | EQ-034 | **PASSING** — `tests/unit/test_multipole.py`. Checked against the exact closed form (ADR-0007 eq. 4, via `scipy.special.sici`) with the *discarded series tail* asserted rather than a flat tolerance, so the test is sensitive to the `(kR)²` coefficient itself. **Mutation-tested:** replacing `5/98` with `1/6`, `1/10`, `1/14`, a sign flip, a 0.1% nudge, or even a **0.001% nudge** each fails 4–5 tests. Note the "tends to unity" test is *not* what catches them — it passes for every wrong coefficient except the sign flip; `test_finite_size_correction_coefficient_is_exactly_5_over_98` is the load-bearing pin. Regression guards name both wrong form factors explicitly (rule 4). Independent numerical verification lives in `scratchpad/spike_4_5.py`, not in the suite — it takes ~20 s and its results are recorded in ADR-0007 |
| Focal phase solution (T-9.5) | EQ-029, EQ-030 | **PASSING** — `tests/unit/test_focus.py`, verified against 60-digit `decimal` reference ranges rather than the implementation's own float64 arithmetic |
| Split-phase decomposition (T-11.3) | EQ-030, EQ-031 | **PASSING** — `tests/unit/test_split_phase.py`, including the required demonstration that naive FP32 **fails** the same check, and the stronger finding that naive float64 does too |
| `UNPHYSICAL` stamp propagation (T-2.2) | — (governance, no equation) | **PASSING** — `tests/unit/test_stamped_result.py`, 36 tests covering arithmetic, slicing, `str()`, JSON, and refusal of `np.asarray`/`np.array`/`out=` |
| Ledger schema round-trip and stable rendering (T-2.6) | — (schema, no equation) | **PASSING** — `tests/unit/test_gap_report.py`, field set and order pinned against the freeze |
| **Body-parameter ledger row (T-4.9)** | — (schema wrapper, no equation) | **PASSING** — `tests/unit/test_gap_report.py`. `body_quadrupole_gap` fixes `name`/`units`; achieved/required are caller-supplied, so no new physics is introduced (`ledger/` is exempt from `check_citations.py` for this reason). End-to-end test reuses T-4.8's fixed-mass sphere fixture and its measured elastic-quadrupole magnitude rather than an arbitrary number |
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
| **Spin-2 tensor superposition and mismatch loss (T-6.5/T-6.6)** | EQ-046, EQ-047, EQ-048; claim **B-1**; [ADR-0003](adr/0003-spin2-superposition.md) | **PASSING** — `tests/unit/test_superposition.py`. **The project's highest-risk equation class, with no external reference implementation** (rule 4). Coverage, clause by clause: reduces to the scalar spin-1 array factor for co-oriented elements at **rtol 1e-9, atol 1e-15** (the regression proving the extension is a controlled departure, not a rewrite); result symmetric/traceless/transverse to atol 1e-15; 45°-apart elements give gain **exactly 2.0 (abs 1e-9)** and strictly < N²; **the 90° complete cancellation is guarded by name** — `test_elements_ninety_degrees_apart_cancel_completely`, asserting `max\|h\| < 1e-15` with the docstring "*An array laid out on antenna reasoning with elements at 90 degrees radiates NOTHING along its intended axis. Asserted explicitly so nobody 'fixes' it*"; near-field input **raises** `ValueError(match="near field")` rather than degrading; `cos(2Δψ)` pinned at **7 parametrized angles** (0/22.5/30/45/60/90/180°) to abs 1e-12; `test_maximal_mismatch_at_45_not_90` and `test_period_is_pi_not_two_pi` both present by name; radiation along an element's own axis raises. **Alignment tolerance (EQ-054) rebuilt 2026-08-03**: now asserts the bias-corrected `exp(−4σ²) + (1−exp(−4σ²))/N` to **5 standard errors of the estimator's own sampling distribution**, over σ ∈ {2.87°, 5°, 10°, 20°} (N=200, 50,000 realizations, seeded), plus a parametrized positive control `test_uncorrected_asymptotic_law_is_rejected_at_finite_n`. ⚠️ **The tolerance is statistical, not absolute, deliberately** — the SE spans 30× across this σ range, and a flat `abs=1e-4` sat at 0.7 SE at σ = 20°, failing 13 of 30 reseeds while passing on the committed seed. Do not reintroduce a flat one. Seed-robust (0/40) and discriminating at **every** σ: dropping the `1/N` term is rejected by 2.2–2.9×. ✅ **Analytic-TT pin committed 2026-08-03**, closing the last ADR-0003 gap: `test_tt_projection_matches_the_analytic_closed_form` and `test_superposition_reproduces_the_analytic_form_through_the_production_path` reproduce the hand-derived `h^TT = ½[[cos2ψ, sin2ψ],[sin2ψ, −cos2ψ]]` to **atol 1e-14** across the nine ψ of SPIKE-4.4, and `test_tt_tensor_period_in_psi_is_pi_not_two_pi` asserts the half-period **inversion** `h(ψ+π/2) = −h(ψ)` — the clause that rules out period 2π rather than merely being consistent with π. Measured worst error **1.1e-16**, so ADR-0003 was *conservative* here (the opposite direction to its alignment claim). Mutation-checked: a spin-1 (single-angle) implementation is rejected by ~1e-1, twelve orders outside tolerance |
| Mass dipole moment and derivative (T-2.3) | EQ-041, EQ-042 | **PASSING** — `tests/unit/test_multipole_rad.py`. `d_i = Σm x_i` and `d̈_i = Σm a_i` to **rtol 1e-15**; vanishes for a symmetric pair (atol 1e-15) and for a momentum-conserving configuration; nonzero for an unbalanced one — the positive control that keeps the null result meaningful. Float32 rejected, not promoted |
| **Flagged dipole strain — always `UNPHYSICAL` (T-2.4)** | EQ-043 | **PASSING** — `tests/unit/test_multipole_rad.py`. 🚨 The ~10¹⁰× artifact CLAUDE.md rule 2 exists to contain. `test_always_returns_a_stamped_result` pins that the stamp is unconditional; `test_raises_for_momentum_conserving_source` pins that the function **refuses** the physical case rather than silently returning ~0; `allow_trivial` permits the zero case **and still stamps it**. Physics checks: symmetric (rtol 1e-14), transverse, independent of `r` (rtol 1e-12), quadratic in `d̈` (rtol 1e-13), vanishing when `d̈ ∥ n̂` (atol 1e-30) |
| Mass octupole (T-2.5) | EQ-044 | **PASSING, and now externally anchored (2026-08-03).** `tests/unit/test_multipole.py` asserts full symmetry, tracelessness on **every** index pair, vanishing for a symmetric pair, and dtype/shape contracts — and, new, **`test_octupole_reproduces_blanchet_two_body_newtonian_octupole`** across five mass ratios (rtol 1e-12, atol 0), placing the bodies at `y₁ = (m₂/m)x`, `y₂ = −(m₁/m)x` and reproducing [B] eq. 302a's Newtonian leading term `I_ijk = −νm∆x⟨ijk⟩`. Until this date that cross-check was **asserted in the docstring and executed nowhere** — the same defect class as ADR-0003's analytic-TT figure. **Mutation-checked:** perturbing the STF trace coefficient from `/5` to `/3`, `/7` or even `/5.05` is caught (rel dev 1.4, 0.61, 2.1e-2); the reference fixes `/5` from the STF *definition*, not from the code, which is what gives it that power. A companion test pins the equal-mass null on the `∆ = 0` prefactor, so it fails for a different cause than the pre-existing odd-moment symmetry test |
| Acceleration profiles and spectra (T-3.1–T-3.6) | — (kinematics, no equation) | **PASSING** — `tests/unit/test_profiles.py`. Each profile's velocity and position are checked against numerical integration of the derivative below it — see the in-file comment on `test_position_matches_integral_of_velocity` for **why the tolerance is set by quadrature error across kinks, not by the code** (this is the "fix the measurement, never the tolerance" case). Bang-bang reproduces the rectangular-window **−13.3 dB** first sidelobe (abs 1.0); raised-cosine matches a Hann window's spectral rolloff to rtol 1e-6/atol 1e-9; `spectrum` satisfies **Parseval to rel 1e-9** and reproduces −13.0 dB (rect) and −31.0 dB (Hann) sidelobes. The acceleration profile *is* the transmit pulse shape |
| Spin-2 polarization basis, rotation, decomposition, element patterns (T-5.1–T-5.4) | EQ-035–EQ-040 | **PASSING** — `tests/unit/test_polarization.py`. Basis traceless/transverse (atol 1e-15) and orthonormal under double contraction (`e:e = 2`, abs 1e-12); **`test_frame_rotation_transforms_amplitudes_by_exp_2i_psi`** and **`test_basis_has_period_pi_not_two_pi`** pin the spin-2 signature by name — the latter asserting `e(ψ+π) = +e(ψ)` *and* `e(ψ+π/2) = −e(ψ)`, which is what distinguishes spin-2 from spin-1; a 45° rotation maps `e₊ → e_×` (atol 1e-12), the 45°-not-90° separation. Element patterns checked against an independent quadrupole calculation (abs 1e-9 linear, 1e-12 rotating), including the face-on-circular / edge-on-linear limits. `decompose`/`recompose` round-trip to rtol 1e-12 and project out non-TT components |
| Geodesic deviation at the target (T-8.1) | EQ-045 | **PASSING** — `tests/unit/test_geodesic.py`. Matches `½ḧξ` to rtol 1e-14; linear in both `h` and `ξ`; transverse to the propagation direction across seeded random cases; separation purely along propagation gives zero (atol 1e-12). **`test_net_acceleration_of_the_center_of_mass_is_zero` (atol 1e-12) is the load-bearing one** — it encodes claim A-6, that a GW produces tidal strain and **not** net centre-of-mass acceleration, paired with a positive control showing relative acceleration between two bodies is generically nonzero |
| Coupling channels: tidal, absorption, gravity tractor (T-8.2–T-8.4, T-8.6) | EQ-023 | **PASSING** — `tests/unit/test_coupling.py`. Gravity tractor reproduces **both** worked examples from the source paper (Apophis 0.053 N; 2004 VD17 0.092 N, each rel 1e-2) and scales as `1/d²`. Tidal strain matches `½hR` (rel 1e-14). **`test_channel_absorption_below_1e_30_n_for_1km_asteroid_at_40au` pins the coupling wall numerically.** Type discipline is enforced structurally: `CouplingResult` requires **exactly one** of strain/force, so `channel_tidal` cannot return a force — and **`test_compare_channels_never_sums_the_rows`** guards the category error of adding a strain to a force |
| Impulse → Δv → miss distance (T-8.7/T-8.8) | — (elementary Newtonian, deliberately uncited) | **PASSING** — `tests/unit/test_deflection.py`. **`test_dart_cross_check`** anchors the chain against reality: 1.16e7 N·s on 4.3e9 kg → 2.7 mm/s, **rel 1e-2**, cited to Daly et al. 2023. Both relations linear in their arguments to rel 1e-14; `miss_distance` matches its closed form to rel 1e-12 and **rejects a lead time exceeding the orbital period** rather than extrapolating past its validity |
| Focus trajectory and dwell time (T-9.7, T-10.3) | EQ-049, EQ-050 | **PASSING** — `tests/unit/test_focus_trajectory.py`. **`test_focus_moves_at_exactly_c` (rtol 1e-12) and `test_focus_does_not_remain_stationary` together encode the physical wall**: GWs are non-dispersive in vacuum, so a temporal focus is a converging-then-diverging pulse that *propagates*, never a stationary hot spot. Trajectory passes through the focal point at the focal time (rtol 1e-9); `dwell_time = 1/B` to rel 1e-14 |
| Peak-to-sidelobe ratio (T-10.4) | EQ-051 | **PASSING** — `tests/unit/test_focus_trajectory.py`. Ratio scales as `√N` across seeded sparse arrays (rel 0.1); steered peak matches `N` to rel 1e-9. ⚠️ **`test_peak_to_sidelobe_uniform_ratio_matches_sqrt_n_only_by_coincidence` is the anti-vacuity guard** — it records that a well-spaced uniform array hitting `√N` is coincidence, not the mode-locking mechanism, so the `√N` assertion cannot be satisfied for the wrong reason |
| Band sweep, f⁶ scaling (T-10.5) | EQ-052 | **PASSING** — `tests/unit/test_focus_trajectory.py`. Reproduces `f⁶` across the band to rtol 1e-6, and **`test_band_sweep_spans_about_36_decades` (abs 0.1) pins the magnitude wall**: ~36 orders of magnitude between 1 Hz and 1 MHz operation. This is a wall, not a bug (rule 5) |
| Aperture/frequency trade surface (T-10.6) | EQ-053 | **PASSING** — `tests/unit/test_focus_trajectory.py`. Matches the closed form to rtol 1e-12 and reproduces **both** reference points — **1.8e18 m at 1 Hz and 1.8e12 m at 1 MHz** (rel 0.03). ⚠️ **This is the diffraction wall (claim B-3) in solved-for-`D` form.** Those two numbers are ~1.2e7 AU and ~12 AU respectively. If a change shrinks them, suspect the change |
| Field slices, heatmap, wavefront animation (T-7.1–T-7.3) | — (visualization, no equation) | **PASSING** — `tests/unit/test_slices.py` (13 tests), headless `Agg`. Slice geometry, plane-axis selection and extent-to-coordinate mapping verified against the requested extent; the colorbar is asserted **symmetric about zero** (a sign-legibility property, not cosmetics); zero-field input does not crash; `animate_propagation` writes a GIF with frame count matching the requested times |
| Polarization ellipse (T-7.6) | — (visualization; depicts EQ-035/EQ-039) | **PASSING** — `tests/unit/test_polarization_ellipse.py`. Pure `h₊` stretches along the axes (1.25 / 0.75 at ±½h, rel 1e-12); **pure `h_×` deforms at 45°, not 90°** — the spin-2 signature made visual; the two produce the same shape rotated (rtol 1e-3); zero strain gives a unit circle (rtol 1e-12) |
| Volumetric rendering and VTK export (T-7.7/T-7.8) | — (visualization, no equation) | **PASSING** — `tests/unit/test_volume.py`, `test_export_vtk.py`. **These 2 tests skip without the optional `pyvista` extra.** The asymmetry is deliberate and asserted: `render_volume` **degrades quietly** (returns `None` with a message), `export_field` **raises** `RuntimeError`. When PyVista is present, exported `.vti` reloads via `pyvista.read` with matching shape and values |
| Trade-surface visualization (T-10.7) | — (visualization; renders EQ-053) | **PASSING** — `tests/unit/test_patterns.py`. Renders headless; **asserted to use log–log axes and to annotate the frequency-invariance of `D/λ`** — i.e. the plot is required to *state the wall it depicts*, not merely draw it |
| GPU backend, precision guard, chunked evaluation (T-11.4, T-11.5, T-11.7) | — (infrastructure, no equation) | **PASSING** — `tests/unit/test_backend.py`, `test_split_phase.py`. CuPy path agrees with the NumPy reference to rtol 1e-5 (**this 1 test skips without CuPy**, which is not a declared extra) and raises a clear error when CuPy is absent. `assert_phase_precision` **raises on unauthorized float32 phase** and passes float64 regardless of authorization; **`test_split_phase_differential_is_the_one_authorized_float32_call_site`** pins ADR-0002 §5's single carve-out so it cannot quietly widen. Chunked evaluation matches unchunked to rtol 1e-12 independent of chunk size, and a 512³ grid completes within a 4 GB budget |

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

**Updated 2026-08-02 (second pass) — this table was ABSENT, not stale, for ~30 completed
tasks.** The reconciliation of §1/§2 earlier the same day (see the drift note at the end of §1)
exposed that §4 had no rows at all for T-2.3/2.4/2.5, T-3.1–3.6, T-5.1–5.4, **T-6.5/T-6.6**,
T-7.1–7.3/7.6–7.8, T-8.1–8.4/8.6–8.8, T-9.7, T-10.3–10.7 and T-11.4/11.5/11.7. All tests
existed and passed throughout; only the rows were missing. **This is the more serious half of
that drift**: §4's own rule says a benchmark that has not run since the code it validates last
changed is *stale, not passing* — but an **unlisted** benchmark cannot even be checked for
staleness, so the gap was structurally invisible. Rows are now written from the assertions
themselves; every tolerance quoted above was read out of the test that asserts it.

**Worst instance, now closed:** T-6.5/T-6.6 — the spin-2 tensor superposition, this project's
highest-risk equation class and the discharge of claim B-1 — had **no validation row at all.**

**Two findings surfaced while writing these rows. Neither is fixed here.**

1. ✅ **RESOLVED 2026-08-03 — and the diagnosis inverted the fix.** The finding as first
   written (retained below) assumed the *test* was the weak party and proposed tightening it
   to ADR-0003's ~1e-4. **That was impossible, and the ADR was the defective document.**
   `exp(−4σ²)` is the `N → ∞` limit; at finite `N` there is an exact positive bias
   `(1−exp(−4σ²))/N` that neither document named. At the test's `N = 200` the bias *alone* is
   5.7e-4, so no tolerance there could ever reach 1e-4 — the old `abs=2e-3` was **correctly
   sized, not sloppy**. Meanwhile ADR-0003's "~1e-4" is contradicted by its own printed table
   (8.8e-4 at σ = 20°) and is unreachable at the `N = 100` it also cites (bias alone 3.9e-3).
   Closed by: an ADR-0003 amendment deriving the bias; EQ-054; a rebuilt test asserting the
   *corrected* prediction to 5 standard errors (statistical, not absolute — a flat `abs=1e-4`
   failed 13 of 30 reseeds at σ = 20°) with a parametrized positive control; and
   `scratchpad/spike_b1_alignment_bias.py` as committed evidence. **No claim demoted** — the
   bias is positive, so a finite array marginally beats the law, and σ ≤ 2.87° stands.
   *Original finding, retained:*

   > ⚠️ **The `exp(−4σ²)` alignment test is materially weaker than the claim it is cited for.**
   > [ADR-0003](adr/0003-spin2-superposition.md) §3 reports the law matching measurement **to
   > ~1e-4 across σ ∈ [0°, 20°] at N = 100 and N = 1000**, and `CLAIMS.md` B-1 rests on that.
   > `test_alignment_tolerance_matches_adr_prediction` actually asserts **abs 2e-3** (20× looser),
   > at **N = 200**, over **200 realizations**, and only at σ ∈ {1°, 2.87°, 5°, 10°} — it never
   > reaches 20°. The engineering conclusion drawn from this law (1% loss at σ ≤ 2.87°, exactly
   > 2× tighter than spin-1) is a *hard array-design constraint*, so the gap between the asserted
   > and the claimed precision matters. **The test is not wrong; it is narrower than the record it
   > is named after.** Either tighten it to the ADR's figures or amend the ADR to state what is
   > actually enforced in CI.
2. ✅ **RESOLVED 2026-08-03.** The finding stood: no committed test pinned an absolute
   analytic value, so the 1e-14 the ADR and the paper both printed was not reproducible from
   this repository. Closed by three parametrized tests in `test_superposition.py` — the
   closed form through `apply_tt` and again through the production `superpose_tt` path, plus
   the half-period inversion `h(ψ+π/2) = −h(ψ)`. **Unlike finding 1, this claim was
   *conservative*:** measured worst error is 1.1e-16 against the 1e-14 asserted, ~100x margin.
   The two ADR-0003 precision errors ran in **opposite directions**, which is the reason
   neither could be assumed and both had to be measured. *Original finding, retained:*

   > ⚠️ **ADR-0003's 1e-14 analytic-TT check exists only in the scratch prototype.** The ADR
   > reports the two-element prototype reproducing the closed-form `h^TT` to **1e-14 across nine
   > ψ values**; no test in `tests/` performs that comparison. The suite validates *structure*
   > (symmetry, tracelessness, transversality to atol 1e-15) and *relative* behaviour, but never
   > pins an absolute analytic value. Same class as the ADR-0006 dangling-prototype finding
   > recorded in §3 — the evidence for an accepted decision living outside the repository's
   > executable surface.

✅ **A third, smaller instance of the same class — RESOLVED 2026-08-03.** `bodies/multipole.py`
claimed `octupole_moment` was cross-checked against Blanchet's two-body Newtonian octupole
(eq. 302a); **no test executed that comparison**. It now does, across five mass ratios at
rtol 1e-12, and is mutation-checked against the STF coefficient. The citation sweep that
preceded it also found **[B] eq. 302a is the 2.5PN circular-orbit octupole**, not a Newtonian
expression — only its leading term is what we reproduce, and EQ-044 now says so.

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
