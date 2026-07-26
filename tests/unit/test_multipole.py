"""Unit tests for gwtb.bodies.multipole (T-1.3, T-1.4, T-1.5)."""

from __future__ import annotations

import itertools
import math

import numpy as np
import pytest

from gwtb.bodies.multipole import (
    quadrupole_moment,
    quadrupole_second_derivative,
    quadrupole_third_derivative,
)
from tests.benchmarks.helpers import binary_si, circular_binary


def _random_bodies(rng: np.random.Generator, n: int = 6) -> tuple[np.ndarray, np.ndarray]:
    masses = rng.uniform(1.0, 10.0, size=n)
    positions = rng.uniform(-5.0, 5.0, size=(n, 3))
    return masses, positions


def _signed_permutations(vec: tuple[float, float, float]) -> set[tuple[float, float, float]]:
    """All points reachable from ``vec`` by permuting axes and flipping signs.

    The orbit of a point under the full hyperoctahedral (signed-permutation)
    group. A mass distribution invariant under this group has an isotropic
    second moment: axis-permutation invariance forces the diagonal entries
    equal, and independent sign-flip invariance forces every off-diagonal
    entry to be its own negative, hence zero. So the trace-free quadrupole of
    such a distribution is exactly zero, not merely small — the residual is
    pure floating-point roundoff.
    """
    pts: set[tuple[float, float, float]] = set()
    for perm in itertools.permutations(vec):
        for signs in itertools.product((1.0, -1.0), repeat=3):
            pts.add(tuple(s * v for s, v in zip(signs, perm, strict=True)))
    return pts


def _cubic_symmetric_shell(radius: float) -> tuple[np.ndarray, np.ndarray]:
    """50 equal-mass points on one sphere, invariant under axis permutation and sign flip.

    Union of four signed-permutation orbits, sized 6 + 8 + 12 + 24 = 50, all
    scaled to lie on the same sphere of the given radius:

    - axis points   (R, 0, 0)-type            -> orbit size 6
    - cube corners  (c, c, c)-type             -> orbit size 8
    - edge points   (e, e, 0)-type             -> orbit size 12
    - generic       (d, f, 0)-type, d != f     -> orbit size 24
    """
    r = radius
    c = r / math.sqrt(3.0)
    e = r / math.sqrt(2.0)
    theta = 0.4  # generic angle: avoids 0, pi/4, pi/2 so d != f and neither is 0
    d, f = r * math.cos(theta), r * math.sin(theta)

    points: set[tuple[float, float, float]] = set()
    points |= _signed_permutations((r, 0.0, 0.0))
    points |= _signed_permutations((c, c, c))
    points |= _signed_permutations((e, e, 0.0))
    points |= _signed_permutations((d, f, 0.0))

    assert len(points) == 50, f"expected 50 distinct points, got {len(points)}"

    positions = np.array(sorted(points), dtype=np.float64)
    masses = np.ones(positions.shape[0], dtype=np.float64)
    return masses, positions


# --- T-1.3 -------------------------------------------------------------------


def test_quadrupole_moment_is_traceless() -> None:
    rng = np.random.default_rng(1)
    masses, positions = _random_bodies(rng)
    Q = quadrupole_moment(masses, positions)
    assert abs(np.trace(Q)) <= 1e-12 * np.max(np.abs(Q))


def test_quadrupole_moment_is_symmetric() -> None:
    rng = np.random.default_rng(2)
    masses, positions = _random_bodies(rng)
    Q = quadrupole_moment(masses, positions)
    np.testing.assert_allclose(Q, Q.T, atol=1e-15)


def test_quadrupole_moment_unit_mass_on_axis() -> None:
    Q = quadrupole_moment([1.0], [[1.0, 0.0, 0.0]])
    expected = np.diag([2.0 / 3.0, -1.0 / 3.0, -1.0 / 3.0])
    np.testing.assert_allclose(Q, expected, rtol=1e-15)


def test_quadrupole_moment_spherical_shell_vanishes() -> None:
    masses, positions = _cubic_symmetric_shell(radius=2.0)
    Q = quadrupole_moment(masses, positions)
    np.testing.assert_allclose(Q, np.zeros((3, 3)), atol=1e-12)


def test_quadrupole_moment_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError):
        quadrupole_moment([1.0, 2.0, 3.0], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


def test_quadrupole_moment_rejects_float32() -> None:
    masses = np.array([1.0, 2.0], dtype=np.float32)
    positions = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float64)
    with pytest.raises(TypeError):
        quadrupole_moment(masses, positions)

    masses64 = np.array([1.0, 2.0], dtype=np.float64)
    positions32 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    with pytest.raises(TypeError):
        quadrupole_moment(masses64, positions32)


