# Tractor Beam Cathedral

**`gwtb`** — a modeling and simulation framework for a theoretical asteroid-deflection
concept: an array of massive spheres undergoing controlled finite maneuvers, phased so their
gravitational radiation constructively interferes at a target out to 40 AU.

This is a **cathedral project**. It is expected to span more than one human lifetime. We build
the theoretical framework; we deliberately leave the "transducer" engineering — whatever
converts stored energy into useful gravitational radiation — to future contributors.

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

## License

Apache-2.0. The explicit patent grant is deliberate: this project invites outside innovators to
invent hardware against our framework, and that clause protects both them and downstream users.
