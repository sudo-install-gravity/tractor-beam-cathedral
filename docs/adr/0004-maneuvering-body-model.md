# ADR 0004 — Modeling a single maneuvering body as a symmetric two-body system

- **Status:** Accepted (recorded retroactively)
- **Date:** 2026-07-27
- **Arises from:** T-3.8 `waveform_from_profile`

## Context

T-3.8 asked for "the strain waveform radiated by a sphere executing a finite maneuver." It was
tiered `sonnet-low`, meaning **zero open design decisions** — but it contained one, and the
implementing session correctly noticed, made a call, and documented it in the docstring as
*"Modeling decision (this function's own, not an external citation)."*

That disclosure is exactly the right behavior. This ADR exists because the decision is real,
downstream work depends on it, and a modeling choice recorded only in a docstring is not
auditable.

**The hidden decision:** a single accelerating point mass is not an isolated, momentum-conserving
source. Its mass dipole does not cancel, so the leading radiation term is a dipole that exists
only because a hidden external agent is pushing — roughly 10¹⁰ times the true quadrupole signal
(`CLAUDE.md` rule 2). The task spec never said what to do about this.

## Decision

**Model the maneuvering sphere as one half of a symmetric two-body system**: two point masses of
`body.mass / 2` at `+x(t)` and `−x(t)` along a fixed axis, where `x(t)` is the profile's scalar
position.

The center of mass never moves, so the configuration is momentum-conserving by construction and
its quadrupole is a physical radiating source with no hidden dipole term.

## Verification

**Dipole cancels exactly**, not approximately — `Σ m x = 0` and `Σ m a = 0` to `0.0` at every
sampled time, since the construction is symmetric by definition rather than by cancellation of
finite quantities.

**The post-maneuver offset is the linear memory, arrived at independently.** After the maneuver
the bodies coast at constant velocity, so `Q̈` retains a constant `2 Σ m v_i v_j` term and the
strain settles to a nonzero constant. That constant should equal the Braginsky & Thorne linear
memory — and it does, **exactly**:

| Route | `h₊` |
|---|---|
| A — settled value of `waveform_from_profile` (quadrupole route) | `5.5377265143e-48` |
| B — `Δh = (4G/c⁴r) Λ : Δ[Σ M_A v^k v^l]` (T-3.7's specified formula) | `5.5377265143e-48` |

Maximum relative difference: **0.0**.

This is not a coincidence of implementation — it is the quadrupole formula and the linear-memory
formula agreeing, as they must, because `Q̈ → 2 Σ m v_i v_j` once acceleration ceases.

> **Refinement, 2026-07-31 (T-3.7 landed).** The `0.0` above holds for observation *along the
> symmetry axis*, which is the geometry measured here, and `tests/benchmarks/test_memory.py`
> asserts it bit-for-bit. It does **not** generalize to oblique observation directions, where the
> two routes agree to **1 ULP** (~2e-16 relative) instead. The cause is arithmetic, not physics:
> the quadrupole route forms `2 Σ m v v − (2/3) δ (v·v)` and then TT-projects, while the memory
> route projects `Σ m v v` directly. The projection analytically removes the trace term, but the
> rounding incurred in forming and subtracting it does not vanish. Asserting bit-equality off-axis
> would be asserting a property of float64 operation ordering, so the benchmark asserts 4 ULP
> there and exactness on-axis.

## Consequences

**Positive.** T-3.8 radiates a physically realizable field with no `UNPHYSICAL` stamp needed.
And **T-3.7 (linear memory) now has an independent cross-check that exists before it is
written** — its implementation must reproduce the settled value of `waveform_from_profile` to
machine precision. A benchmark asserting that agreement should be added when T-3.7 lands.

**Negative.** The function models *two counter-maneuvering half-spheres*, not *one sphere*. The
radiated field is not what a single sphere pushed by an external agent would produce — that
configuration is unphysical and is deliberately routed through the `UNPHYSICAL`-stamped dipole
path (T-2.2, T-2.4) instead. Callers must not read `waveform_from_profile` as "the field of a
thrusting spacecraft."

**Process finding.** T-3.8 was tiered `sonnet-low` on the assumption it had no open decisions. It
had one, and only the implementer's honesty surfaced it. The Definition of Ready check should ask
explicitly, for any task involving an accelerating body: *what supplies the reaction, and does
the dipole cancel?* That question generalizes — it is the same one that produced decision 1 at
project inception.

## Reversal condition

If a future task needs the field of a genuinely single accelerating body — for instance to
quantify how large the spurious dipole would be — it must use the stamped dipole path rather
than changing this construction. Silently altering the configuration here would change results
that downstream tasks have already validated against.