# --- T-1.4 -------------------------------------------------------------------


def test_quadrupole_second_derivative_is_traceless_and_symmetric() -> None:
    rng = np.random.default_rng(3)
    n = 6
    masses = rng.uniform(1.0, 10.0, size=n)
    positions = rng.uniform(-5.0, 5.0, size=(n, 3))
    velocities = rng.uniform(-2.0, 2.0, size=(n, 3))
    accelerations = rng.uniform(-1.0, 1.0, size=(n, 3))

    Qdd = quadrupole_second_derivative(masses, positions, velocities, accelerations)
    assert abs(np.trace(Qdd)) <= 1e-12 * np.max(np.abs(Qdd))
    np.testing.assert_allclose(Qdd, Qdd.T, atol=1e-15 * np.max(np.abs(Qdd)))


def test_quadrupole_second_derivative_matches_central_difference_on_binary() -> None:
    """AC: matches a central difference of quadrupole_moment on a circular
    binary to rtol 1e-5 at step h = 1e-3/omega."""
    b = binary_si()
    h = 1e-3 / b.omega

    def Q_at(t: float) -> np.ndarray:
        masses, positions, _, _, _ = circular_binary(b.m1, b.m2, b.a, t)
        return quadrupole_moment(masses, positions)

    numerical = (Q_at(b.t + h) - 2.0 * Q_at(b.t) + Q_at(b.t - h)) / h**2
    analytic = quadrupole_second_derivative(b.masses, b.positions, b.velocities, b.accelerations)
    # For this planar orbit Q_zz(t) = -mu*a^2/3 is analytically CONSTANT (since
    # |x_rel|^2 = a^2 is time-independent), so its true 2nd derivative is
    # exactly zero; both the analytic function and the finite-difference
    # stencil return pure floating-point noise for that entry, at different
    # noise floors. A bare rtol comparison would be comparing two near-zero
    # numbers to each other, so add an atol scaled to the tensor's overall
    # magnitude (as with the tracelessness checks above) to avoid failing on
    # that noise while still catching a genuine relative-scale error in the
    # dominant xx/xy/yy entries.
    atol = 1e-9 * np.max(np.abs(analytic))
    np.testing.assert_allclose(analytic, numerical, rtol=1e-5, atol=atol)


# --- T-1.5 -------------------------------------------------------------------


def test_quadrupole_third_derivative_is_traceless_and_symmetric() -> None:
    rng = np.random.default_rng(4)
    n = 6
    masses = rng.uniform(1.0, 10.0, size=n)
    positions = rng.uniform(-5.0, 5.0, size=(n, 3))
    velocities = rng.uniform(-2.0, 2.0, size=(n, 3))
    accelerations = rng.uniform(-1.0, 1.0, size=(n, 3))
    jerks = rng.uniform(-0.5, 0.5, size=(n, 3))

    Qddd = quadrupole_third_derivative(masses, positions, velocities, accelerations, jerks)
    assert abs(np.trace(Qddd)) <= 1e-12 * np.max(np.abs(Qddd))
    np.testing.assert_allclose(Qddd, Qddd.T, atol=1e-15 * np.max(np.abs(Qddd)))


def test_quadrupole_third_derivative_matches_five_point_stencil_on_binary() -> None:
    """AC: matches the first derivative of quadrupole_second_derivative taken
    with the 5-point central stencil at h = 1e-3/omega, to rtol 1e-5.

    Do NOT build a third-derivative stencil directly on quadrupole_moment —
    per docs/BACKLOG.md T-1.5 that is roundoff-dominated (eps/h^3) and fails
    against correct code even at the "right" step size.
    """
    b = binary_si()
    h = 1e-3 / b.omega

    def Qdd_at(t: float) -> np.ndarray:
        masses, positions, velocities, accelerations, _ = circular_binary(b.m1, b.m2, b.a, t)
        return quadrupole_second_derivative(masses, positions, velocities, accelerations)

    stencil = (
        -Qdd_at(b.t + 2.0 * h)
        + 8.0 * Qdd_at(b.t + h)
        - 8.0 * Qdd_at(b.t - h)
        + Qdd_at(b.t - 2.0 * h)
    ) / (12.0 * h)

    analytic = quadrupole_third_derivative(
        b.masses, b.positions, b.velocities, b.accelerations, b.jerks
    )
    # Same reasoning as the second-derivative test above: Q_zz(t) is
    # analytically constant for this planar orbit, so its true 3rd derivative
    # is exactly zero and both sides are pure noise for that entry.
    atol = 1e-9 * np.max(np.abs(analytic))
    np.testing.assert_allclose(analytic, stencil, rtol=1e-5, atol=atol)
