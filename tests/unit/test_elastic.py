"""Unit tests for gwtb.bodies.elastic (T-4.3).

The acceptance criterion that matters most is the last one: **R and rho now
enter independently**. T-4.2 asserted the opposite for the rigid model — two
spheres of equal mass but different (R, rho) radiate identically — and this
module is what breaks that degeneracy. The test below is written as a direct
contrast against T-4.2's, so the two cannot silently drift apart.
"""

from __future__ import annotations

import math
from itertools import pairwise

import numpy as np
import pytest

from gwtb.bodies.elastic import induced_quadrupole, love_number_k2
from gwtb.bodies.sphere import Sphere

#: A representative tidal tensor, s^-2. Trace-free already.
_TIDAL = np.array(
    [
        [1.0e-12, 3.0e-13, 0.0],
        [3.0e-13, -4.0e-13, 2.0e-13],
        [0.0, 2.0e-13, -6.0e-13],
    ]
)

#: Steel-like: rigidity ~80 GPa, density 7800 kg/m^3.
_STEEL_RIGIDITY = 8.0e10


def _steel(radius: float = 10.0) -> Sphere:
    return Sphere(radius=radius, density=7800.0)


# --- AC: scales linearly with the applied field ---------------------------


def test_scales_linearly_with_tidal_field() -> None:
    body = _steel()
    single = induced_quadrupole(body, _TIDAL, rigidity=_STEEL_RIGIDITY)
    double = induced_quadrupole(body, 2.0 * _TIDAL, rigidity=_STEEL_RIGIDITY)
    np.testing.assert_allclose(double, 2.0 * single, rtol=1e-14)


def test_zero_field_gives_zero_quadrupole() -> None:
    q = induced_quadrupole(_steel(), np.zeros((3, 3)), rigidity=_STEEL_RIGIDITY)
    np.testing.assert_array_equal(q, np.zeros((3, 3)))


def test_superposes_linearly() -> None:
    body = _steel()
    other = np.diag([2.0e-13, -1.0e-13, -1.0e-13])
    combined = induced_quadrupole(body, _TIDAL + other, rigidity=_STEEL_RIGIDITY)
    separate = induced_quadrupole(body, _TIDAL, rigidity=_STEEL_RIGIDITY) + induced_quadrupole(
        body, other, rigidity=_STEEL_RIGIDITY
    )
    np.testing.assert_allclose(combined, separate, rtol=1e-13)


# --- AC: tends to zero as rigidity -> infinity ----------------------------


def test_tends_to_zero_as_rigidity_grows() -> None:
    body = _steel()
    magnitudes = [
        np.max(np.abs(induced_quadrupole(body, _TIDAL, rigidity=mu)))
        for mu in (1.0e6, 1.0e9, 1.0e12, 1.0e15)
    ]
    assert all(a > b for a, b in pairwise(magnitudes))
    assert magnitudes[-1] < magnitudes[0] * 1e-6


def test_infinite_rigidity_limit_recovers_the_rigid_model() -> None:
    """The bridge back to T-4.2: a perfectly rigid sphere has no induced moment."""
    body = _steel()
    q = induced_quadrupole(body, _TIDAL, rigidity=1.0e30)
    np.testing.assert_allclose(q, np.zeros((3, 3)), atol=1e-6)


def test_zero_rigidity_gives_the_fluid_love_number() -> None:
    assert love_number_k2(_steel(), rigidity=0.0) == pytest.approx(1.5)


def test_love_number_decreases_monotonically_with_rigidity() -> None:
    body = _steel()
    values = [love_number_k2(body, mu) for mu in (0.0, 1.0e6, 1.0e9, 1.0e12)]
    assert all(a > b for a, b in pairwise(values))
    assert all(0.0 < v <= 1.5 for v in values)


def test_love_number_matches_the_closed_form() -> None:
    """Recompute eq. 8-9 independently of the implementation."""
    body = Sphere(radius=500.0, density=3000.0)
    mu = 1.0e10
    g = 6.67430e-11 * body.mass / body.radius**2
    mu_tilde = 19.0 * mu / (2.0 * body.density * g * body.radius)
    assert love_number_k2(body, mu) == pytest.approx(1.5 / (1.0 + mu_tilde), rel=1e-12)


# --- AC: R and rho now enter independently (contrast with T-4.2) ---------


