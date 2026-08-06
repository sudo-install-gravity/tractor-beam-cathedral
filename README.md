# Tractor Beam Cathedral

**`gwtb`** — a modeling and simulation framework for a theoretical asteroid-deflection
concept: an array of massive spheres undergoing controlled finite maneuvers, phased so their
gravitational radiation constructively interferes at a target out to 40 AU.

This is a **cathedral project**. It is expected to span more than one human lifetime. We build
the theoretical framework; we deliberately leave the "transducer" engineering — whatever
converts stored energy into useful gravitational radiation — to future contributors.  Author's note: this approach was directly inspired by Miguel Alcubierre's conceptual faster-than-light drive.

Note from the originator: I am not a trained physicist.  I am, at best, a technologist assisted by AI and playing with physics.  On that note, I welcome collaboration, both with real physicists and with amateurs who, like me, are eager to build exciting things and ideas to help humanity reach its full potential.  If you have deep experience in this area and want to contribute, if you spot errors that I do not have enough expertise to see, or even if you're a curious amateur and you just want to play with the code: please dive in, and reach out to me if you want.  I'm excited to see what we can build in this sandbox!

A central hypothesis of this project is that, by democratizing not just information, but also context and rigor, AI tools like Claude (used extensively for this project) enable educated amateurs (which is to say: people with conceptual understanding of relevant ideas, such that they can communicate rigorously in natural language about those ideas, even if they are not able to formally mathematically express those ideas and their implications) can access rigorously-defined concepts and fuse them into new ideas which are mathematically consistent with the relevant literature, but which have not yet been rigorously explored.  This is a falsifiable hypothesis, in that this work may result entirely in AI slop.

If it doesn't, though, the next key question is how much expert intervention will be required to mature the idea into something that passes peer review.  To that end, and with all due humility associated with my undergraduate-only education, I intend to publish this work as a paper in a peer-reviewed journal.  I will rigorously log any help I receive from people and institutions with access to more formal education than myself. The paper to be published will actually present two ideas: the actual technical work being done in this repo, and a case study of how much expert help it took to mature this idea into something that can pass peer review in a legitimate academic journal.

A final acknowledgement: not to overuse the quote, but I (perhaps more than most scientists) truly stand on the shoulders of giants in this endeavor.  I wish to acknowledge that the AI tools I am using have scraped much of the entire corpus of English-language literature in existence, and that I am almost certainly borrowing heavily from the work of people to whom I cannot specifically attribute it.  This lack of ability to give credit where it is richly due is a severe problem, and I do not have a good solution to it.  However, I do not think that this should stop me (or anyone) from using these tools for the benefit of humanity.  I will continue to think about this problem as I continue this work, and I will update this section of the readme with any insights I gain along the way.

**Optimize for auditability over speed. A cathedral built on a sign error is a ruin.**

---

## What this tool computes

All six capabilities are **implemented and tested**.

| # | Capability | Where |
|---|---|---|
| 1 | Gravitational-wave characteristics from accelerating spherical masses, using equations traceable to primary literature — every implemented equation carries a citation | `source/`, `bodies/` |
| 2 | Radiation from **finite maneuvers** (non-impulsive acceleration profiles), including the linear memory effect a finite maneuver leaves behind | `kinematics/`, `source/memory.py` |
| 3 | The effect of body parameters — radius, density, elastic response, finite size — on emitted radiation | `bodies/` |
| 4 | Phased-array beamforming, extended from the spin-1 electromagnetic case to the **spin-2** gravitational case | `array/`, `propagate/polarization.py` |
| 5 | Visualization of field propagation and beam patterns | `viz/` |
| 6 | Spatiotemporal focusing using mutually incommensurate (prime-valued) drive frequencies | `array/focus.py`, `kinematics/oscillators.py` |

And, on every run, a **feasibility ledger** (`ledger/`): a quantitative statement of how far
the modeled configuration sits from actually deflecting an asteroid.

## What this tool is honest about

The feasibility ledger exists because three walls stand between this concept and reality, and
a framework that hides them would be worse than useless:

