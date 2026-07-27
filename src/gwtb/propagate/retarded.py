"""Retarded-time field evaluation from a collection of point sources.

**Retarded time is computed per element, not from an array centroid.** For an
array with baseline comparable to the light-travel-time scale of interest,
using a single array-center retardation for every element is a real error,
not a harmless simplification: it desynchronizes elements by their
individual path-length differences, which is exactly the phase information a
phased array's coherence depends on. See T-6.7's acceptance test for a case
where the two choices give detectably different answers.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.constants import c
from gwtb.core.validation import as_float64
from gwtb.source.quadrupole import strain_tt


@dataclass
class PointSource:
    """A single radiating element: a fixed position and its quadrupole
    second-derivative history.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 3 (pure data container; see field_at)

    Parameters
    ----------
    position
        Shape ``(3,)``, m. Fixed source location.
    q_ddot
        Callable ``t -> (3, 3)`` array, kg m^2 s^-2: the source's own
        ``d2Q_ij/dt2`` evaluated at the given **source-local** time (i.e.
        already accounting for anything internal to the source; this
        function supplies only the propagation-time retardation).
    """

    position: NDArray[np.float64]
    q_ddot: Callable[[float], NDArray[np.float64]]

    def __post_init__(self) -> None:
        self.position = as_float64(self.position, "position")
        if self.position.shape != (3,):
            raise ValueError(f"position must have shape (3,), got {self.position.shape}")


def field_at(
    sources: list[PointSource], field_point: ArrayLike, time: float
) -> NDArray[np.float64]:
    """Superposed TT strain at ``field_point`` and ``time`` from a set of
    point sources, each retarded by its own source-to-observer light time.

    .. code-block:: text

        h_ij(x, t) = sum_a strain_tt( q_ddot_a(t - |x - x_a|/c), |x - x_a|, n_hat_a )

    This does not project onto a *common* observation direction TT frame —
    each term uses its own ``n_hat_a`` (source-to-field-point direction), per
    :func:`gwtb.source.quadrupole.strain_tt`. Combining sources into a common
    TT frame along one shared direction is :func:`gwtb.array.beamform.superpose_tt`
    (T-6.5, tensor spin-2 superposition), not this function.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 2 (per-source
    strain, applied at each source's own retarded time)

    Parameters
    ----------
    sources
        Point sources contributing to the field.
    field_point
        Shape ``(3,)``, m. Observation location.
    time
        Observation time, s.

    Returns
    -------
    ndarray
        Shape ``(3, 3)``, dimensionless. Sum of each source's retarded
        contribution.
    """
    x = as_float64(field_point, "field_point")
    if x.shape != (3,):
        raise ValueError(f"field_point must have shape (3,), got {x.shape}")
    if not np.isfinite(time):
        raise ValueError(f"time must be finite, got {time!r}")
    if len(sources) == 0:
        raise ValueError("sources must be non-empty")

    total = np.zeros((3, 3), dtype=np.float64)
    for source in sources:
        displacement = x - source.position
        r = float(np.linalg.norm(displacement))
        if r == 0.0:
            raise ValueError("field_point coincides with a source position")
        n_hat = displacement / r
        retarded_time = time - r / c
        q_ddot = source.q_ddot(retarded_time)
        total = total + strain_tt(q_ddot, r, n_hat)
    return total


__all__ = ["PointSource", "field_at"]
