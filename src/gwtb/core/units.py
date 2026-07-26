"""Scaled representation for gravitational-wave strain.

Strain in this project runs around ``1e-40``. That is **subnormal** in IEEE
binary32 (smallest normal ``~1.18e-38``), and even in binary64 it leaves little
headroom once strains are squared or accumulated over a large array. Carrying a
scaled representation keeps stored and displayed values at order unity.

Per ``docs/adr/0002-array-conventions.md`` §4, functions in ``gwtb`` return
**physical** dimensionless strain. Scaling is applied only at storage and
display boundaries — never inside the physics.
"""

from __future__ import annotations

import math
from typing import overload

import numpy as np

DEFAULT_REFERENCE = 1e-40
"""Reference strain. Chosen so a typical value in this project maps to ~1."""


class StrainScale:
    """Convert between physical strain and a scaled representation.

    Parameters
    ----------
    reference
        Physical strain that maps to ``1.0`` in scaled units. Must be positive
        and finite.

    Examples
    --------
    >>> scale = StrainScale()
    >>> scale.to_scaled(1e-40)
    1.0
    >>> scale.from_scaled(1.0)
    1e-40
    """

    __slots__ = ("reference",)

    def __init__(self, reference: float = DEFAULT_REFERENCE) -> None:
        if not isinstance(reference, (int, float)) or isinstance(reference, bool):
            raise TypeError(f"reference must be a real number, got {type(reference).__name__}")
        if not math.isfinite(reference):
            raise ValueError(f"reference must be finite, got {reference!r}")
        if reference <= 0.0:
            raise ValueError(f"reference must be positive, got {reference!r}")
        self.reference = float(reference)

    @overload
    def to_scaled(self, h: float) -> float: ...
    @overload
    def to_scaled(self, h: np.ndarray) -> np.ndarray: ...

    def to_scaled(self, h: float | np.ndarray) -> float | np.ndarray:
        """Physical strain -> scaled units."""
        return h / self.reference

    @overload
    def from_scaled(self, h_s: float) -> float: ...
    @overload
    def from_scaled(self, h_s: np.ndarray) -> np.ndarray: ...

    def from_scaled(self, h_s: float | np.ndarray) -> float | np.ndarray:
        """Scaled units -> physical strain."""
        return h_s * self.reference

    def __repr__(self) -> str:
        return f"{type(self).__name__}(reference={self.reference!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StrainScale):
            return NotImplemented
        return self.reference == other.reference

    def __hash__(self) -> int:
        return hash((type(self).__name__, self.reference))


__all__ = ["DEFAULT_REFERENCE", "StrainScale"]
