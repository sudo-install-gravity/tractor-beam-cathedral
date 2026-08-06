# Claims Registry

Every assertion this project makes falls into exactly one of three categories. Nothing moves
between categories without review, and the category is recorded alongside the equation in
[`INDEX.md`](INDEX.md).

This document exists because a project measured in generations accumulates claims faster than
it accumulates the memory of where they came from.

---

## Epistemic firewall — read before adding anything

This project sits adjacent to a genuinely discredited literature, and its credibility depends
on staying clearly on the right side of that boundary.

The high-frequency gravitational wave (HFGW) generation and detection claims associated with
Robert Baker and collaborators were reviewed by the JASON Defense Advisory Panel at the request
of the National MASINT Committee of the ODNI. The resulting report — *High Frequency
Gravitational Waves*, JSR-08-506 (Eardley, D. et al., MITRE Corporation, October 2008) —
concluded that the proposed applications were fundamentally wrong, that no security threat
existed, and that independent technical vetting of such claims is generally necessary.

**Rules:**

- Never cite gravwave.com, drrobertbaker.com, HFGW patent literature, or the associated
  conference proceedings as authority for anything.
- The credible prior art on deliberately engineered gravitational radiation is Grishchuk, L.P.
  & Sazhin, M.V., "Emission of gravitational waves by an electromagnetic cavity,"
  *Sov. Phys. JETP* **38**(2):215–221 (1974).
- A claim being *adjacent* to bad literature does not make it wrong. It means the citation
  standard is higher, not lower.

The feasibility ledger (`src/gwtb/ledger/`) is the working mechanism that keeps this project on
the right side of the line: it reports, on every run, the quantitative distance between the
modeled configuration and an actual asteroid deflection. A framework that could not state its
own gap would be indistinguishable from the literature above.

---

## Category A — Established physics

Textbook or well-replicated peer-reviewed results. We implement these; we do not defend them.

Sources marked ✅ were independently verified 2026-07-26 against open-access literature:
**[B]** Blanchet, *Living Rev. Relativ.* **17**:2 (2014); **[FH]** Flanagan & Hughes,
*New J. Phys.* **7**:204 (2005). Remaining textbook references are placeholders and will be
replaced at the sprint planning that precedes their use.

| ID | Claim | Source |
|---|---|---|
| A-1 | Linearized Einstein equations admit a retarded-Green's-function solution for a weak, slowly-moving source | **[B] eq. 1** ✅ verified |
| A-2 | Leading-order gravitational radiation is quadrupolar; mass monopole and mass dipole radiation vanish for an isolated system | **[B] eq. 3**; [FH] §4.3 ✅ verified |
| A-3 | The quadrupole luminosity formula `F = (G/5c⁵) Q⃛_ab Q⃛_ab` | **[B] eq. 4** ✅ verified |
| A-4 | Gravitational waves are transverse-traceless and carry two polarizations, h₊ and h×, separated by 45° | **[FH] eq. 4.22** ✅ verified |
| A-5 | Gravitational radiation is spin-2: polarization transforms as e^(2iψ) under rotation about the propagation direction | **Mashhoon, B. & Rahvar, S., *Universe* **9**:6 (2023), arXiv:2211.01691, eq. 4** ✅ verified 2026-08-03 — `h'₁₁ = h₁₁cos2ϑ + h₁₂sin2ϑ`, `h'₁₂ = −h₁₁sin2ϑ + h₁₂cos2ϑ`; open access, CC BY 4.0. *Previously cited "MTW §35–36" — a **chapter** reference, i.e. exactly the pattern rule 1 rejects, sitting under the project's most load-bearing Category A claim. Retained here as historical provenance only.* |
| A-6 | A passing GW produces tidal geodesic deviation, not net center-of-mass acceleration of a free body | MTW §37.2 |
| A-7 | Linear GW memory: a finite burst leaves a permanent strain offset | **Favata, *Class. Quantum Grav.* 27:084036 (2010), arXiv:1003.3486, eq. 10k** ✅ verified 2026-07-31. Historical provenance: Zel'dovich & Polnarev (1974); Braginsky & Thorne, *Nature* **327**:123 (1987) — the latter is a Nature letter with no numbered equations and does **not** meet this project's citation bar; cite Favata |
| A-8 | Phased-array factor and beam-steering relations for a coherent aperture | Balanis, *Antenna Theory* ch. 6 |
| A-9 | Diffraction limits a focused spot to `w ≈ λr/D`; for a uniformly-illuminated circular aperture the −3 dB (FWHM) transverse extent is **`w = 1.029 λr/D`** | ✅ verified 2026-07-31 via the transcendental root `x = 1.61633` of `2J₁(x)/x = 1/√2`, reproducible with `scipy.special.j1` — **self-auditable, needing no textbook page**. Corroborated by Thorne & Blandford, *Modern Classical Physics* ch. 8 (open-access Caltech ph136 notes), `ρ_FWHM = 1.61633 z/(kR)`. ⚠️ **Not 1.22** — that is the Rayleigh first-null criterion, not the −3 dB width. Scalar-diffraction result: safe for aperture geometry, **never** for how h₊/h× combine |
| A-10 | A spacecraft's gravitational attraction can deflect an asteroid (gravity tractor) | Lu, E.T. & Love, S.G., *Nature* **438**:177 (2005) |
| A-11 | Kinetic impact can measurably alter an asteroid's orbit | NASA DART / Dimorphos, 2022 |