def test_equal_mass_spheres_now_radiate_differently() -> None:
    """The headline result: the T-4.2 degeneracy is broken.

    T-4.2 asserts that in the rigid model two spheres with equal M but
    different (R, rho) produce **identical** radiation. Here they must not:
    the induced quadrupole carries R^5 explicitly and rho through the Love
    number, so equal mass is no longer sufficient to fix the response.
    """
    compact = Sphere(radius=10.0, density=7800.0)
    # Same mass, twice the radius => density down by 2^3.
    diffuse = Sphere(radius=20.0, density=7800.0 / 8.0)
    assert compact.mass == pytest.approx(diffuse.mass, rel=1e-12)

    q_compact = induced_quadrupole(compact, _TIDAL, rigidity=_STEEL_RIGIDITY)
    q_diffuse = induced_quadrupole(diffuse, _TIDAL, rigidity=_STEEL_RIGIDITY)

    # atol=0 is load-bearing. These quadrupoles are ~1e-9, and np.allclose's
    # default atol=1e-8 would call a factor-of-two difference "close" —
    # exactly the scale-dependence trap recorded in docs/HANDOVER.md §5.
    assert not np.allclose(q_compact, q_diffuse, rtol=1e-3, atol=0.0)
    ratio = np.max(np.abs(q_diffuse)) / np.max(np.abs(q_compact))
    assert ratio == pytest.approx(2.0, rel=1e-6)
    # And the rigid model's self-quadrupole remains zero for both, so the
    # difference comes entirely from elasticity.
    np.testing.assert_array_equal(compact.self_quadrupole(), diffuse.self_quadrupole())


def test_radius_dependence_is_fifth_power_at_fixed_love_number() -> None:
    """With k_2 held fixed, Q scales as R^5 exactly (Hinderer eq. 4-5)."""
    small = induced_quadrupole(Sphere(1.0, 3000.0), _TIDAL, love_k2=0.3)
    large = induced_quadrupole(Sphere(2.0, 3000.0), _TIDAL, love_k2=0.3)
    np.testing.assert_allclose(large, 32.0 * small, rtol=1e-13)


def test_density_changes_the_response_at_fixed_radius() -> None:
    """rho enters through self-gravity in mu_tilde, independently of R."""
    light = induced_quadrupole(Sphere(100.0, 1000.0), _TIDAL, rigidity=_STEEL_RIGIDITY)
    heavy = induced_quadrupole(Sphere(100.0, 8000.0), _TIDAL, rigidity=_STEEL_RIGIDITY)
    assert not np.allclose(light, heavy, rtol=1e-3, atol=0.0)


# --- tensor structure ------------------------------------------------------


def test_result_is_symmetric_and_trace_free() -> None:
    q = induced_quadrupole(_steel(), _TIDAL, rigidity=_STEEL_RIGIDITY)
    np.testing.assert_allclose(q, q.T, rtol=1e-15)
    assert abs(np.trace(q)) < 1e-12 * np.max(np.abs(q))


def test_trace_of_the_input_field_is_ignored() -> None:
    """Only the trace-free part drives an l = 2 response."""
    body = _steel()
    with_trace = _TIDAL + np.eye(3) * 5.0e-13
    a = induced_quadrupole(body, _TIDAL, rigidity=_STEEL_RIGIDITY)
    b = induced_quadrupole(body, with_trace, rigidity=_STEEL_RIGIDITY)
    np.testing.assert_allclose(a, b, rtol=1e-13)


def test_sign_opposes_the_applied_field() -> None:
    """Hinderer eq. 4: Q_ij = -lambda E_ij, with lambda > 0."""
    field = np.diag([1.0e-12, -5.0e-13, -5.0e-13])
    q = induced_quadrupole(_steel(), field, love_k2=1.0)
    assert q[0, 0] < 0.0
    assert q[1, 1] > 0.0


# --- validation ------------------------------------------------------------


def test_requires_exactly_one_of_love_k2_or_rigidity() -> None:
    body = _steel()
    with pytest.raises(ValueError, match="exactly one"):
        induced_quadrupole(body, _TIDAL)
    with pytest.raises(ValueError, match="exactly one"):
        induced_quadrupole(body, _TIDAL, love_k2=1.0, rigidity=1.0e10)


@pytest.mark.parametrize("bad", [-1.0, math.nan, math.inf])
def test_rejects_invalid_rigidity(bad: float) -> None:
    with pytest.raises(ValueError, match="rigidity"):
        love_number_k2(_steel(), bad)


@pytest.mark.parametrize("bad", [-0.5, math.nan, math.inf])
def test_rejects_invalid_love_number(bad: float) -> None:
    with pytest.raises(ValueError, match="love_k2"):
        induced_quadrupole(_steel(), _TIDAL, love_k2=bad)


def test_rejects_wrong_field_shape() -> None:
    with pytest.raises(ValueError, match=r"\(3, 3\)"):
        induced_quadrupole(_steel(), np.zeros(3), rigidity=_STEEL_RIGIDITY)


def test_rejects_float32_field() -> None:
    """ADR-0002 §5: float32 is rejected, not upcast."""
    with pytest.raises(TypeError, match="float32"):
        induced_quadrupole(_steel(), _TIDAL.astype(np.float32), rigidity=_STEEL_RIGIDITY)