| Wall | Statement |
|---|---|
| **Diffraction** | Focusing to a 1 km spot at 40 AU requires an aperture of **6×10⁹ wavelengths**, at any frequency. Raising frequency does not relax the ratio — it shrinks the physical size that ratio corresponds to (1.2×10⁷ AU at 1 Hz; ~12 AU at 1 MHz). |
| **Coupling** | A gravitational wave produces tidal *strain*, not net force. Momentum transfer requires absorption, and an asteroid's absorption cross-section is negligible. |
| **Magnitude** | **−6.8 to +29.2 orders of magnitude** separate engineered sources from deflection-relevant power, depending on configuration — measured, not estimated (`tools/run_campaign.py`, R5). Radiated power scales as f⁶, making frequency the dominant lever by ~36 decades between 1 Hz and 1 MHz. ⚠️ **At the 10⁹ kg / 1 km / 1 MHz end the gap is *negative* — this wall does not bind there.** That does not imply feasibility: coupling still demands 14 decades and diffraction 8. *This row previously read "roughly 40 orders of magnitude"; the ledger does not reproduce that figure — see the 2026-08-03 note in `docs/CLAIMS.md`.* |

**A wall is a finding, not a bug.** If a change makes one disappear, the change is presumed
defective until proven otherwise. This rule is enforced in review.

The most valuable output of this project is not a working tractor beam. It is a rigorous,
parameterized quantification of **which orders of magnitude must be attacked, and in what
order** — so that contributors across the project's lifetime aim at the real bottleneck rather
than a comfortable one.

## Where this sits relative to the discredited literature

This work is adjacent to the high-frequency gravitational wave (HFGW) claims associated with
Robert Baker and collaborators, which a JASON Defense Advisory Panel review commissioned by the
ODNI's National MASINT Committee (*High Frequency Gravitational Waves*, JSR-08-506, MITRE, 2008)
found to be fundamentally in error.

We stay on the right side of that line deliberately and mechanically:

- Never cite gravwave.com, drrobertbaker.com, HFGW patent literature, or the associated
  conference proceedings as authority for anything. A source tracing there **halts review**.
- The credible prior art on deliberately engineered gravitational radiation is Grishchuk &
  Sazhin, *Sov. Phys. JETP* **38**(2):215 (1974).
- **A claim being adjacent to bad literature does not make it wrong. It means the citation
  standard is higher, not lower.**

The feasibility ledger is the working mechanism that holds the line: it makes the framework
report its own distance from the application on every run. A framework that could not state its
own gap would be indistinguishable from the literature above. See [`docs/CLAIMS.md`](docs/CLAIMS.md).

---

## Status

**Pre-alpha, v0.1.0, unreleased.** The repository is not yet public.

The planned backlog is essentially complete — but that is a statement about the *modeling
framework*, not about the concept. Nothing here asserts that gravitational-wave asteroid
deflection is feasible. The framework's own ledger says the opposite, quantitatively.

| | |
|---|---|
| Tasks | **111 of 118 complete** (304 story points) |
| Tests | **867 passing**, 3 skipped (2 need PyVista, 1 needs CuPy), ~70–85 s |
| Code | 7,117 lines source; 8,801 lines test |
| Equation registry | **53 equations**, each mapped to source, implementation and test |
| Claims registry | 11 established / 7 our derivation / 4 open conjecture |
| Assumption ledger | 30 approximations, each with its breakdown regime |
| Errata | 2 verified errors found in the cited literature |
| Decision records | 7 ADRs |

**Remaining work is externally blocked.** `T-2.9` (branch protection) needs the repository made
public; the six Sprint 12 closeout tasks (`T-12.1`, `T-12.4`–`T-12.8`) depend on *all* tasks and
are therefore stranded behind it. `python tools/schedule.py --next` reports this directly rather
than showing an empty list.

**Known documentation gap:** `docs/INDEX.md` §4 (Validation Status) has no rows for roughly 30
completed tasks, including `T-6.5`/`T-6.6` — the spin-2 tensor superposition. The tests exist and
pass; only the table rows are missing. Recorded here rather than left to be discovered.

### Results established so far

Selected, all reproducible from the test suite:

- **The dipole cancels.** The project's central physics premise: in momentum-conserving
  configurations the mass-dipole term vanishes to < 10⁻¹² relative across 20 seeded
  configurations, with a deliberate positive control exceeding 10⁻³.
- **Hulse–Taylor reproduced to 0.21%.** PSR B1913+16 orbital decay: −2.4031×10⁻¹² computed
  against −2.398×10⁻¹² observed.
- **Quadrupole luminosity exact to 4.1×10⁻¹⁶** against the independent closed form
  `L = (32/5)(G/c⁵)μ²a⁴ω⁶` — an algebraic identity, far stronger evidence than any
  finite-difference check.