## Category B — Our derived extensions

Results we derive by combining Category A results. Each must show its derivation in
[`PHYSICS.md`](PHYSICS.md) and be validated against a limiting case that reduces to Category A.

| ID | Claim | Status | Reduces to |
|---|---|---|---|
| B-1 | Phased-array synthesis extended from spin-1 (EM) to spin-2 (GW) fields: superposition acts on the TT-projected tensor; element mismatch factor is `cos(2Δψ)`; array gain is N² only for co-oriented elements; alignment tolerance `exp(−4σ²)` **as N → ∞, with an exact finite-N bias `+(1−exp(−4σ²))/N`** | **Derived & validated** 2026-07-27 — [ADR-0003](adr/0003-spin2-superposition.md). **Precision amended 2026-08-03** (ADR-0003 amendment): the tolerance law is the `N → ∞` limit, not a finite-N statement, and the ADR's original "verified to ~1e-4 across σ ∈ [0°, 20°]" was overstated by up to 39× at the smaller N it cited. The *physics* is unchanged and the σ ≤ 2.87° engineering conclusion stands — the bias is positive, so a finite array does marginally **better** than the law | A-5, A-8 |
| B-2 | For a rigid uniform sphere in the long-wavelength limit, radius and density are degenerate with total mass; the degeneracy is broken only by elastic deformation, finite-size retardation, or rotational oblateness | **Derived; all three breaking mechanisms now validated.** Rigid-model degeneracy and oblateness (T-4.1/4.2/4.6), **elastic deformation (T-4.3, 2026-07-31)** — `bodies/elastic.py` breaks the degeneracy explicitly (`Q ∝ R⁵`, ρ via `μ̃`), asserted against T-4.2's identical-radiation test — and **finite-size retardation (T-4.5, 2026-08-02)**, see B-7. Note the third mechanism breaks the degeneracy through **radius only**: the form factor is geometric, and density does not enter it | A-2 |
| B-3 | Required aperture for a focused spot is `D/λ ≳ r/w`, i.e. ~6×10⁹ wavelengths for a 1 km spot at 40 AU, independent of frequency | **Not yet derived** (T-10.1/10.2 outstanding), but **independently corroborated from the other side** 2026-07-31: at 40 AU a 12.4 km aperture sits at `R/R_Fraunhofer ≈ 5.9×10⁹` at 1 kHz, and the entire focusing phase correction is ~6.7×10⁻¹¹ rad — focusing is numerically degenerate with steering. The two numbers are the same wall. See `INDEX.md` assumption ledger and `test_focus.py::test_focusing_is_degenerate_with_steering_at_40_au` | A-9 |
| B-4 | Mutually incommensurate (prime-valued) drive frequencies produce a spatiotemporal focus with peak amplitude N·A against a √N·A background, and a pattern recurrence period equal to the product of the primes | **Partially derived** 2026-07-31 (T-9.6). Peak `N·A` confirmed at broadside to rtol 1e-6; peak-to-background ratio confirmed to scale as `√N` across N ∈ {16, 64, 100}. **Correction to the claim as stated:** the background *mean* is the Rayleigh value `√(Nπ)/2 ≈ 0.886√N`, not `√N` — it is the *ratio* that scales as `√N`. Recurrence period (T-9.8) still outstanding | A-8 |
| B-5 | Radiated GW momentum flux delivers negligible impulse to an asteroid; any real coupling must be near-zone gravitational gradient (A-10), not radiative | **Not yet derived** | A-6, A-10 |
| B-6 | Analytic 2nd/3rd time derivatives of the trace-free quadrupole moment for point masses | **Derived & validated** 2026-07-26 | A-3, Blanchet eq. 3 |
| B-7 | The leading finite-size retardation correction to the mass quadrupole of a body with a **volume-filling** `l=2` radial profile is `F₂(kR) = 1 − 5(kR)²/98`; generally `1 − (kR)²(l+3)/[2(2l+3)(l+5)]` | **Derived & numerically validated** 2026-08-02 — [ADR-0007](adr/0007-uniform-sphere-quadrupole-form-factor.md), EQ-034, SPIKE-4.5. **Admitted to Category B without a citation, deliberately:** no numbered equation for this result exists in any accessible source (Thorne 1980 is paywalled and its numbering unconfirmed — cited *without* an equation number, per rule 1). Justified instead by three independent numerical routes, the strongest agreeing to `1.7e-12`, none evaluating a spherical Bessel function. The machinery also reproduces the externally-checkable `l=0` result `3j₁(kR)/(kR)`. ⚠️ **A *surface* profile gives `1 − (kR)²/14` — 40% larger — so this must not be applied to B-2's elastic or oblateness mechanisms.** Promotion to A requires a numbered equation that states the volume-filling profile explicitly | A-3, Blanchet eq. 3 |

