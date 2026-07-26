# Codebase Index

Maintained by the `indexer` agent. This is the central knowledge store for the project — the
defense against future archaeology. A contributor arriving decades from now should be able to
audit the foundations from here without reverse-engineering the code.

**Last updated:** 2026-07-26 (Sprint 0)

---

## 1. Equation Registry

One row per implemented equation. `Status` mirrors the categories in
[`CLAIMS.md`](CLAIMS.md): `VERIFIED` (citation confirmed by `researcher`), `DERIVED` (our
extension of a cited result), `CONJECTURE` (not yet grounded).

| ID | Equation | Source + eq. no. | Implemented in | Tested by | Status |
|----|----------|------------------|----------------|-----------|--------|
| — | *No equations implemented yet. Sprint 0 is foundation only.* | | | | |

**Planned for Sprint 1** (citations to be confirmed by `researcher` at sprint planning):

| ID | Equation | Intended source | Target module |
|----|----------|-----------------|---------------|
| EQ-001 | Mass quadrupole moment `Q_ij` | Maggiore Vol. 1 ch. 3 | `bodies/multipole.py` |
| EQ-002 | Second derivative `Q̈_ij` (analytic) | derived from EQ-001 | `bodies/multipole.py` |
| EQ-003 | TT projector `Λ_ij,kl` | Maggiore Vol. 1 ch. 1 | `propagate/tt_projection.py` |
| EQ-004 | Quadrupole strain `h_ij^TT` | Maggiore Vol. 1 ch. 3 | `source/quadrupole.py` |
| EQ-005 | GW luminosity `L_GW` | Maggiore Vol. 1 ch. 3 | `source/quadrupole.py` |

---

## 2. Module Map

| Module | Purpose | Public API | Depends on |
|---|---|---|---|
| `core/constants.py` | Physical constants with sources | *(Sprint 1)* | — |
| `core/units.py` | Scaled strain representation | *(Sprint 1)* | `constants` |
| `core/backend.py` | Array-API shim (numpy / numba / future GPU) | *(Sprint 11)* | — |
| `bodies/sphere.py` | Rigid uniform sphere; degeneracy guard | *(Sprint 4)* | `constants` |
| `bodies/elastic.py` | Love-number deformation; breaks R/ρ degeneracy | *(Sprint 4)* | `sphere` |
| `bodies/multipole.py` | Mass multipole moments and derivatives | *(Sprint 1)* | `constants` |
| `kinematics/profiles.py` | Finite-maneuver acceleration profiles | *(Sprint 3)* | — |
| `kinematics/oscillators.py` | Prime-frequency drive synthesis | *(Sprint 9)* | `profiles` |
| `source/quadrupole.py` | Quadrupole radiation and luminosity | *(Sprint 1)* | `multipole`, `tt_projection` |
| `source/multipole_rad.py` | Higher multipoles; dipole term (flagged) | *(Sprint 2)* | `multipole` |
| `source/memory.py` | Linear GW memory from finite maneuvers | *(Sprint 3)* | `quadrupole` |
| `source/conservation.py` | ∂_μT^μν audit; `UNPHYSICAL` stamping | *(Sprint 2)* | — |
| `propagate/tt_projection.py` | Transverse-traceless projector | *(Sprint 1)* | — |
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
| Circular binary (h₊, h×, L) | EQ-004, EQ-005 | Not implemented |
| Hulse–Taylor PSR B1913+16 period decay | EQ-005 | Not implemented |
| Spinning rod power | EQ-005 | Not implemented |
| **Dipole cancellation** | Conservation auditor | Not implemented — *highest-value test in the suite* |
| Linear memory (hyperbolic scattering) | `source/memory.py` | Not implemented |
| Array factor vs. arraytool | `array/beamform.py` | Not implemented |
| Diffraction limit `w ≈ λr/D` | `array/focus.py` | Not implemented |
| Energy conservation over distant sphere | EQ-005 | Not implemented |

---

## 5. Open Questions

| ID | Question | Context |
|---|---|---|
| OQ-1 | Does the dipole term cancel numerically to the precision we expect in a momentum-conserving two-body configuration? | Validates the project's central physics framing (decision 1). Scheduled Sprint 1 — pulled forward from Sprint 2 because a surprise here reframes everything downstream |
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
