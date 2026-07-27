"""Unit tests for gwtb.bodies.sphere (T-4.1, T-4.2, T-4.6)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from gwtb.bodies.sphere import Sphere, oblateness_quadrupole
from gwtb.core.constants import G


def test_mass_matches_volume_times_density() -> None:
    s = Sphere(radius=2.0, density=5510.0)
    expected = (4.0 / 3.0) * math.pi * 2.0**3 * 5510.0
    assert s.mass == pytest.approx(expected, rel=1e-12)


def test_moment_of_inertia_matches_two_fifths_m_r_squared() -> None:
    s = Sphere(radius=3.0, density=2700.0)
    assert s.moment_of_inertia == pytest.approx((2.0 / 5.0) * s.mass * 3.0**2, rel=1e-12)


@pytest.mark.parametrize("radius,density", [(0.0, 1.0), (-1.0, 1.0), (1.0, 0.0), (1.0, -1.0)])
def test_rejects_non_positive_radius_or_density(radius: float, density: float) -> None:
    with pytest.raises(ValueError):
        Sphere(radius=radius, density=density)


def test_self_quadrupole_is_exactly_zero() -> None:
    rng = np.random.default_rng(0)
    for _ in range(20):
        radius = rng.uniform(0.1, 100.0)
        density = rng.uniform(1.0, 2e4)
        s = Sphere(radius=radius, density=density)
        q = s.self_quadrupole()
        assert q.shape == (3, 3)
        assert np.max(np.abs(q)) <= 1e-15


def test_degeneracy_warning_names_the_assumption() -> None:
    s = Sphere(radius=1.0, density=1.0)
    msg = s.degeneracy_warning()
    assert "degenerate" in msg.lower() or "identical" in msg.lower()
    assert "B-2" in msg or "rigid" in msg.lower()


def test_equal_mass_different_radius_density_radiate_identically() -> None:
    """The surprising result the API must not hide: two spheres with equal
    mass but different (R, rho) are radiatively indistinguishable in the
    rigid model, because self_quadrupole is zero regardless of (R, rho)."""
    m_target = 1.0e15
    density_a = 2000.0
    radius_a = (m_target / ((4.0 / 3.0) * math.pi * density_a)) ** (1.0 / 3.0)
    density_b = 8000.0
    radius_b = (m_target / ((4.0 / 3.0) * math.pi * density_b)) ** (1.0 / 3.0)

    sphere_a = Sphere(radius=radius_a, density=density_a)
    sphere_b = Sphere(radius=radius_b, density=density_b)

    assert sphere_a.mass == pytest.approx(sphere_b.mass, rel=1e-9)
    assert radius_a != pytest.approx(radius_b, rel=1e-3)
    np.testing.assert_array_equal(sphere_a.self_quadrupole(), sphere_b.self_quadrupole())


def test_oblateness_quadrupole_zero_at_zero_spin() -> None:
    s = Sphere(radius=6.371e6, density=5510.0)
    q = oblateness_quadrupole(s, spin_rate=0.0)
    np.testing.assert_array_equal(q, np.zeros((3, 3)))


def test_oblateness_quadrupole_scales_as_spin_squared() -> None:
    s = Sphere(radius=6.371e6, density=5510.0)
    q1 = oblateness_quadrupole(s, spin_rate=1e-4)
    q2 = oblateness_quadrupole(s, spin_rate=2e-4)
    assert q2[2, 2] == pytest.approx(4.0 * q1[2, 2], rel=1e-9)


def test_oblateness_quadrupole_traceless_and_diagonal() -> None:
    s = Sphere(radius=6.371e6, density=5510.0)
    q = oblateness_quadrupole(s, spin_rate=7.292e-5)
    assert np.trace(q) == pytest.approx(0.0, abs=1e-30)
    off_diag = q.copy()
    np.fill_diagonal(off_diag, 0.0)
    np.testing.assert_array_equal(off_diag, np.zeros((3, 3)))


def test_oblateness_quadrupole_matches_maclaurin_flattening_relation() -> None:
    """Cross-check Q_zz against the flattening formula epsilon = (5/4)*m
    (Fitzpatrick eq. 2.130) via the independent moment-of-inertia route,
    rather than re-deriving the same closed form."""
    s = Sphere(radius=6.371e6, density=5510.0)
    omega = 1.0e-5  # small enough that the leading-order epsilon expansion converges
    m_param = omega**2 * s.radius**3 / (G * s.mass)
    epsilon = 1.25 * m_param
    a = s.radius
    c = a * (1.0 - epsilon)
    i_zz = (2.0 / 5.0) * s.mass * a**2
    i_xx = (1.0 / 5.0) * s.mass * (a**2 + c**2)
    q_zz_expected = -(2.0 / 3.0) * (i_zz - i_xx)

    q = oblateness_quadrupole(s, spin_rate=omega)
    assert q[2, 2] == pytest.approx(q_zz_expected, rel=1e-3)
