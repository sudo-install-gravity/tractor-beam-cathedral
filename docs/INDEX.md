# Codebase Index

Maintained by the `indexer` agent. This is the central knowledge store for the project — the
defense against future archaeology. A contributor arriving decades from now should be able to
audit the foundations from here without reverse-engineering the code.

**Last updated:** 2026-07-26 (Sprint 1 core implemented — T-1.0 through T-1.10)

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

**Citations verified 2026-07-26** for all Sprint 1 equations. Sources are open access with
checkable equation numbers:

- **[B]** Blanchet, *Living Rev. Relativ.* **17**:2 (2014), arXiv:1310.1528
- **[FH]** Flanagan & Hughes, *New J. Phys.* **7**:204 (2005), arXiv:gr-qc/0501041

**Textbook citations were rejected during verification.** Maggiore and MTW equation numbers could
not be confirmed without the physical books. A citation a contributor cannot check is not a
citation, so open-access sources were substituted throughout. This is now the project's standing
preference — see `CONTRIBUTING.md`.

⚠️ **[FH] eqs. (4.41) and (4.42) contain typos.** See [`ERRATA.md`](ERRATA.md) ERR-001/ERR-002.
The derivations we rely on ([FH] 4.17–4.23) are correct; only the worked binary example is
affected.

---

## 2. Module Map

| Module | Purpose | Public API | Depends on |
|---|---|---|---|
| `core/constants.py` | Physical constants with sources | **live** — `G`, `c`, `AU`, `M_SUN`, `PARSEC`, `G_OVER_C4/5`, `TARGET_RANGE` | — |
| `core/units.py` | Scaled strain representation | **live** — `StrainScale` | `constants` |
| `core/backend.py` | Array-API shim (numpy / numba / future GPU) | *(Sprint 11)* | — |
| `bodies/sphere.py` | Rigid uniform sphere; degeneracy guard | *(Sprint 4)* | `constants` |
| `bodies/elastic.py` | Love-number deformation; breaks R/ρ degeneracy | *(Sprint 4)* | `sphere` |
| `bodies/multipole.py` | Mass multipole moments and derivatives | **live** — `quadrupole_moment`, `_second_derivative`, `_third_derivative` | `constants` |
| `kinematics/profiles.py` | Finite-maneuver acceleration profiles | *(Sprint 3)* | — |
| `kinematics/oscillators.py` | Prime-frequency drive synthesis | *(Sprint 9)* | `profiles` |
| `source/quadrupole.py` | Quadrupole radiation and luminosity | **live** — `strain_tt`, `luminosity` | `multipole`, `tt_projection` |
| `source/multipole_rad.py` | Higher multipoles; dipole term (flagged) | *(Sprint 2)* | `multipole` |
| `source/memory.py` | Linear GW memory from finite maneuvers | *(Sprint 3)* | `quadrupole` |
| `source/conservation.py` | ∂_μT^μν audit; `UNPHYSICAL` stamping | *(Sprint 2)* | — |
| `propagate/tt_projection.py` | Transverse-traceless projector | **live** — `tt_projector`, `apply_tt`, `transverse_projector` | — |
| `propagate/polarization.py` | Spin-2 basis; e^(2iψ) rotation | *(Sprint 5)* | `tt_projection` |
| `propagate/retarded.py` | Retarded-time field evaluation to 40 AU | *(Sprint 6)* | `quadrupole` |
| `array/geometry.py` | Element placement | *(Sprint 5)* | — |
| `array/beamform.py` | Array factor, steering, tapering | *(Sprint 6)* | `geometry`, `polarization` |
| `array/grating.py` | Grating-lobe and spacing constraints | *(Sprint 6)* | `geometry` |
| `array/focus.py` | Spatiotemporal focusing | *(Sprint 9)* | `beamform` |
| `target/geodesic.py` | Geodesic deviation at the target | *(Sprint 8)* | `tt_projection` |
| `target/coupling.py` | Three momentum-transfer channels | *(Sprint 8)* | `geodesic` |
| `target/deflection.py` | Orbit propagation; Δv → miss distance | *(Sprint 8)* | `coupling` |
| `ledger/gap_report.py` | Feasibility ledger | *(Sprint 2)* | most modules |
| `viz/*` | Field slices, beam patterns, volumetric | *(Sprint 7)* | — |
| `core/validation.py` | ADR-0002 shape/dtype/unit-vector guards | **live** — `as_masses`, `as_body_array`, `as_tensor_3x3`, `as_unit_vector` | — |

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

---

## 4. Validation Status

A benchmark that has not run since the code it validates last changed is **stale**, not
passing.

| Benchmark | Validates | Status |
|---|---|---|
| Circular binary (h₊, h×, L) | EQ-005, EQ-006, EQ-007 | **PASSING** rtol 1e-6 |
| Hulse–Taylor PSR B1913+16 period decay | EQ-006 | Not implemented |
| Spinning rod power | EQ-006 | Not implemented (T-2.8) |
| **Dipole cancellation** | Momentum conservation (decision 1) | **PASSING** — ratio < 1e-12 over 20 seeded configs, plus a positive control > 1e-3. *OQ-1 resolved: the dipole does cancel as expected.* |
| Linear memory (hyperbolic scattering) | `source/memory.py` | Not implemented |
| Array factor vs. arraytool | `array/beamform.py` | Not implemented |
| Diffraction limit `w ≈ λr/D` | `array/focus.py` | Not implemented |
| Energy conservation over distant sphere | EQ-006 | Not implemented |

---

## 5. Open Questions

| ID | Question | Context |
|---|---|---|
| ~~OQ-1~~ | **RESOLVED 2026-07-26** — the dipole cancels to <1e-12 relative in momentum-conserving configurations, confirming decision 1. | |
| OQ-1 (orig) | Does the dipole term cancel numerically to the precision we expect in a momentum-conserving two-body configuration? | Validates the project's central physics framing (decision 1). Scheduled Sprint 1 — pulled forward from Sprint 2 because a surprise here reframes everything downstream |
| OQ-2 | How is polarization-mismatch loss correctly formulated for spin-2 array elements of differing orientation? | No external reference implementation exists. `SPIKE-4.4` (Sprint 2) attacks this early because it sits on the critical path |
| OQ-3 | At what R/λ does the long-wavelength quadrupole approximation fail badly enough to matter? | Determines whether `bodies/` finite-size corrections are a refinement or a requirement |
| OQ-4 | Is a sparse (non-filled) array viable given the 6×10⁹-wavelength aperture requirement? | Sparse arrays relax element count but raise sidelobes — directly opposed to requirement 6's single-point focus |
| OQ-5 | Does the near-zone gradient channel (Lu & Love) scale to anything useful at 40 AU? | If not, conjecture C-4 has no candidate mechanism |

---

## Maintenance rules

- Never let the Equation Registry drift from the code. A citation in a docstring but not the
  registry gets added; a registry row pointing at a function that no longer exists gets
  **flagged loudly**, not deleted. A vanished equation is a finding.
- Cross-link to `CLAIMS.md` categories so the two documents cannot disagree.
- Prefer flagging over fixing. When index and code disagree, report the disagreement and let a
  human or a task decide which is wrong.
