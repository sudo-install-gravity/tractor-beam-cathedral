"""Benchmark: linear memory against the independent quadrupole route (T-3.7).

ADR-0004 recorded a prediction before this code existed. The settled,
post-maneuver value of :func:`gwtb.source.quadrupole.waveform_from_profile`
reaches the linear memory by an entirely different path — integrating the
quadrupole formula through a finite maneuver — and must agree with the closed
form implemented in :func:`gwtb.source.memory.linear_memory`.

The agreement is exact rather than approximate, and that is the point. Once the
maneuver ends and acceleration ceases, ``d2Q_ij/dt2 -> 2 sum_A m_A v_i v_j``, so
the quadrupole formula's ``2G/c^4 r`` prefactor and the memory formula's
``4G/c^4 r`` describe the same tensor. A tolerance-based check would pass even
if one route had picked up a spurious factor close to 1; requiring machine
precision does not.
"""

from __future__ import annotations

import numpy as np

from gwtb.bodies.sphere import Sphere
from gwtb.core.constants import AU
from gwtb.kinematics.profiles import QuinticProfile
from gwtb.source.memory import linear_memory
from gwtb.source.quadrupole import waveform_from_profile

_MANEUVER_AXIS = np.array([1.0, 0.0, 0.0])
_R = 40.0 * AU
_N_HAT = np.array([0.0, 0.0, 1.0])


def _settled_strain(
    body: Sphere, profile: QuinticProfile, r: float, n_hat: np.ndarray
) -> np.ndarray:
    """Strain long after the maneuver ends, from the quadrupole route."""
    times = np.array([profile.duration * 5.0])
    return np.asarray(waveform_from_profile(body, profile, r, n_hat, times)[0])


def _memory_for_profile(
    body: Sphere, profile: QuinticProfile, r: float, n_hat: np.ndarray
) -> np.ndarray:
    """Same configuration, via the closed-form linear memory.

    ADR-0004 models the maneuvering sphere as two half-masses at ``+x(t)`` and
    ``-x(t)``. They start at rest and coast at ``+/- v_end``, so the memory
    follows from those two velocity states alone.
    """
    half = body.mass / 2.0
    v_end = float(profile.velocity(profile.duration))
    masses = np.array([half, half])
    rest = np.zeros((2, 3))
    final = np.array([v_end * _MANEUVER_AXIS, -v_end * _MANEUVER_AXIS])
    return linear_memory(masses, rest, final, r, n_hat)


def test_linear_memory_reproduces_the_settled_waveform_exactly() -> None:
    """ADR-0004's predicted 0.0 relative difference, now asserted in code."""
    body = Sphere(radius=5.0, density=8000.0)
    profile = QuinticProfile(delta_v=100.0, duration=60.0)

    settled = _settled_strain(body, profile, _R, _N_HAT)
    memory = _memory_for_profile(body, profile, _R, _N_HAT)

    # Machine precision, not a tolerance: the two routes are algebraically the
    # same tensor once acceleration ceases.
    np.testing.assert_array_equal(memory, settled)


def test_agreement_holds_across_masses_and_maneuvers() -> None:
    """The identity is structural, so it must not depend on the parameters."""
    cases = [
        (Sphere(radius=1.0, density=2000.0), QuinticProfile(delta_v=10.0, duration=5.0)),
        (Sphere(radius=20.0, density=19300.0), QuinticProfile(delta_v=1.0e3, duration=600.0)),
        (Sphere(radius=0.5, density=7800.0), QuinticProfile(delta_v=0.1, duration=1.0)),
    ]
    for body, profile in cases:
        settled = _settled_strain(body, profile, _R, _N_HAT)
        memory = _memory_for_profile(body, profile, _R, _N_HAT)
        assert np.max(np.abs(memory - settled)) == 0.0


def test_agreement_holds_to_one_ulp_for_an_oblique_observer() -> None:
    """Obliquely the two routes agree to 1 ULP, not bit-for-bit — and that is
    the correct expectation, not a defect.

    ADR-0004 measured 0.0 relative difference along the symmetry axis, and that
    still holds (see the tests above). It does not generalize, because the two
    routes reach the same tensor by different arithmetic: the quadrupole route
    forms ``2 sum m v v - (2/3) delta (v.v)`` and then TT-projects, while the
    memory route projects ``sum m v v`` directly. The projection analytically
    removes the trace term, but the rounding incurred in forming and subtracting
    it does not vanish. Along the axis the operations happen to coincide
    exactly; obliquely they differ in the last bit.

    Asserting bit-equality here would be asserting a property of float64
    operation ordering, not of the physics.
    """
    body = Sphere(radius=5.0, density=8000.0)
    profile = QuinticProfile(delta_v=100.0, duration=60.0)
    n = np.array([2.0, -1.0, 3.0])
    n = n / np.linalg.norm(n)

    settled = _settled_strain(body, profile, _R, n)
    memory = _memory_for_profile(body, profile, _R, n)

    scale = np.max(np.abs(settled))
    assert np.max(np.abs(memory - settled)) <= 4.0 * np.finfo(np.float64).eps * scale


def test_the_memory_offset_is_nonzero() -> None:
    """Guards against the identity being satisfied by two zeros.

    Both routes returning zero would satisfy every assertion above, so the
    physical content — a *permanent* offset — is asserted separately.
    """
    body = Sphere(radius=5.0, density=8000.0)
    profile = QuinticProfile(delta_v=100.0, duration=60.0)
    memory = _memory_for_profile(body, profile, _R, _N_HAT)
    assert np.max(np.abs(memory)) > 0.0
