# Changelog

All notable changes to this project are recorded here. The format loosely follows
[Keep a Changelog](https://keepachangelog.com/); dates are `YYYY-MM-DD`.

## [0.1.1] — 2026-08-16

The release Zenodo actually archives — the GitHub–Zenodo integration was enabled after
`v0.1.0` published, and Zenodo only archives releases created after the integration is turned
on. No physics or behavior changed; this version exists to trigger that archive with correct
metadata in place.

- Added the author's ORCID to `CITATION.cff` (`0009-0007-1522-7282`), closing the placeholder
  that file carried since its creation — filed specifically so the identifier is present before
  Zenodo mints a DOI against this metadata, since archived records aren't meant to be quietly
  edited afterward.
- Capped `numpy<2.5` in `pyproject.toml`. NumPy 2.5's bundled type stubs started using PEP 695
  syntax unconditionally, which `mypy` correctly rejects under this project's `python_version =
  "3.10"` target (the real supported floor) regardless of which interpreter runs it. Broke CI
  four days after `v0.1.0`, from dependency drift alone — no code change on this project's side.

## [0.1.0] — 2026-08-11

First citable release (T-12.8, Sprint 12, Gate G4). The framework is feature-complete against
the Sprint 0 plan: 118 tasks across 12 sprints, `docs/PHYSICS.md` fully sourced with every
Category B claim carrying a derivation and a reducing limit, and the feasibility ledger
publishing its walls on every run rather than asserting a conclusion.

**Not a 1.0 semver claim of production maturity.** The PyPI classifier stays
`Development Status :: 2 - Pre-Alpha` and the package version stays `0.1.0` — the backlog task
that produces this release is named "v1.0 release" in the loose sense of "first release worth
citing," and this project's own ledger is the reason not to read more into it than that: several
walls remain 20+ decades from closing (see below), and a project whose whole point is stating
its own gap honestly should not brand itself past what it has shown.

### The transferable result

Phased-array theory extended from spin-1 (electromagnetic) to spin-2 (gravitational) fields:
element mismatch is `cos(2Δψ)`, not `cos(Δψ)`; elements 90° apart cancel completely where
electromagnetic intuition predicts a doubling of power; and the orientation tolerance for 1%
gain loss is exactly twice as tight as the electromagnetic case. Derived and validated
(`docs/PHYSICS.md` §5.1, claim B-1, [ADR-0003](docs/adr/0003-spin2-superposition.md)) — no
external reference implementation exists to check this against, so the project built its own
auditability in instead: every physics function carries a machine-checked citation to a numbered
equation in an open-access source (`tools/check_citations.py`), every claim is filed as
established / derived / conjectural (`docs/CLAIMS.md`), and results from a non-momentum-conserving
source are inseparable from an `UNPHYSICAL` provenance stamp.

### The feasibility ledger — what is quantified and what is not

Run `examples/deflection_scenario.py` or `tools/run_campaign.py` for live numbers. Reference
scenario: 1 km asteroid at 40 AU, 8×8 phased array, 1250 m spacing.

| Wall | Quantified | Headline figure |
|---|---|---|
| **Diffraction** | Yes | `D/λ ≥ 1.029 r/w`, ~6.2×10⁹ wavelengths for a 1 km spot at 40 AU, independent of frequency (B-3) |
| **Coupling** | Yes | Radiative coupling is `(v/c)⁶`-suppressed relative to the near-zone gravity-tractor channel; measured 1.31×10⁻³¹ ratio decomposes exactly into mechanism × geometry (B-5) |
| **Magnitude** | Yes | Emission gap ranges **−6.75 to +29.25 decades** across the scoping set (C-2, R5 campaign) — the negative end does not close the gap, since coupling and diffraction still bind at that same source |
| **Transducer** | **No, deliberately** | Conjecture C-1 — some mechanism converting stored energy to gravitational radiation at useful efficiency — is out of scope by project charter and is not modeled. Reported here as an explicit unaddressed wall, not a fabricated number |

The best case found anywhere in the 432-cell deflection tradespace (`target/tradespace.py`,
B-9, paper §R8) is still short by **29.0 decades**.

### Test suite

76 benchmark tests across the 9 originally-scoped `Benchmark:` backlog tasks (T-1.9, T-1.10,
T-2.8, T-3.9, T-6.9, T-9.8, T-10.2, T-12.2, T-12.3), plus 3 additional benchmark modules
(`test_body_sensitivity`, `test_performance`, `test_smoke`) added as the suite grew past its
Sprint-0-era count. **All pass.** 1193 tests pass overall, 3 skipped (CuPy/PyVista optional
dependencies absent in this environment).

### Documentation completed this sprint

- [`docs/PHYSICS.md`](docs/PHYSICS.md) (T-12.5) — the last three `[UNVERIFIED]` citation
  markers replaced; every Category B claim (B-1…B-9) now carries a derivation and an explicit
  reducing limit to a Category A result.
- [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) (T-12.7) — clone-to-first-PR on-ramp.
- [`examples/deflection_scenario.py`](examples/deflection_scenario.py) (T-12.1) — the
  end-to-end demonstration referenced throughout this release.

### Known limitations, stated rather than hidden

- The transducer problem (C-1) is untouched — no mechanism is proposed or assumed for
  converting stored energy into engineered gravitational radiation.
- Whether the gap quantified by C-2 is closable at all remains open; the emission-magnitude
  wall going negative at 1 MHz does not resolve it, because coupling and diffraction still bind.
- Near-field focusing is out of scope; at the project's 40 AU reference range, focusing is
  numerically degenerate with steering (`docs/PHYSICS.md` §8.1).

[0.1.1]: https://github.com/sudo-install-gravity/tractor-beam-cathedral/releases/tag/v0.1.1
[0.1.0]: https://github.com/sudo-install-gravity/tractor-beam-cathedral/releases/tag/v0.1.0
