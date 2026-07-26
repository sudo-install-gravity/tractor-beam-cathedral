# ADR 0001 — Use linearized GR with retarded multipole expansion, not numerical relativity

- **Status:** Accepted
- **Date:** 2026-07-26
- **Sprint:** 0

## Context

We must model the generation and propagation of gravitational waves from accelerating masses
out to 40 AU. The obvious candidates are the mature open-source numerical relativity codes —
Einstein Toolkit, GRChombo, SpECTRE, NRPy+ — which represent decades of community effort and
are the standard tools for gravitational-wave source modeling.

The temptation to reuse them is strong, and reuse is normally the right instinct.

## Decision

**Do not use numerical relativity. Implement linearized GR with a retarded multipole
expansion.**

## Rationale

**1. The regime is wrong for NR.** Numerical relativity solves the full nonlinear Einstein
equations in a 3+1 split, and exists because the strong-field region near merging compact
objects cannot be treated perturbatively. Strains there are of order h ~ 10⁻¹ near the horizon.

In this project h ~ 10⁻⁴⁰. We are forty orders of magnitude into the linear regime. Using NR
here would be solving a nonlinear PDE to recover, at enormous cost, an answer that a linear
integral gives exactly.

**2. The scales are wrong for NR.** NR grids are sized in geometric units of the source mass,
typically spanning hundreds of M. Propagating a field to 40 AU = 6×10¹² m on such a grid is not
merely expensive — it is not what the codes are built to do. Waveform extraction at future null
infinity exists precisely because NR *cannot* carry a field to large radius directly.

**3. Linearity is not a convenience here — it is the enabling property.** The entire project
rests on superposing the fields of many array elements. Superposition holds *exactly* in the
linear regime. If we were in a regime where NR were necessary, fields would not superpose, and
"phased array of gravitational wave sources" would be a meaningless phrase.

Choosing the linear formulation is therefore not a simplification we accept reluctantly. It is
the mathematical fact that makes the concept coherent enough to model at all.

**4. Auditability.** A cathedral project needs code a contributor can check against a textbook.
The quadrupole formula is four lines and appears in MTW; an NR evolution scheme is not
auditable in the same way by a newcomer decades from now.

## Consequences

**Positive**

- Fast. Field evaluation is an integral, not a PDE evolution — CPU-tractable, no supercomputer.
- Exact to linear order; no truncation error from the gravity solver.
- Superposition is exact, licensing the phased-array formalism.
- Auditable against primary sources equation by equation.
- No dependency on large NR toolchains.

**Negative**

- Cannot model strong-field or nonlinear effects. Acceptable: none occur here.
- Nonlinear ("Christodoulou") memory is inaccessible; only linear memory is available. This is
  a real limitation, but linear memory is the dominant term for the finite-maneuver
  configurations we care about.
- We must implement and validate our own source physics rather than inheriting a battle-tested
  code. Mitigated by the benchmark suite (`docs/INDEX.md` §4), which validates against analytic
  results and cross-checks against `PyCBC`, `LALSuite`, and `scri`.

**Reversal condition**

If a future configuration enters a regime where h is large enough that nonlinearity matters, or
where nonlinear memory is a leading effect, this decision must be revisited. Given the
magnitudes in `PHYSICS.md` §8, that is not a near-term concern.

## What we still reuse

Rejecting NR does not mean rejecting the ecosystem:

- `arraytool` — phased-array factor and tapering (scalar/spin-1 baseline to validate against)
- `gwpy`, `PyCBC` — time-series containers, spectral tooling, reference waveforms
- `LALSuite` — reference TT projections and antenna patterns for cross-validation
- `scri`, `sxs` — memory-effect reference implementations
- `EinsteinPy` — geodesic integration for target response
- `PyVista`/VTK, ParaView — field visualization
- `astropy`, `poliastro` — constants, units, orbit propagation