- **The spin-2 array laws, derived and validated** (ADR-0003): element mismatch is `cos(2Δψ)`,
  maximal at **45°, not 90°**; elements 90° apart **cancel completely** where electromagnetic
  intuition predicts twice the power; alignment tolerance is `exp(−4σ²)`, so 1% gain loss
  requires co-orientation to **σ ≤ 2.87° — exactly twice as tight as spin-1**.
- **Linear memory cross-validated** to bit-for-bit agreement on-axis against an independent
  quadrupole route, as ADR-0004 predicted before the code existed.
- **The uniform-sphere `l=2` finite-size form factor**, `F₂(kR) = 1 − 5(kR)²/98`, derived and
  verified by three independent numerical routes — the strongest agreeing to 1.7×10⁻¹²
  (ADR-0007). No citable numbered equation for it exists; that outcome is recorded as the
  decision, not hidden.

- **The spin-2 array laws hold at scale, and are N-independent** (campaign R2): the
  `cos(2Δψ)` mismatch law is exact to 4.5×10⁻¹⁴ from N = 2 to N = 1000, and the 90°
  cancellation is machine-zero at every N where spin-1 reasoning predicts half the power.
- **The dull option wins by thirty-one orders of magnitude** (campaign R6): a Newtonian
  gravity tractor delivers 3.32 N against a ~43 N requirement — short by a factor of 13 —
  while radiative coupling is short by a factor of 10³². We report this because a framework
  that hid it would be worthless.
- **One wall does not bind everywhere** (campaign R5): at 10⁹ kg / 1 km / 1 MHz the
  *emission* gap goes **negative** by 6.75 decades. The concept still fails, on coupling
  (14.0 decades) and diffraction (8.16) — but the honest statement is a range, not a single
  number, and finding this forced a correction to our own README.

### Findings of independent interest

Two numerical results here are not specific to gravitational waves:

- **Differencing two ~10¹² m ranges at 40 AU returns exactly zero in float64.** Every element's
  range rounds to the same value, so 100% of the focusing information is lost with no error, no
  warning, and a plausible-looking array of zeros.
- **Absolute propagation phase is not representable, in float64 either.** At 40 AU / 1 kHz the
  phase is ~1.25×10⁸ rad, where float64's spacing is ~340× *larger* than the entire per-element
  differential. The reference/differential split is not a single-precision optimization — it is
  the only way to obtain the number at all.

Both are validated against 60-digit `decimal` references rather than the implementation's own
arithmetic.

---

## Documentation

| Document | Purpose |
|---|---|
| [`docs/HANDOVER.md`](docs/HANDOVER.md) | **Start here** — current state, what to run next, known traps |
| [`CLAUDE.md`](CLAUDE.md) | Operating instructions for AI agents working on this repo |
| [`docs/PHYSICS.md`](docs/PHYSICS.md) | First-principles derivation of the framework |
| [`docs/CLAIMS.md`](docs/CLAIMS.md) | Established physics vs. our derivation vs. conjecture, plus the epistemic firewall |
| [`docs/INDEX.md`](docs/INDEX.md) | Equation registry, module map, assumption ledger, validation status |
| [`docs/BACKLOG.md`](docs/BACKLOG.md) | Sprint plan and task specifications |
| [`docs/ERRATA.md`](docs/ERRATA.md) | Verified errors found in cited literature |
| [`docs/adr/`](docs/adr/) | Architecture decision records (7) |
| [`docs/paper/`](docs/paper/) | Manuscript drafts *(work in progress)* |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to contribute |
| [`CITATION.cff`](CITATION.cff) | How to cite this work — and the AI-assistance disclosure, with per-model commit counts |

**If you read only one thing beyond this file**, read `docs/INDEX.md` §3, the assumption ledger.
Several approximations here hold across most of the parameter space and fail at its edges — and
this project's interesting configurations live near those edges.

## Package layout

```
src/gwtb/
  core/       constants, unit scaling, validation guards, backend shim
  bodies/     mass distributions, multipole moments, elastic deformation
  kinematics/ acceleration profiles, oscillator drive synthesis
  source/     radiation: quadrupole, multipoles, memory, conservation audit
  propagate/  retarded fields, TT projection, spin-2 polarization
  array/      geometry, beamforming, grating lobes, focusing
  target/     geodesic deviation, coupling channels, deflection
  ledger/     feasibility gap report
  viz/        field slices, beam patterns, volumetric rendering
```