*"Not yet derived" means the claim is currently a scoping estimate. It is not usable in any
published result until it carries a derivation and a validating test.*

## Category C — Open conjectures

Stated so they are not silently assumed. **No code depends on anything in this table.**

| ID | Conjecture | Why it is open |
|---|---|---|
| C-1 | Some physical mechanism can convert stored energy into gravitational radiation at an efficiency useful for deflection | Deliberately out of scope per project charter — this is the "transducer" problem left to future contributors |
| C-2 | The ~40 order-of-magnitude gap between plausible engineered sources and deflection-relevant power is closable at all | Unknown. Quantifying it precisely is this project's primary deliverable |
| C-3 | An aperture of ~6×10⁹ wavelengths is physically constructible in any regime | Unknown. At 1 MHz this is ~12 AU |
| C-4 | Any mechanism exists to couple GW energy to an asteroid's center-of-mass motion with non-negligible efficiency | A-6 says radiative coupling is essentially nil; whether a near-zone alternative scales is open |

---

## Promotion and demotion

- **C → B** requires a derivation in `PHYSICS.md` plus a limiting case that reduces to a
  Category A result.
- **B → A** requires independent peer-reviewed publication. We do not promote our own work.
- **Demotion happens.** If a validating test fails or a citation is found not to say what we
  thought, the claim moves down and everything depending on it is flagged. Demotions are
  recorded here with a date and a reason, never silently deleted.

## Change log

