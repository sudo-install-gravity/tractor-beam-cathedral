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
| A-5 | Gravitational radiation is spin-2: polarization transforms as e^(2iψ) under rotation about the propagation direction | MTW §35–36 |
| A-6 | A passing GW produces tidal geodesic deviation, not net center-of-mass acceleration of a free body | MTW §37.2 |
| A-7 | Linear GW memory: a finite burst leaves a permanent strain offset | Zel'dovich & Polnarev (1974); Braginsky & Thorne, *Nature* **327**:123 (1987) |
| A-8 | Phased-array factor and beam-steering relations for a coherent aperture | Balanis, *Antenna Theory* ch. 6 |
| A-9 | Diffraction limits a focused spot to `w ≈ λr/D` | Goodman, *Fourier Optics* ch. 4 |
| A-10 | A spacecraft's gravitational attraction can deflect an asteroid (gravity tractor) | Lu, E.T. & Love, S.G., *Nature* **438**:177 (2005) |
| A-11 | Kinetic impact can measurably alter an asteroid's orbit | NASA DART / Dimorphos, 2022 |

## Category B — Our derived extensions

Results we derive by combining Category A results. Each must show its derivation in
[`PHYSICS.md`](PHYSICS.md) and be validated against a limiting case that reduces to Category A.

| ID | Claim | Status | Reduces to |
|---|---|---|---|
| B-1 | Phased-array synthesis extended from spin-1 (EM) to spin-2 (GW) fields, including polarization-mismatch loss between differently-oriented elements | **Not yet derived** | A-5, A-8 |
| B-2 | For a rigid uniform sphere in the long-wavelength limit, radius and density are degenerate with total mass; the degeneracy is broken only by elastic deformation, finite-size retardation, or rotational oblateness | **Not yet derived** | A-2 |
| B-3 | Required aperture for a focused spot is `D/λ ≳ r/w`, i.e. ~6×10⁹ wavelengths for a 1 km spot at 40 AU, independent of frequency | **Not yet derived** | A-9 |
| B-4 | Mutually incommensurate (prime-valued) drive frequencies produce a spatiotemporal focus with peak amplitude N·A against a √N·A background, and a pattern recurrence period equal to the product of the primes | **Not yet derived** | A-8 |
| B-5 | Radiated GW momentum flux delivers negligible impulse to an asteroid; any real coupling must be near-zone gravitational gradient (A-10), not radiative | **Not yet derived** | A-6, A-10 |
| B-6 | Analytic 2nd/3rd time derivatives of the trace-free quadrupole moment for point masses | **Derived & validated** 2026-07-26 | A-3, Blanchet eq. 3 |

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
