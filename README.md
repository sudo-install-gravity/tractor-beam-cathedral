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

---

## What this tool actually computes

1. Gravitational-wave characteristics from accelerating spherical masses, using equations
   traceable to primary literature (every implemented equation carries a citation).
2. Radiation from **finite maneuvers** — non-impulsive acceleration profiles — including the
   linear memory effect that a finite maneuver leaves behind.
3. The effect of body parameters (radius, density, elastic response) on emitted radiation.
4. Phased-array beamforming, extended from the spin-1 electromagnetic case to the **spin-2**
   gravitational case.
5. Visualization of field propagation and beam patterns.
6. Spatiotemporal focusing using mutually incommensurate (prime-valued) drive frequencies.

And, on every run, a **feasibility ledger**: a quantitative statement of how far the modeled
configuration sits from actually deflecting an asteroid.

## What this tool is honest about

The feasibility ledger exists because three walls stand between this concept and reality, and
a framework that hides them would be worse than useless:

| Wall | Statement |
|---|---|
| **Diffraction** | Focusing to a 1 km spot at 40 AU requires an aperture of **6×10⁹ wavelengths**, at any frequency. |
| **Coupling** | A gravitational wave produces tidal *strain*, not net force. Momentum transfer requires absorption, and an asteroid's absorption cross-section is negligible. |
| **Magnitude** | Roughly 40 orders of magnitude separate plausible engineered sources from deflection-relevant power. Radiated power scales as f⁶, making frequency the dominant lever. |

The most valuable output of this project is not a working tractor beam. It is a rigorous,
parameterized quantification of **which orders of magnitude must be attacked, and in what
order** — so that contributors across the project's lifetime aim at the real bottleneck rather
than a comfortable one.

## Status

Pre-alpha. Sprint 0 (foundation and governance). Nothing here computes physics yet.

## Documentation

| Document | Purpose |
|---|---|
| [`docs/HANDOVER.md`](docs/HANDOVER.md) | **Start here** — current state, what to run next, known traps |
| [`CLAUDE.md`](CLAUDE.md) | Operating instructions for AI agents working on this repo |
| [`docs/PHYSICS.md`](docs/PHYSICS.md) | First-principles derivation of the framework |
| [`docs/CLAIMS.md`](docs/CLAIMS.md) | Established physics vs. our derivation vs. conjecture |
| [`docs/INDEX.md`](docs/INDEX.md) | Equation registry, module map, assumption ledger |
| [`docs/BACKLOG.md`](docs/BACKLOG.md) | Sprint plan and task specifications |
| [`docs/ERRATA.md`](docs/ERRATA.md) | Verified errors found in cited literature |
| [`docs/adr/`](docs/adr/) | Architecture decision records |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to contribute |

## Installation

```bash
pip install -e ".[dev]"
```

## Development

```bash
pytest
```

See what to work on next — the scheduler batches tasks by execution tier and
dependency order:

```bash
python tools/schedule.py --next
```

## License

Apache-2.0. The explicit patent grant is deliberate: this project invites outside innovators to
invent hardware against our framework, and that clause protects both them and downstream users.
