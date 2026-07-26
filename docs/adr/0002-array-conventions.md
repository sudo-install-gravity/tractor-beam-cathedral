# ADR 0002 — Array shape, dtype, and unit conventions

- **Status:** Accepted
- **Date:** 2026-07-26
- **Sprint:** 1 (pre-implementation)

## Context

An audit of the Sprint 1 task specs against the Definition of Ready found that no task specified
array shapes, dtypes, or unit conventions. Every Sprint 1 task touches these, each would have
guessed independently, and the guesses would have diverged.

This is the kind of defect a per-task review does not catch, because each task is individually
reasonable — the incoherence only appears at integration, in Sprint 2, which is the expensive
place to find it. Fixing it costs one document now.

## Decision

The following conventions are binding on all of `src/gwtb/`. Changing them requires a new ADR.

### 1. Body collections are "first axis is the body"

```
masses         (N,)      float64    kg
positions      (N, 3)    float64    m
velocities     (N, 3)    float64    m/s
accelerations  (N, 3)    float64    m/s^2
jerks          (N, 3)    float64    m/s^3
```

`N` is the number of point masses or array elements. Rationale: this matches NumPy's row-major
memory layout, so per-body slices are contiguous; it reads naturally as a list of bodies; and it
matches the convention in `astropy` and most N-body codes.

### 2. Tensors carry their indices in the trailing axes

```
quadrupole moment Q_ij      (3, 3)          float64
TT projector      Lambda    (3, 3, 3, 3)    float64
strain            h_ij      (3, 3)          float64   dimensionless
```

Time series prepend a leading axis: `(T, 3, 3)`. Field grids prepend their spatial axes:
`(nx, ny, nz, 3, 3)`. **Trailing tensor indices, always** — so `einsum` subscripts are identical
whether or not a leading axis is present, and `...ij` broadcasting works unchanged.

### 3. Directions are unit vectors, named `n_hat`, shape `(3,)`

Functions taking `n_hat` **must** validate `|n_hat| = 1` to `atol=1e-12` and raise `ValueError`
otherwise. A silently unnormalized direction produces a plausible, wrong TT projection — one of
the failure modes that is expensive to find later.

### 4. SI units internally, everywhere, no exceptions

Inputs and outputs are SI. No geometric units (`G = c = 1`) anywhere in `src/gwtb/`.

This costs some elegance and is deliberate. Much of the source literature works in geometric
units — Flanagan & Hughes Eq. (4.23) is an example — and the conversion is exactly where factors
of `G/c⁴` get dropped. Keeping SI throughout means every implemented equation carries its
dimensional factors explicitly and can be dimension-checked against its citation.

Strain is dimensionless but is *represented* in scaled units via `gwtb.core.units.StrainScale`
(h ~ 1e-40 is subnormal in float32 and loses precision in intermediate float64 products).
Functions returning strain return **physical** dimensionless strain; scaling is applied at
storage and display boundaries only.

### 5. float64 everywhere

No float32 anywhere in `src/gwtb/` without an explicit ADR authorizing it. See `PHYSICS.md` §7:
absolute phase over 40 AU is ~1e10 wavelengths, beyond float32's ~1e-7 relative precision.

Functions should not silently upcast. Validate `dtype` on public entry points and raise on
float32 input rather than promoting it, so precision loss upstream is caught rather than masked.

### 6. Trace-free by convention

`Q_ij` throughout the codebase means the **trace-free** quadrupole moment
(Blanchet eq. 3), not the second moment `I_ij` (Flanagan & Hughes eq. 4.17).

Where a source uses the second moment, the conversion `Q_ij = I_ij − ⅓δ_ij I` is applied at the
point of use and noted in the docstring. Function names distinguish them: `second_moment()` vs.
`quadrupole_moment()`.

### 7. Time is a float, seconds, and retarded time is explicit

Functions that evaluate fields take `t` as coordinate time at the **field point**, and compute
retarded time internally **per source element** — never from an array centroid. See
`code-reviewer.md`; retardation from the wrong origin is a quiet, high-damage error.

### 8. Validation is at public boundaries only

Public functions validate shapes, dtypes, and normalization. Private helpers (`_name`) assume
validated input and do not re-check — this keeps hot loops clean while making the contract
explicit at the API surface.

## Consequences

**Positive:** every Sprint 1 task now has an unambiguous contract, making them
Sonnet-Low-executable. `einsum` subscripts are uniform across the codebase. Dimensional
consistency is checkable against citations because units are never implicit.

**Negative:** SI-only means carrying `G/c⁴` and `G/c⁵` factors that geometric units would hide,
and the literature must be translated at each point of use rather than transcribed. That
translation is precisely where errors would otherwise be introduced silently, so the cost is
accepted deliberately.

**Enforcement:** `tests/unit/test_conventions.py` asserts these contracts against the public API
as it grows.
