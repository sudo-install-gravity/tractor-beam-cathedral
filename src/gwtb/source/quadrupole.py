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

from gwtb.bodies.multipole import quadrupole_second_derivative
from gwtb.bodies.sphere import Sphere
from gwtb.core.constants import G_OVER_C4, G_OVER_C5
from gwtb.core.validation import as_float64, as_tensor_3x3, as_unit_vector
from gwtb.kinematics.profiles import AccelerationProfile
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


_MANEUVER_AXIS = np.array([1.0, 0.0, 0.0])


def _coasting_kinematics(
    profile: AccelerationProfile, t: NDArray[np.float64]
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Scalar position/velocity/acceleration along the profile's axis for
    ``t`` possibly beyond ``profile.duration``.

    ``AccelerationProfile`` is defined only on ``[0, duration]``
    (``_validate_domain``); its own docstring names this function as the
    intended caller needing "coasting" behavior past that point. For
    ``t > duration`` the body coasts at ``velocity(duration)`` with zero
    acceleration, starting from ``position(duration)``.
    """
    duration = profile.duration
    clamped = np.minimum(t, duration)
    x_end = float(profile.position(duration))
    v_end = float(profile.velocity(duration))

    x = np.asarray(profile.position(clamped), dtype=np.float64)
    v = np.asarray(profile.velocity(clamped), dtype=np.float64)
    a = np.asarray(profile.acceleration(clamped), dtype=np.float64)

    coasting = t > duration
    if np.any(coasting):
        x = np.where(coasting, x_end + v_end * (t - duration), x)
        v = np.where(coasting, v_end, v)
        a = np.where(coasting, 0.0, a)
    return x, v, a


def waveform_from_profile(
    body: Sphere,
    profile: AccelerationProfile,
    r: float,
    n_hat: ArrayLike,
    times: ArrayLike,
) -> NDArray[np.float64]:
    """Strain waveform radiated by a sphere executing a finite maneuver.

    **Modeling decision (this function's own, not an external citation):** a
    single accelerating point mass is not an isolated, momentum-conserving
    source (CLAUDE.md rule 2) — its mass dipole does not cancel. Rather than
    silently accept that artifact, this function models the maneuvering
    sphere as one half of a symmetric two-body system: two point masses of
    ``body.mass / 2`` at ``+x(t)`` and ``-x(t)`` along a fixed axis
    (``_MANEUVER_AXIS``, the x-axis), where ``x(t)`` is the profile's scalar
    position. The configuration is momentum-conserving by construction (the
    center of mass never moves), so its quadrupole is a physical radiating
    source with no hidden dipole term.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 3 (quadrupole
    second derivative, via :func:`gwtb.bodies.multipole.
    quadrupole_second_derivative`, applied to the symmetric two-body
    construction above)

    Parameters
    ----------
    body
        Supplies the total mass (radius/density otherwise unused: the rigid
        long-wavelength model, per T-4.2, radiates only through mass and
        trajectory).
    profile
        The single-axis maneuver, evaluated with post-maneuver coasting for
        ``times`` beyond ``profile.duration``.
    r
        Observer distance, m.
    n_hat
        Shape ``(3,)`` unit vector from source to observer.
    times
        Shape ``(T,)``, s. May extend beyond ``profile.duration``.

    Returns
    -------
    ndarray
        Shape ``(T, 3, 3)``, dimensionless strain at each requested time.
        After the maneuver ends, the strain settles to the memory offset
        (rather than zero), since the coasting configuration still has a
        nonzero, constant quadrupole second derivative contribution from
        each body's fixed final velocity — see T-3.8's acceptance test.
    """
    t = as_float64(times, "times")
    if t.ndim != 1:
        raise ValueError(f"times must have shape (T,), got {t.shape}")
    n = as_unit_vector(n_hat, "n_hat")
    if not np.isfinite(r) or r <= 0.0:
        raise ValueError(f"r must be positive and finite, got {r!r}")

    x, v, a = _coasting_kinematics(profile, t)

    half_mass = body.mass / 2.0
    masses = np.array([half_mass, half_mass])

    result = np.empty((t.size, 3, 3), dtype=np.float64)
    for i in range(t.size):
        positions = np.array([x[i] * _MANEUVER_AXIS, -x[i] * _MANEUVER_AXIS])
        velocities = np.array([v[i] * _MANEUVER_AXIS, -v[i] * _MANEUVER_AXIS])
        accelerations = np.array([a[i] * _MANEUVER_AXIS, -a[i] * _MANEUVER_AXIS])
        q_ddot = quadrupole_second_derivative(masses, positions, velocities, accelerations)
        result[i] = strain_tt(q_ddot, r, n)
    return result


__all__ = ["luminosity", "strain_tt", "waveform_from_profile"]
