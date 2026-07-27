"""Mass dipole moment and its second time derivative.

The mass dipole is the system's center of mass. Its second derivative equals
``dP/dt``, the net external force — for an isolated, momentum-conserving
system this vanishes identically, which is why the leading radiative
multipole is the quadrupole rather than the dipole (Blanchet, Living Rev.
Relativ. 17:2 (2014), eq. 3; see ``docs/PHYSICS.md`` §2).

**This module does not compute dipole radiation.** ``dipole_strain`` (T-2.4,
wrapped in a ``StampedResult`` carrying the ``UNPHYSICAL`` provenance stamp)
is a separate, later task; this module supplies only the moment and its
second derivative, which T-2.4 will consume. Do not add a strain function
here.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.validation import as_body_array, as_masses


def dipole_moment(masses: ArrayLike, positions: ArrayLike) -> NDArray[np.float64]:
    """Mass dipole moment ``d_i`` of a system of point masses.

    .. code-block:: text

        d_i = sum_A m_A x_A,i

    For a point-mass distribution ``rho = sum_A m_A delta^3(x - x_A)``, this
    is the ``l=1`` term of the mass multipole expansion — the system's
    center-of-mass position weighted by total mass, ``M * x_cm``.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.30

    Flanagan & Hughes define ``M_1 = integral rho(x) x_i d^3x`` (their eq.
    4.30, ``rho`` being ``T^tt``); substituting the point-mass density gives
    the sum above directly.

    Parameters
    ----------
    masses
        Shape ``(N,)``, kg.
    positions
        Shape ``(N, 3)``, m.

    Returns
    -------
    ndarray
        Shape ``(3,)``, kg m.
    """
    m = as_masses(masses)
    x = as_body_array(positions, "positions", n_bodies=m.size)
    result: NDArray[np.float64] = np.einsum("a,ai->i", m, x)
    return result


def dipole_second_derivative(masses: ArrayLike, accelerations: ArrayLike) -> NDArray[np.float64]:
    """Analytic second time derivative ``d2(d_i)/dt2`` of the mass dipole.

    .. code-block:: text

        d_i_ddot = sum_A m_A a_A,i = dP_i/dt

    Equal to the system's total momentum derivative, i.e. the net external
    force. For an isolated (momentum-conserving) system this is exactly zero
    — that vanishing is *the* reason mass-dipole gravitational radiation does
    not occur, not an incidental fact (``docs/PHYSICS.md`` §2). Do not "fix"
    a nonzero result for a momentum-conserving configuration; a nonzero value
    correctly signals an unbalanced external force, which is what
    :func:`gwtb.source.conservation.audit` exists to flag.

    **Analytic. Never finite-difference** — this is one time-derivative of
    Flanagan & Hughes eq. (4.35), ``dM_1/dt = P``, applied again; no numerical
    differentiation is needed or permitted since the accelerations are already
    given.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.35

    Parameters
    ----------
    masses
        Shape ``(N,)``, kg.
    accelerations
        Shape ``(N, 3)``, m/s^2.

    Returns
    -------
    ndarray
        Shape ``(3,)``, kg m s^-2 (N). Zero to numerical roundoff for a
        momentum-conserving configuration.
    """
    m = as_masses(masses)
    a = as_body_array(accelerations, "accelerations", n_bodies=m.size)
    result: NDArray[np.float64] = np.einsum("a,ai->i", m, a)
    return result


__all__ = ["dipole_moment", "dipole_second_derivative"]
