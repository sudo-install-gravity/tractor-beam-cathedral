"""Stress-energy conservation auditing.

The mass dipole's second derivative equals the net external force on a system
(``sum_A m_A a_A = dP/dt``, see :mod:`gwtb.source.multipole_rad`). For an
isolated system this vanishes, which is *why* the leading radiative multipole
is the quadrupole rather than the dipole (``docs/PHYSICS.md`` §2). This module
checks that assumption numerically rather than assuming it silently: any
downstream calculation built on a non-conserving source is otherwise
indistinguishable from a physical one until someone notices the numbers are
wrong by ten orders of magnitude (CLAUDE.md rule 2).

This module is deliberately minimal: it reports whether a configuration
conserves momentum. It does **not** stamp results as ``UNPHYSICAL`` — that is
:class:`StampedResult` (T-2.2), a separate, later task. Nothing here should
import or reference it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.validation import as_body_array, as_masses

#: Relative-residual threshold below which a configuration is judged
#: momentum-conserving. Matches the tolerance used by the T-1.10 dipole-
#: cancellation benchmark, which established that a momentum-conserving
#: configuration cancels to machine-roundoff (~1e-16), leaving many orders of
#: margin before this threshold.
_CONSERVING_TOL = 1e-12


@dataclass(frozen=True)
class ConservationReport:
    """Result of auditing a system of point masses for momentum conservation.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.35

    Attributes
    ----------
    net_force
        Shape ``(3,)``, N. ``sum_A m_A a_A``, the mass dipole's second time
        derivative, equal to ``dP/dt`` by eq. (4.35).
    is_conserving
        ``True`` if ``residual`` is below the conserving threshold.
    residual
        Dimensionless. ``|net_force| / (M_total * a_char)``, where
        ``a_char = max_A |a_A|``. Zero for an exactly balanced configuration;
        scales linearly with an imposed imbalance small compared to
        ``a_char`` (the regime in which ``a_char`` itself is not disturbed by
        the imbalance being measured).
    """

    net_force: NDArray[np.float64]
    is_conserving: bool
    residual: float


def audit(masses: ArrayLike, accelerations: ArrayLike) -> ConservationReport:
    """Audit a system of point masses for momentum conservation.

    Computes the net external force ``sum_A m_A a_A`` (the mass dipole's
    second derivative — see :func:`gwtb.source.multipole_rad.
    dipole_second_derivative`, which this duplicates rather than imports, to
    keep this module's only dependency on the validated masses/accelerations
    contract) and reports whether it vanishes relative to the system's
    characteristic force scale.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.35

    Flanagan & Hughes eq. (4.34)-(4.35) identify ``dM_1/dt = P`` (momentum);
    one further time derivative gives ``d^2 M_1/dt^2 = dP/dt``, the net
    external force. For an isolated system, momentum conservation forces this
    to vanish — this function tests that numerically rather than assuming it.

    Parameters
    ----------
    masses
        Shape ``(N,)``, kg.
    accelerations
        Shape ``(N, 3)``, m/s^2.

    Returns
    -------
    ConservationReport
        See class docstring. Not stamped; see module docstring.
    """
    m = as_masses(masses)
    a = as_body_array(accelerations, "accelerations", n_bodies=m.size)

    net_force: NDArray[np.float64] = np.einsum("a,ai->i", m, a)

    m_total = float(np.sum(m))
    a_char = float(np.max(np.linalg.norm(a, axis=1)))
    scale = m_total * a_char

    if scale > 0.0:
        residual = float(np.linalg.norm(net_force) / scale)
    else:
        # a_char == 0: every body is unaccelerated, so the system trivially
        # conserves momentum regardless of net_force's (necessarily zero)
        # floating-point noise.
        residual = 0.0

    return ConservationReport(
        net_force=net_force,
        is_conserving=bool(residual < _CONSERVING_TOL),
        residual=residual,
    )


__all__ = ["ConservationReport", "audit"]
