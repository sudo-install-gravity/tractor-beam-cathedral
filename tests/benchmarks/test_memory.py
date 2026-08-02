"""Benchmark: linear memory against the independent quadrupole route (T-3.7),
and against hyperbolic two-body scattering (T-3.9).

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

T-3.9 is a genuinely different cross-check: a real two-body **hyperbolic
scattering** encounter, integrated numerically (``scipy.integrate.solve_ivp``)
from a finite launch radius, compared against the closed-form asymptotic
velocities of classical Kepler hyperbolic-orbit theory. This is elementary
Newtonian celestial mechanics — not GW physics, no citation required — and is
the source of the AC's looser ``rtol 1e-4`` (dominated by the numerical
integration and the finite-launch-radius approximation, not by algebra).
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from gwtb.bodies.sphere import Sphere
from gwtb.core.constants import AU, G
from gwtb.kinematics.profiles import QuinticProfile
from gwtb.source.memory import linear_memory
from gwtb.source.quadrupole import waveform_from_profile
from tests.benchmarks.helpers import assert_relative

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


# --- T-3.9: hyperbolic two-body scattering ---------------------------------


def _kepler_asymptotic_velocities(
    m1: float, m2: float, b: float, v_inf: float
) -> tuple[np.ndarray, np.ndarray]:
    """Closed-form incoming/outgoing per-body velocities for a Newtonian
    hyperbolic two-body encounter.

    Elementary celestial mechanics (not GW physics; no citation applies). In
    the conservative 1/r two-body problem, energy conservation forces the
    relative speed at r -> infinity to be identical on the incoming and
    outgoing asymptotes; only the direction rotates, by the deflection angle

    .. code-block:: text

        mu    = G (m1 + m2)
        e     = sqrt(1 + (b v_inf^2 / mu)^2)
        theta = 2 asin(1/e)

    (the hyperbolic-orbit analogue of Rutherford scattering). Individual
    velocities follow from the reduced two-body relation
    ``v_1 = -(m2/M) v_rel``, ``v_2 = (m1/M) v_rel``.

    Returns
    -------
    tuple of ndarray
        ``(v_initial, v_final)``, each shape ``(2, 3)`` — per-body velocities
        long before and long after the encounter.
    """
    mu = G * (m1 + m2)
    total = m1 + m2
    e = math.sqrt(1.0 + (b * v_inf**2 / mu) ** 2)
    theta = 2.0 * math.asin(1.0 / e)

    # Geometry below launches from y = +b with v0 along +x, so the initial
    # angular momentum L_z = x0*0 - b*v_inf = -b*v_inf is NEGATIVE: for an
    # attractive central force this is a clockwise (L_z < 0) trajectory, so
    # the outgoing direction rotates by -theta, not +theta.
    v_rel_in = v_inf * np.array([1.0, 0.0, 0.0])
    v_rel_out = v_inf * np.array([math.cos(theta), -math.sin(theta), 0.0])

    v_initial = np.array([-(m2 / total) * v_rel_in, (m1 / total) * v_rel_in])
    v_final = np.array([-(m2 / total) * v_rel_out, (m1 / total) * v_rel_out])
    return v_initial, v_final


def _integrate_encounter(
    m1: float, m2: float, b: float, v_inf: float, r0: float, t_total: float
) -> tuple[np.ndarray, float]:
    """Numerically integrate the full two-body Newtonian trajectory.

    Launched from finite separation ``r0`` along the incoming asymptote
    direction, with velocity set to the asymptotic ``v_inf`` exactly. The
    initial angular momentum ``|r0_vec x v0|`` equals ``b v_inf`` exactly
    regardless of ``r0`` (the y-offset ``b`` and purely-x velocity make this
    exact by construction); only the initial *energy* carries an
    ``O(mu / (r0 v_inf^2))`` deficit relative to the true asymptotic value,
    which is why ``r0`` is chosen large compared to ``mu / v_inf^2``.

    Returns
    -------
    tuple
        ``(v_final, r_final)`` — per-body velocities at ``t_total`` (shape
        ``(2, 3)``) and the final separation, m (a sanity check that the
        integration ran long enough to exit back to large separation).
    """
    total = m1 + m2
    x0 = -math.sqrt(r0**2 - b**2)
    r_rel0 = np.array([x0, b, 0.0])
    v_rel0 = np.array([v_inf, 0.0, 0.0])

    x1_0 = -(m2 / total) * r_rel0
    x2_0 = (m1 / total) * r_rel0
    v1_0 = -(m2 / total) * v_rel0
    v2_0 = (m1 / total) * v_rel0
    y0 = np.concatenate([x1_0, x2_0, v1_0, v2_0])

    def rhs(_t: float, y: np.ndarray) -> np.ndarray:
        x1, x2, v1, v2 = y[0:3], y[3:6], y[6:9], y[9:12]
        r_vec = x2 - x1
        d = np.linalg.norm(r_vec)
        a1 = G * m2 * r_vec / d**3
        a2 = -G * m1 * r_vec / d**3
        return np.concatenate([v1, v2, a1, a2])

    sol = solve_ivp(rhs, (0.0, t_total), y0, rtol=1e-12, atol=1e-12)
    yf = sol.y[:, -1]
    x1_f, x2_f, v1_f, v2_f = yf[0:3], yf[3:6], yf[6:9], yf[9:12]
    return np.array([v1_f, v2_f]), float(np.linalg.norm(x2_f - x1_f))


def test_memory_offset_matches_analytic_hyperbolic_scattering() -> None:
    """AC: offset matches the analytic result to rtol 1e-4.

    Parameters are chosen so the natural length scale of the encounter,
    ``mu/v_inf^2 ~ 0.13 m``, is ~7 orders of magnitude below the launch radius
    ``r0 = 1e6 m``: the finite-r0 approximation error is ~1e-7, far inside the
    1e-4 budget, so the budget is dominated by the encounter's own numerics
    rather than by the launch-radius approximation.
    """
    m1 = m2 = 1.0e15  # kg
    b = 1.0  # m, impact parameter
    v_inf = 1.0e3  # m/s
    r0 = 1.0e6  # m, launch radius
    t_total = 2200.0  # s, ample for a round trip at v_inf over ~2*r0

    masses = np.array([m1, m2])
    v_initial, v_final_analytic = _kepler_asymptotic_velocities(m1, m2, b, v_inf)
    v_final_numeric, r_final = _integrate_encounter(m1, m2, b, v_inf, r0, t_total)

    assert r_final > 0.9 * r0, "integration did not run long enough to exit the encounter"

    h_analytic = linear_memory(masses, v_initial, v_final_analytic, _R, _N_HAT)
    h_numeric = linear_memory(masses, v_initial, v_final_numeric, _R, _N_HAT)

    scale = np.max(np.abs(h_analytic))
    assert scale > 0.0, "expected a nonzero memory offset from a genuine deflection"
    rel_error = np.max(np.abs(h_numeric - h_analytic)) / scale
    assert rel_error < 1.0e-4, f"relative error {rel_error:.3e} exceeds 1e-4"


def test_deflection_angle_matches_the_rutherford_like_formula() -> None:
    """Cross-checks the integrator itself against the closed-form angle,
    independent of linear_memory — isolates which half of the pipeline would
    be at fault if the memory comparison above ever failed.
    """
    m1 = m2 = 1.0e15
    b = 1.0
    v_inf = 1.0e3
    mu = G * (m1 + m2)
    e = math.sqrt(1.0 + (b * v_inf**2 / mu) ** 2)
    theta_analytic = 2.0 * math.asin(1.0 / e)

    v_final_numeric, _ = _integrate_encounter(m1, m2, b, v_inf, 1.0e6, 2200.0)
    v_rel_final = v_final_numeric[1] - v_final_numeric[0]
    theta_numeric = -math.atan2(v_rel_final[1], v_rel_final[0])

    assert_relative(theta_numeric, theta_analytic, rtol=1e-4, what="deflection angle")


def test_zero_impact_parameter_limit_gives_a_head_on_reversal() -> None:
    """b -> 0 gives theta -> pi (a head-on bounce): e -> 1, asin(1) = pi/2."""
    m1 = m2 = 1.0e15
    mu = G * (m1 + m2)
    v_inf = 1.0e3
    e = math.sqrt(1.0 + (1.0e-9 * v_inf**2 / mu) ** 2)  # b essentially zero
    theta = 2.0 * math.asin(1.0 / e)
    assert theta == pytest.approx(math.pi, rel=1e-6)
