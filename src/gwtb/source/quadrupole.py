"""Quadrupole radiation: strain at an observer, and total radiated power.

These two functions are the leading-order description of gravitational radiation
from a slowly-moving, weakly self-gravitating source, and everything else in
``gwtb`` reduces to them in the appropriate limit.

Both carry explicit factors of ``G/c^4`` and ``G/c^5``. Much of the literature
works in geometric units where those vanish (Flanagan & Hughes eq. 4.23 is an
example); ADR-0002 §4 keeps this codebase in SI precisely so those factors stay
visible and dimension-checkable against the citation.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.constants import G_OVER_C4, G_OVER_C5
from gwtb.core.validation import as_tensor_3x3
from gwtb.propagate.tt_projection import apply_tt


def strain_tt(q_ddot: ArrayLike, r: float, n_hat: ArrayLike) -> NDArray[np.float64]:
    """Transverse-traceless strain ``h_ij`` from a source quadrupole.

    .. code-block:: text

        h_ij^TT = (2G / (c^4 r)) * Lambda_ij,kl * d2Q_kl/dt2

    **This function does not compute retarded time.** ``q_ddot`` is taken as an
    already-evaluated tensor; the caller is responsible for having evaluated it
    at ``t - r/c``. Retardation belongs in :mod:`gwtb.propagate.retarded`, where
    it must be computed per source element rather than from an array centroid.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 2

    Parameters
    ----------
    q_ddot
        Shape ``(3, 3)``, kg m^2 s^-2. Second time derivative of the trace-free
        quadrupole moment, evaluated at retarded time.
    r
        Distance from source to observer, m. Must be positive.
    n_hat
        Shape ``(3,)`` unit vector from source to observer.

    Returns
    -------
    ndarray
        Shape ``(3, 3)``, dimensionless. Symmetric, traceless, and transverse to
        ``n_hat``. Physical strain — apply :class:`gwtb.core.units.StrainScale`
        only at storage or display boundaries.
    """
    q = as_tensor_3x3(q_ddot, "q_ddot")

    if not np.isscalar(r) and np.asarray(r).ndim != 0:
        raise TypeError("r must be a scalar distance in metres")
    r_val = float(r)
    if not np.isfinite(r_val):
        raise ValueError(f"r must be finite, got {r!r}")
    if r_val <= 0.0:
        raise ValueError(f"r must be positive, got {r_val!r}")

    return (2.0 * G_OVER_C4 / r_val) * apply_tt(q, n_hat)


def luminosity(q_dddot: ArrayLike) -> float:
    """Total gravitational-wave power radiated in all directions.

    .. code-block:: text

        F = (G / (5 c^5)) * d3Q_ab/dt3 * d3Q_ab/dt3

    The ``G/c^5`` prefactor is ``2.76e-53`` in SI, and that single number is
    most of why this project's feasibility gap is what it is — see
    ``docs/PHYSICS.md`` §8.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 4

    Parameters
    ----------
    q_dddot
        Shape ``(3, 3)``, kg m^2 s^-3. Third time derivative of the trace-free
        quadrupole moment. Must be computed analytically — see
        :func:`gwtb.bodies.multipole.quadrupole_third_derivative`.

    Returns
    -------
    float
        Radiated power in W. Non-negative, being a sum of squares.
    """
    q3 = as_tensor_3x3(q_dddot, "q_dddot")
    return float(G_OVER_C5 / 5.0 * np.einsum("ij,ij->", q3, q3))


__all__ = ["luminosity", "strain_tt"]
