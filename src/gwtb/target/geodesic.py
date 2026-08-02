"""Geodesic deviation: how a passing gravitational wave moves free-falling
test masses relative to each other.

A GW does not accelerate a free body's center of mass — it is a statement
about *curvature*, not force, and produces only a **relative, tidal**
acceleration between separated masses (claim A-6, ``docs/CLAIMS.md``). This is
the mechanism through which any of this project's coupling channels
(``target/coupling.py``) could act on a real target at all.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.validation import as_float64, as_tensor_3x3


def deviation_acceleration(h_ddot: ArrayLike, separation: ArrayLike) -> NDArray[np.float64]:
    """Relative acceleration between two nearby free-falling test masses.

    .. code-block:: text

        d2(xi_i)/dt2 = (1/2) * (d2 h_ij^TT / dt2) * xi_j

    where ``xi_i`` is the coordinate separation vector between the two masses
    in the TT gauge.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 3.11

    Derived there from the geodesic deviation equation (their eq. 3.7)
    specialized to the linearized TT-gauge Riemann tensor (their eq. 2.21),
    evaluated in the local proper reference frame of one of the two masses.
    Their eq. (3.11) is the coordinate-acceleration form used directly here;
    the physically observed displacement follows by time-integration, since a
    free-falling mass sits at *fixed coordinate position* in the TT gauge —
    it is the ruler between the masses that appears to move, not the masses
    themselves.

    **Transverse to the propagation direction** is not separately enforced
    here: it follows automatically because ``h_ddot`` is TT (transverse to
    ``n_hat`` by construction wherever it is produced, e.g.
    :func:`gwtb.source.quadrupole.strain_tt`), so contracting it with *any*
    separation vector — including one with a component along ``n_hat`` —
    still yields an acceleration with no component along ``n_hat``, because
    the TT tensor's own rows/columns along ``n_hat`` are zero.

    Parameters
    ----------
    h_ddot
        Shape ``(3, 3)``. Second time derivative of the TT strain,
        ``d2 h_ij^TT / dt2``, at the detector's location.
    separation
        Shape ``(3,)``, m. Coordinate separation vector between the two
        masses, in the same TT frame as ``h_ddot``.

    Returns
    -------
    ndarray
        Shape ``(3,)``, m/s^2. The relative acceleration ``d2 xi_i/dt2``.
    """
    h = as_tensor_3x3(h_ddot, "h_ddot")
    sep = as_float64(separation, "separation")
    if sep.shape != (3,):
        raise ValueError(f"separation must have shape (3,), got {sep.shape}")

    result: NDArray[np.float64] = 0.5 * np.einsum("ij,j->i", h, sep)
    return result


__all__ = ["deviation_acceleration"]
