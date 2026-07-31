"""Linear (ordinary) gravitational-wave memory: the permanent strain offset left
behind after a system's constituent velocities change.

Memory is the part of the waveform that does not return to zero. A detector that
watched a maneuver end up displaced, and stays displaced — the spacetime between
the test masses is permanently, if minutely, altered. For this project it is the
observable signature of a completed maneuver, as distinct from the oscillatory
signal radiated during one.

**This module implements the non-relativistic limit.** Favata's eq. (10k) is the
full Lienard-Wiechert result and carries two relativistic factors per body — the
Lorentz factor ``1/sqrt(1 - v^2/c^2)`` and the beaming factor
``1/(1 - v.N)``. Both tend to 1 as ``v/c -> 0``, and at the velocities this
project models (``v/c ~ 1e-5`` for asteroid deflection) they are corrections at
the 1e-10 level. They are dropped deliberately, not overlooked; see
:func:`linear_memory` for the exact statement of what was dropped.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.constants import G_OVER_C4
from gwtb.core.validation import as_body_array, as_masses, as_unit_vector
from gwtb.propagate.tt_projection import apply_tt


def linear_memory(
    masses: ArrayLike,
    velocities_initial: ArrayLike,
    velocities_final: ArrayLike,
    r: float,
    n_hat: ArrayLike,
) -> NDArray[np.float64]:
    """Permanent TT strain offset from a change in the bodies' velocities.

    .. code-block:: text

        Delta h_ij^TT = (4G / (c^4 r)) * Lambda_ij,kl * Delta[ sum_A M_A v^k v^l ]

    where ``Delta[...]`` is the difference between the final and initial states.
    The strain is permanent: unlike the oscillatory waveform it does not decay
    after the maneuver, because the coasting bodies retain a constant
    ``sum_A M_A v_i v_j`` term in the quadrupole's second derivative.

    Source: Favata, Class. Quantum Grav. 27:084036 (2010), arXiv:1003.3486,
    eq. 10k

    **Exactly what differs from the printed equation.** Favata eq. (10k) reads
    ``Delta h_jk^TT = Delta sum_A [4 M_A / (R sqrt(1 - v_A^2))]
    [v_A^j v_A^k / (1 - v_A.N)]^TT`` in geometrized units. Three differences,
    all deliberate:

    * **Units.** ``4 M_A / R`` becomes ``4 G M_A / (c^4 R)`` in SI (ADR-0002 §4).
    * **Lorentz factor** ``1/sqrt(1 - v_A^2/c^2)`` is dropped — the
      non-relativistic limit.
    * **Beaming factor** ``1/(1 - v_A.N)`` is dropped likewise. Note this one is
      absent from the backlog's statement of the formula as well; it is recorded
      here so a future reader does not mistake this for the full relativistic
      result.

    Favata writes the projection as ``[...]^TT`` rather than with an explicit
    ``Lambda_ij,kl``; the two denote the same operation, applied here by
    :func:`gwtb.propagate.tt_projection.apply_tt`.

    **Cross-check.** For a momentum-conserving system this reproduces the
    settled, post-maneuver value of
    :func:`gwtb.source.quadrupole.waveform_from_profile` to machine precision —
    an independent route through the quadrupole formula, agreeing at 0.0
    relative difference. That agreement is not a coincidence: once acceleration
    ceases, ``d2Q_ij/dt2 -> 2 sum_A m_A v_i v_j``, and the factor of 2 against
    the quadrupole formula's ``2G/c^4 r`` prefactor is precisely the ``4G/c^4 r``
    above. See ADR-0004 and ``tests/benchmarks/test_memory.py``.

    **This function does not check momentum conservation.** Memory computed from
    a velocity change that no reaction balances is the mass-dipole artifact of
    ``CLAUDE.md`` rule 2, not a physical signal. Callers working with such a
    configuration must route the result through
    :class:`gwtb.source.conservation.StampedResult`; :func:`gwtb.source.
    conservation.audit` decides which case applies. Nothing here can tell the
    difference, because the initial and final velocities alone do not say what
    supplied the impulse.

    Parameters
    ----------
    masses
        Shape ``(N,)``, kg.
    velocities_initial
        Shape ``(N, 3)``, m/s. Velocities before the change.
    velocities_final
        Shape ``(N, 3)``, m/s. Velocities after it.
    r
        Distance from source to observer, m. Must be positive.
    n_hat
        Shape ``(3,)`` unit vector from source to observer.

    Returns
    -------
    ndarray
        Shape ``(3, 3)``, dimensionless. Symmetric, traceless, and transverse to
        ``n_hat``. Exactly zero when the velocities are unchanged.
    """
    m = as_masses(masses)
    v_i = as_body_array(velocities_initial, "velocities_initial", n_bodies=m.size)
    v_f = as_body_array(velocities_final, "velocities_final", n_bodies=m.size)
    n = as_unit_vector(n_hat, "n_hat")

    if not np.isscalar(r) and np.asarray(r).ndim != 0:
        raise TypeError("r must be a scalar distance in metres")
    r_val = float(r)
    if not np.isfinite(r_val):
        raise ValueError(f"r must be finite, got {r!r}")
    if r_val <= 0.0:
        raise ValueError(f"r must be positive, got {r_val!r}")

    # Difference the momentum-flux tensors, rather than differencing two
    # separately-projected strains: the TT projection is linear, so the results
    # agree analytically, but taking the difference first keeps the subtraction
    # in the (large) source quantities where it is well-conditioned.
    flux_initial = np.einsum("a,ai,aj->ij", m, v_i, v_i)
    flux_final = np.einsum("a,ai,aj->ij", m, v_f, v_f)
    delta_flux = flux_final - flux_initial

    return (4.0 * G_OVER_C4 / r_val) * apply_tt(delta_flux, n)


__all__ = ["linear_memory"]