| Date | Change |
|---|---|
| 2026-07-26 | Registry created at Sprint 0. All Category B claims are scoping estimates pending derivation. |
| 2026-07-26 | B-6 added and validated: analytic Q̈ and Q⃛ derived from Blanchet eq. (3). Luminosity built from Q⃛ reproduces the closed form `L = (32/5)(G/c⁵)μ²a⁴ω⁶` to 4.1e-16. |
| 2026-07-26 | Source policy changed: open-access citations preferred over textbooks, since textbook equation numbers could not be independently confirmed. See `PHYSICS.md` header. |
| 2026-07-26 | `ERRATA.md` created — two verified typos in Flanagan & Hughes (2005) eqs. (4.41), (4.42). |
| 2026-07-31 | **B-4 partially derived** (T-9.6), and corrected: the random-phase background *mean* is `√(Nπ)/2 ≈ 0.886√N`, not `√N`. The peak-to-background *ratio* is what scales as `√N`, confirmed across N ∈ {16, 64, 100}. |
| 2026-07-31 | **A-9 measured, not just cited** (T-10.1). `FWHM_COEFFICIENT = 1.0290` verified two independent ways: re-solved from `2J₁(x)/x = 1/√2` with `scipy.optimize.brentq`, and measured from the simulated diffraction pattern of a filled circular aperture. A test asserts explicitly that it is **not** 1.22, the substitution most likely to be made silently. |
| 2026-07-31 | **SPIKE-9.6 → ADR-0006.** Discharged the open design decision blocking T-9.6. `focused_field` builds on `superpose_tt`: the per-element angular spread at 40 AU is 1.03e-9 rad against ADR-0003's 5.0e-2 rad budget (2.4e7× margin), so the common-`n̂` reversal condition is **not** triggered. Near-field focusing stays out of scope. **B-3 sharpened**: at the nominal 1 kHz drive the 12.4 km reference aperture spans `D/λ = 0.041` — sub-wavelength, no beam at all. The aperture requirement is not merely large, it is unreachable at any GW-plausible frequency for apertures of this scale. |
| 2026-07-31 | **A-7 re-sourced.** Linear memory now cites Favata arXiv:1003.3486 eq. (10k), an open-access numbered equation. Braginsky & Thorne (1987) is a Nature letter with no numbered equations and never met the citation bar; it is retained as historical provenance only. Implementation (`source/memory.py`, T-3.7) is the **non-relativistic limit** — Favata's per-body Lorentz factor *and* the beaming factor `1/(1−v·N)` are both dropped. Note the beaming factor was absent from BACKLOG's statement of the formula too, so this corrects the spec, not just the code. |
| 2026-07-31 | **A-9 sharpened.** The −3 dB coefficient is `1.029`, from the root `x = 1.61633` of `2J₁(x)/x = 1/√2` — self-auditable via `scipy.special.j1`, replacing a bare chapter reference. Records explicitly that `1.22` (Rayleigh first null) is **not** the −3 dB width, a substitution that would have been easy to make silently. |
| 2026-07-31 | **B-2 advanced.** Elastic deformation (T-4.3) implemented and validated against T-4.2's degeneracy assertion, citing Hinderer arXiv:0711.2420 eqs. (4)–(5) and Cheng, Lee & Peale arXiv:1402.0625 eqs. (8)–(9). Two of three degeneracy-breaking mechanisms are now live. |
| 2026-07-31 | **New blocker, OQ-7 (T-4.5).** `researcher` returned UNVERIFIED for the finite-size form factor and found the task's premise wrong: `sin(kR)/(kR)` is `l=0` **spin-1 antenna machinery** — CLAUDE.md rule 4's trap, nearly implemented as GW physics — and `3j₁(kR)/(kR)` is the total-mass monopole. The `l=2` result appears to be `1 − 5(kR)²/98` but has **no numbered equation**; it is a derivation. Escalated to SPIKE-4.5. **No code was written from the unverified formula.** |
| 2026-08-02 | **OQ-7 closed as a negative answer; B-7 added; B-2 completed.** SPIKE-4.5 → [ADR-0007](adr/0007-uniform-sphere-quadrupole-form-factor.md). **The citation search failed and that failure is the decision**: no numbered equation for the uniform-sphere `l=2` form factor exists in any accessible source, so `1 − 5(kR)²/98` is admitted to **Category B on numerical evidence instead** — three independent routes, the strongest agreeing to `1.7e-12`, none evaluating a spherical Bessel function; the same machinery reproduces the externally-checkable `l=0` result. Thorne 1980 stays paywalled and is cited **without** an equation number, deliberately (rule 1: a guessed number is worse than none). Both originally-proposed form factors confirmed wrong (`1/6` spin-1 `l=0`; `1/10` total-mass monopole). **New finding, recorded in the assumption ledger:** the radial profile is load-bearing — a *surface* deformation gives `1 − (kR)²/14`, **40% larger**, so B-7 must not be applied to B-2's elastic (T-4.3) or oblateness (T-4.6) mechanisms without re-deriving. T-4.5's acceptance criterion was **recomputed**: the departure at `R/λ = 0.1` is 2.0142%, not the ">1%" written against the wrong form factor. |
| 2026-07-27 | **B-1 discharged** by SPIKE-4.4 / ADR-0003. Two-element prototype reproduced the analytic TT form to 1e-14 and confirmed the mismatch factor is `cos(2Δψ)`: elements 45° apart are polarization-orthogonal (EM needs 90°), and elements **90° apart cancel completely** where EM intuition predicts 2× power. Alignment tolerance `exp(−4σ²)` verified to ~1e-4; 1% loss at σ = 2.87°, exactly 2× tighter than spin-1. *(The "~1e-4" in this entry was corrected 2026-08-03 — see below. Retained as written, per the no-silent-edits rule.)* |
| 2026-08-03 | **Citation sweep completed — every remaining new equation number read at source.** Both primary papers were downloaded and their text extracted locally rather than trusted to a summary, because EQ-040 had just shown a plausible number in the right paper can point at the wrong equation. **Two verified exactly:** [FH] eq. 3.11 (EQ-045) is `d²Lⁱ/dt² = ½(d²h^TT_ij/dt²)Lʲ`, and [FH] eq. 4.30 (EQ-041) is `M₁ ≡ ∫ρxⁱd³x`. **Two verified but overstated in scope, reclassified VERIFIED→DERIVED:** [FH] eq. 4.35 (EQ-042) is `dM₁/dt = P`, the **first** derivative, where the code returns the second; and [B] eq. 123a (EQ-044) is Theorem 6's general **post-Newtonian** multipole with finite-part regularization, not the Newtonian point-mass octupole. In both cases the *function's own prose was already accurate* — only the `Source:` line overreached, which is a narrower failure than EQ-040's and worth distinguishing. Also established: **[B] eq. 302a is the 2.5PN circular-orbit octupole**, so only its leading term `I_ijk = −νm∆x⟨ijk⟩` is the Newtonian two-body result; that reduction is confirmed algebraically and now runs as a test. **No claim changed category between A/B/C and no physics changed.** |
| 2026-08-03 | **A-5 re-sourced, and EQ-040's citation CORRECTED — the most load-bearing citation in the project was pointing at the wrong equation.** `rotate_polarization` cited [FH] eq. 4.22 for the e^(2iψ) rotation law. **[FH] eq. 4.22 is the transverse-traceless projector** — the very equation EQ-004 cites, correctly, for `tt_projection` — and a `researcher` pass confirmed the rotation law appears **nowhere** in that paper (it shows the 45° relationship only qualitatively, in Figure 1, with no equation). Two distinct claims cannot rest on one number. Replaced with **Mashhoon & Rahvar, *Universe* 9:6 (2023), arXiv:2211.01691, eq. 4**, which matches the implementation term for term and is open access with a checkable number; verified by direct fetch, not taken on report. **A-5 itself was simultaneously mis-cited** to "MTW §35–36", a chapter reference of exactly the form rule 1 rejects, and now carries the same numbered source. **No physics changed and no claim moved category** — e^(2iψ) was never in doubt; it is the *provenance* that was broken, one hop below the manuscript's opening sentence. |
| 2026-08-03 | **EQ-054's precedent question resolved — and Ruze is NOT it.** `code-reviewer` proposed Ruze, *Proc. IEEE* 54(4):633 (1966) as precedent for the finite-N random-phasor bias. Verified false: Ruze gives the **N → ∞ limit only**. The finite-N form is **D'Addario, L. R., *IPN Progress Report* 42-175, JPL/Caltech (2008), eq. 5** — `P/P_max = (1/N²)[N + N(N−1)e^(−σ₀²)] = (1/N)(1−e^(−σ₀²)) + e^(−σ₀²)` — algebraically identical to our `μ² + (1−μ²)/N`, and that paper's *own* eq. 6 is the N → ∞ reduction it attributes to Ruze. Confirmed by reading the PDF directly after two automated extractions garbled it. **EQ-054 stays Category B.** D'Addario is a scalar/spin-1 RF source and a JPL technical report, not peer-reviewed: it supports the **N-dependence skeleton** only. The spin-2 content — that the relevant phase error is `2ψ`, so `σ_phase = 2σ_orientation` and the law is `exp(−4σ²)` rather than `exp(−σ²)` — is this project's own derivation and does not promote. Same shape as EQ-034, which cites DLMF for its input series while the specialization stays ours. |
| 2026-08-03 | **B-1 precision corrected — a stated-precision defect, not a physics defect.** `exp(−4σ²)` is the **`N → ∞` limit**; at finite `N` the estimator carries an exact positive bias `(1−exp(−4σ²))/N`, derived and verified in `scratchpad/spike_b1_alignment_bias.py` (observed/predicted ∈ [0.95, 1.03] over `N ∈ {100, 200, 1000}`, deviation halving as `N` doubles, mean ratio 1.962 vs 2.000). ADR-0003's "verified to ~1e-4 across σ ∈ [0°, 20°]" **is contradicted by its own printed table** (8.8e-4 at σ = 20°) and is unreachable at the `N = 100` it also cites, where the bias alone is 3.9e-3. **No claim is demoted:** the tensor superposition, `cos(2Δψ)`, the 90° cancellation and the σ ≤ 2.87° requirement are all unaffected, and the bias is *positive*, so a real finite array beats the law slightly. **Found by auditing the paper draft against the test suite** — the manuscript printed a precision better than CI enforced, both tracing to the same ADR sentence. The test now asserts the bias-corrected prediction to **5 standard errors of the estimator's own sampling distribution** over σ ∈ {2.87°, 5°, 10°, 20°} — a statistical tolerance, because a flat `abs=1e-4` sat at 0.7 SE at σ = 20° and failed 13 of 30 reseeds while passing on the committed seed. Seed-robust (0/40 reseeds fail) and discriminating at **every** σ: dropping the `1/N` term is rejected by 2.2–2.9×. **Citation caveat:** `code-reviewer` flagged Ruze, *Proc. IEEE* 54(4):633 (1966) as a plausible precedent for the random-phasor skeleton; unconfirmed, cited without an equation number, and it is a **spin-1** source — it could never promote the `4σ²` spin-2 prefactor out of Category B. |