⚠️ **`array/beamform.py` is deliberately two things at once.** Its scalar functions
(`array_factor`, `steering_phases`, `beamwidth_3db`, `peak_sidelobe_level`, `taper`) are the
**spin-1 baseline** — ordinary classical array theory, never to be read as gravitational
radiation. Only `superpose_tt` and `mismatch_loss` carry spin-2 physics. **Any code borrowed
from antenna, radar, or acoustics references is spin-1 and will be silently wrong.** This is the
project's highest-risk bug class.

## Installation

Requires Python ≥ 3.10.

```bash
pip install -e ".[dev]"
```

Optional extras: `.[viz]` adds PyVista for volumetric rendering and VTK export. Without it,
`viz.render_volume` degrades quietly (returns `None` with a message) while `viz.export_field`
raises `RuntimeError` — the difference is deliberate — and **2 tests skip**.

A **third test skips without CuPy**, which exercises the optional GPU path in
`core/backend.py:field_grid_split_phase`. CuPy is not a declared extra; install it separately if
you need that path. A full local run is therefore **867 passed, 3 skipped**.

**On Windows** (the primary development host since 2026-07-29), a working venv lives at `.venv`.
Use it for everything — the system Python has no numpy. In **Windows PowerShell**:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

The same applies to `ruff.exe`, `mypy.exe` and `pytest.exe` under `.venv\Scripts\`.

## Development

Run the tests:

```bash
pytest -q
```

**Five checks gate every commit. All five must pass:**

```bash
ruff check src tests tools && ruff format --check src tests tools && python -m mypy src && python tools/check_citations.py && python -m pytest -q
```

⚠️ **Invoke `mypy` and `pytest` as `python -m`, not through their console-script shims.** On
the Windows development host both `.venv\Scripts\mypy.exe` and `.venv\Scripts\pytest.exe`
are broken and fail **silently** — exit 1 with no output, which reads as a failing gate that
declines to say why. `ruff` is unaffected (it is a standalone binary, not a Python shim).

`check_citations.py` is the mechanical half of this project's central rule: every public function
in `source/`, `propagate/`, `bodies/` and `array/` must carry a docstring line of the form
`Source: <reference>, eq. <number>`. **"Blanchet ch. 3" is rejected; "Blanchet eq. 3" is
accepted.** A contributor auditing this code decades from now must be able to open one page and
check one line. The tool verifies a citation is *present and specific* — it cannot verify it is
*correct*, which remains a human review gate.

See what to work on next — the scheduler batches tasks by execution tier and dependency order,
and reports externally blocked work rather than silently omitting it:

```bash
python tools/schedule.py --next
```

Completion is read from ✅ markers on task headers in `docs/BACKLOG.md`, so the plan always
matches reality. **Mark a task ✅ when you finish it.**

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md), then [`docs/HANDOVER.md`](docs/HANDOVER.md). Three
rules matter more than the rest:

1. **Never implement a physics formula from memory.** Confirm the governing equation and its
   exact equation number against a primary source first. Prefer open-access sources — a citation
   a stranger cannot open is not a citation.
2. **Never strip an `UNPHYSICAL` stamp.** Mass-dipole radiation exists only if the system's
   momentum is not conserved; that artifact is roughly 10¹⁰× the true quadrupole signal.
   Unstamped, it does not look like a bug — it looks like a breakthrough.
3. **Published sources contain errors.** See [`docs/ERRATA.md`](docs/ERRATA.md) for two we
   verified numerically. Never "fix" correct code to match a printed typo.

## Citing this work

See [`CITATION.cff`](CITATION.cff) — machine-readable, schema-valid, and rendered
automatically by GitHub's "Cite this repository" button.

It also carries the project's **AI-assistance disclosure**. This work was produced with
extensive help from Anthropic's Claude: as of commit `93f215c`, 55 of 61 commits carry a
`Co-Authored-By` trailer naming the model. The models are deliberately **not** listed as
authors — Nature, Science and all Springer-Nature journals hold that Large Language Models
cannot satisfy authorship criteria, because authorship carries accountability that cannot
be assigned to a tool. Disclosure is required; authorship is prohibited. Accountability for
every claim in this repository rests with the human author.

The counts are a snapshot. The authoritative record is the git history itself:

```bash
git log --format='%b' | grep -i '^Co-Authored-By:' | sort | uniq -c
```

## License

Apache-2.0. The explicit patent grant is deliberate: this project invites outside innovators to
invent hardware against our framework, and that clause protects both them and downstream users.
