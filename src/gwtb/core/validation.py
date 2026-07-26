"""Input validation for the public API.

Implements the contracts in ``docs/adr/0002-array-conventions.md``:
``masses (N,)``, body arrays ``(N, 3)``, tensors with trailing indices,
``n_hat`` a unit vector, float64 throughout.

Two rules here are load-bearing rather than defensive:

* **float32 is rejected, not upcast.** Silently promoting hides the fact that
  precision was already lost upstream. Absolute phase over 40 AU is ~1e10
  wavelengths, well beyond float32's ~1e-7 relative precision.
* **Non-unit ``n_hat`` raises.** An unnormalised direction produces a
  plausible-looking but wrong TT projection, which is expensive to find later.

Per ADR-0002 §8 these run at public boundaries only; private helpers assume
validated input.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

UNIT_TOL = 1e-12
"""Tolerance on |n_hat| = 1."""


def _reject_float32(arr: NDArray[np.floating], name: str) -> None:
    if arr.dtype == np.float32:
        raise TypeError(
            f"{name} is float32; gwtb requires float64 (see docs/adr/0002-array-conventions.md "
            f"§5). Passing float32 means precision was already lost upstream, so it is rejected "
            f"rather than promoted."
        )


def as_float64(a: ArrayLike, name: str) -> NDArray[np.float64]:
    """Coerce to a float64 array, rejecting float32 and non-finite values."""
    arr = np.asarray(a)
    if arr.dtype == np.float32:
        _reject_float32(arr, name)
    if not np.issubdtype(arr.dtype, np.number):
        raise TypeError(f"{name} must be numeric, got dtype {arr.dtype}")
    out = np.asarray(arr, dtype=np.float64)
    if not np.all(np.isfinite(out)):
        raise ValueError(f"{name} contains non-finite values")
    return out


def as_masses(masses: ArrayLike) -> NDArray[np.float64]:
    """Validate a mass array: shape ``(N,)``, float64, strictly positive."""
    m = as_float64(masses, "masses")
    if m.ndim != 1:
        raise ValueError(f"masses must have shape (N,), got {m.shape}")
    if m.size == 0:
        raise ValueError("masses is empty")
    if np.any(m <= 0.0):
        raise ValueError("masses must be strictly positive")
    return m


def as_body_array(a: ArrayLike, name: str, n_bodies: int | None = None) -> NDArray[np.float64]:
    """Validate a per-body vector array: shape ``(N, 3)``, float64.

    ``n_bodies`` cross-checks the leading axis against the mass array, catching
    the common error of passing positions for a different body count.
    """
    arr = as_float64(a, name)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError(f"{name} must have shape (N, 3), got {arr.shape}")
    if n_bodies is not None and arr.shape[0] != n_bodies:
        raise ValueError(
            f"{name} has {arr.shape[0]} bodies but masses has {n_bodies}; "
            f"the leading axis is the body index (ADR-0002 §1)"
        )
    return arr


def as_tensor_3x3(a: ArrayLike, name: str) -> NDArray[np.float64]:
    """Validate a rank-2 spatial tensor: shape ``(3, 3)``, float64."""
    arr = as_float64(a, name)
    if arr.shape != (3, 3):
        raise ValueError(f"{name} must have shape (3, 3), got {arr.shape}")
    return arr


def as_unit_vector(n_hat: ArrayLike, name: str = "n_hat") -> NDArray[np.float64]:
    """Validate a direction: shape ``(3,)``, float64, unit norm.

    Raises rather than normalising. A caller passing a non-unit vector has a bug
    upstream, and silently fixing it here would hide that while still producing
    a wrong TT projection in the cases we could not detect.
    """
    v = as_float64(n_hat, name)
    if v.shape != (3,):
        raise ValueError(f"{name} must have shape (3,), got {v.shape}")
    norm = float(np.linalg.norm(v))
    if abs(norm - 1.0) > UNIT_TOL:
        raise ValueError(
            f"{name} must be a unit vector; |{name}| = {norm!r} differs from 1 by "
            f"{abs(norm - 1.0):.3e} (tolerance {UNIT_TOL:g}). Normalise before calling."
        )
    return v


__all__ = [
    "UNIT_TOL",
    "as_body_array",
    "as_float64",
    "as_masses",
    "as_tensor_3x3",
    "as_unit_vector",
]
