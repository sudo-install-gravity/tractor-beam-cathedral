"""Unit tests for gwtb.bodies.multipole (T-1.3, T-1.4, T-1.5, T-4.5)."""

from __future__ import annotations

import itertools
import math

import numpy as np
import pytest
from scipy.special import sici

from gwtb.bodies.multipole import (
    finite_size_correction,
    octupole_moment,
    quadrupole_moment,
    quadrupole_second_derivative,
    quadrupole_third_derivative,
)
from gwtb.bodies.sphere import Sphere
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


# --- T-2.5 -------------------------------------------------------------------


def test_octupole_moment_is_fully_symmetric() -> None:
    rng = np.random.default_rng(5)
    masses, positions = _random_bodies(rng)
    Q = octupole_moment(masses, positions)
    scale = np.max(np.abs(Q))
    np.testing.assert_allclose(Q, np.transpose(Q, (1, 0, 2)), atol=1e-12 * scale)
    np.testing.assert_allclose(Q, np.transpose(Q, (0, 2, 1)), atol=1e-12 * scale)
    np.testing.assert_allclose(Q, np.transpose(Q, (2, 1, 0)), atol=1e-12 * scale)
    for perm in itertools.permutations((0, 1, 2)):
        np.testing.assert_allclose(Q, np.transpose(Q, perm), atol=1e-12 * scale)


def test_octupole_moment_is_traceless_on_every_index_pair() -> None:
    rng = np.random.default_rng(6)
    masses, positions = _random_bodies(rng)
    Q = octupole_moment(masses, positions)
    scale = np.max(np.abs(Q))

    trace_ij = np.einsum("iik->k", Q)
    trace_jk = np.einsum("ijj->i", Q)
    trace_ki = np.einsum("iji->j", Q)

    assert np.max(np.abs(trace_ij)) <= 1e-12 * scale
    assert np.max(np.abs(trace_jk)) <= 1e-12 * scale
    assert np.max(np.abs(trace_ki)) <= 1e-12 * scale


def test_octupole_moment_zero_for_symmetric_pair() -> None:
    """Equal masses at +x and -x: an odd-order moment must vanish exactly,
    same reasoning as the dipole (test_multipole_rad.py)."""
    masses = [3.0, 3.0]
    positions = [[2.0, 0.0, 0.0], [-2.0, 0.0, 0.0]]
    Q = octupole_moment(masses, positions)
    np.testing.assert_allclose(Q, np.zeros((3, 3, 3)), atol=1e-12)


def test_octupole_moment_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError):
        octupole_moment([1.0, 2.0, 3.0], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


def test_octupole_moment_rejects_float32() -> None:
    masses = np.array([1.0, 2.0], dtype=np.float32)
    positions = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float64)
    with pytest.raises(TypeError):
        octupole_moment(masses, positions)

    masses64 = np.array([1.0, 2.0], dtype=np.float64)
    positions32 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    with pytest.raises(TypeError):
        octupole_moment(masses64, positions32)


def test_octupole_moment_is_float64_and_correct_shape() -> None:
    rng = np.random.default_rng(7)
    masses, positions = _random_bodies(rng)
    Q = octupole_moment(masses, positions)
    assert Q.dtype == np.float64
    assert Q.shape == (3, 3, 3)


# =============================================================================
# T-4.5 / ADR-0007 — finite-size retardation correction
# =============================================================================


def _sphere_at(r_over_lambda: float, wavelength: float = 1.0) -> tuple[Sphere, float]:
    return Sphere(radius=r_over_lambda * wavelength, density=1.0), wavelength


def _f2_closed_form(x: float) -> float:
    """ADR-0007 eq. 4: the exact l=2 uniform-ball form factor, 75(3Si+xcos-4sin)/x^5.

    Independent of the implementation's truncated series. Cancellation-limited
    below x ~ 0.05 (see ADR-0007), so callers must stay above that.
    """
    si, _ = sici(x)
    return float(75.0 * (3.0 * si + x * math.cos(x) - 4.0 * math.sin(x)) / x**5)


def test_finite_size_correction_coefficient_is_exactly_5_over_98() -> None:
    """The exact-coefficient pin — the single strongest assertion in this file.

    Everything else about the function is qualitative (tends to 1, decreases,
    depends only on R/lambda) and is satisfied by all three *wrong* form
    factors too. This line is what actually distinguishes them, so it gets its
    own name rather than living inside a guard test where a reader would not
    look for it.

    **The loop stops at R/lambda = 0.03 deliberately.** ``1.0 - implemented``
    is a difference against 1.0, so its absolute error is float64's spacing
    there (~2.2e-16) regardless of how small the departure is. Supporting
    ``rel=1e-12`` needs a departure above ~2.2e-4, i.e. R/lambda >~ 0.011.
    Extending this loop downwards measures float64, not the formula — the
    point-mass limit is covered by the monotone test below instead.
    """
    for r_over_lambda in (0.5, 0.3, 0.2, 0.1, 0.05, 0.03):
        k_r = 2.0 * math.pi * r_over_lambda
        implemented = finite_size_correction(*_sphere_at(r_over_lambda))
        assert (1.0 - implemented) / k_r**2 == pytest.approx(5.0 / 98.0, rel=1e-12)


def test_finite_size_correction_tends_to_unity_in_the_point_mass_limit() -> None:
    """The headline AC: F -> 1 as R/lambda -> 0.

    **This test does not constrain the coefficient.** It passes unchanged for
    1/6, 1/10, 1/14 and a 0.1% nudge — only the sign flip fails it. That is
    intentional (it checks the qualitative acceptance criterion), but do not
    read a pass here as evidence the formula is right; see
    :func:`test_finite_size_correction_coefficient_is_exactly_5_over_98`.
    """
    previous = 0.0
    for r_over_lambda in (1e-2, 1e-3, 1e-4, 1e-5, 1e-6):
        f = finite_size_correction(*_sphere_at(r_over_lambda))
        assert f < 1.0, "a finite body must radiate less than the point-mass limit"
        assert f > previous, "F must increase monotonically towards 1 as R/lambda falls"
        previous = f
    assert finite_size_correction(*_sphere_at(1e-8)) == pytest.approx(1.0, abs=1e-13)


def test_finite_size_correction_departure_at_the_regime_boundary() -> None:
    """The *corrected* AC (ADR-0007 "Recomputed acceptance criterion").

    T-4.5's original criterion said "departs from unity by >1% when R/lambda >
    0.1". That was written against the wrong form factor. The true departure
    there is 2.0142%, so assert the actual value — ">1%" is satisfied by a
    formula that is wrong by a factor of two.
    """
    f = finite_size_correction(*_sphere_at(0.1))
    departure = 1.0 - f
    assert departure == pytest.approx(0.020142049798141547, rel=1e-12)
    assert departure > 0.01  # the original AC, now a weak corollary

    # The 1% point is at R/lambda = 0.070460897, not 0.1.
    one_percent = finite_size_correction(*_sphere_at(0.070460897))
    assert 1.0 - one_percent == pytest.approx(0.01, rel=1e-7)


def test_finite_size_correction_matches_the_exact_closed_form() -> None:
    """Eq. 3 (implemented) against eq. 4 (exact), inside eq. 4's valid window.

    The difference must be exactly the discarded tail of the series,
    ``-5(kR)^4/4536 + 5(kR)^6/365904``. Asserting *that* rather than a flat
    tolerance is what makes the test sensitive to the (kR)^2 coefficient: a
    formula with 1/6 or 1/10 in place of 5/98 misses by ~1e-2, four orders
    above this tolerance.

    **The window is bounded below on purpose.** Eq. 4 is a difference of O(x)
    terms yielding O(x^5) and is cancellation-limited below kR ~ 0.05
    (ADR-0007): at R/lambda = 0.005 the measured difference is 28x the true
    truncation, which is the closed form's floating-point noise, not physics.
    Do not extend this loop downwards.
    """
    for r_over_lambda in (0.03, 0.05, 0.08, 0.1, 0.15):
        k_r = 2.0 * math.pi * r_over_lambda
        implemented = finite_size_correction(*_sphere_at(r_over_lambda))
        exact = _f2_closed_form(k_r)
        discarded_tail = -5.0 * k_r**4 / 4536.0 + 5.0 * k_r**6 / 365904.0
        assert implemented - exact == pytest.approx(discarded_tail, rel=1e-3)


def test_closed_form_reference_would_reject_the_wrong_coefficients() -> None:
    """The previous test is not vacuous: pin how badly a wrong 5/98 would miss.

    Without this, a reader cannot tell whether ``rel=1e-3`` above is a tight
    constraint or a rubber stamp.
    """
    k_r = 2.0 * math.pi * 0.1
    exact = _f2_closed_form(k_r)
    for wrong_coeff in (1.0 / 6.0, 1.0 / 10.0, 1.0 / 14.0):
        wrong = 1.0 - wrong_coeff * k_r**2
        assert abs(wrong - exact) > 1e-3, "a wrong coefficient must miss by >1e-3"
    correct = 1.0 - (5.0 / 98.0) * k_r**2
    assert abs(correct - exact) < 2e-4


def test_finite_size_correction_is_independent_of_density() -> None:
    """Only the radius enters — the form factor is geometric, not inertial."""
    values = {
        finite_size_correction(Sphere(radius=0.05, density=rho), 1.0)
        for rho in (1.0, 1e3, 7.8e3, 2.2e4)
    }
    assert len(values) == 1


def test_finite_size_correction_scales_with_radius_over_wavelength_only() -> None:
    """F depends on (R, lambda) solely through their ratio."""
    reference = finite_size_correction(Sphere(radius=0.03, density=1.0), 1.0)
    for scale in (1e-6, 1e3, 1e9):
        scaled = finite_size_correction(Sphere(radius=0.03 * scale, density=1.0), scale)
        assert scaled == pytest.approx(reference, rel=1e-14)


@pytest.mark.parametrize("wavelength", [0.0, -1.0, math.inf, math.nan])
def test_finite_size_correction_rejects_bad_wavelength(wavelength: float) -> None:
    with pytest.raises(ValueError):
        finite_size_correction(Sphere(radius=1.0, density=1.0), wavelength)


# --- ADR-0007 regression guards: the two wrong-multipole-order form factors ---
#
# Both are smooth, both tend to 1 as R/lambda -> 0, and both would satisfy the
# original ">1% departure" acceptance criterion. Only the (kR)^2 coefficient
# tells them apart, so each is pinned here BY NAME. CLAUDE.md rule 4 makes this
# the project's highest-risk bug class.


def test_finite_size_correction_is_not_the_spin1_sinc_form_factor() -> None:
    """Guard: sin(kR)/(kR), leading term 1 - (kR)^2/6, is l=0 ANTENNA machinery.

    This is precisely the borrowed-from-antennas trap of CLAUDE.md rule 4. If a
    future change makes this test fail, the change is wrong — not the test.
    """
    r_over_lambda = 0.1
    k_r = 2.0 * math.pi * r_over_lambda
    implemented = finite_size_correction(*_sphere_at(r_over_lambda))

    sinc_l0 = math.sin(k_r) / k_r
    assert implemented != pytest.approx(sinc_l0, rel=1e-3)
    # and specifically: our coefficient is 5/98, not 1/6. The positive form of
    # this assertion lives in test_..._coefficient_is_exactly_5_over_98.
    assert (1.0 - implemented) / k_r**2 != pytest.approx(1.0 / 6.0, rel=1e-2)


def test_finite_size_correction_is_not_the_monopole_form_factor() -> None:
    """Guard: 3 j_1(kR)/(kR), leading term 1 - (kR)^2/10, is the TOTAL-MASS monopole.

    It is the correct Fourier transform of a uniform sphere's density — just of
    the wrong multipole. Being "the right answer to a different question" is
    what makes it dangerous.
    """
    r_over_lambda = 0.1
    k_r = 2.0 * math.pi * r_over_lambda
    implemented = finite_size_correction(*_sphere_at(r_over_lambda))

    j1 = math.sin(k_r) / k_r**2 - math.cos(k_r) / k_r
    monopole_l0 = 3.0 * j1 / k_r
    assert implemented != pytest.approx(monopole_l0, rel=1e-3)
    assert (1.0 - implemented) / k_r**2 != pytest.approx(1.0 / 10.0, rel=1e-2)


def test_finite_size_correction_is_not_the_surface_profile_form_factor() -> None:
    """Guard: 1 - (kR)^2/14 is the SURFACE-deformation profile (ADR-0007 eq. 5).

    A tidally or rotationally deformed incompressible body has its l=2 mass
    concentrated at r = R, giving a coefficient 40% larger. This function is the
    volume-filling case. The two are not interchangeable, and a source quoting
    1/14 is not a confirmation of this one.
    """
    r_over_lambda = 0.1
    k_r = 2.0 * math.pi * r_over_lambda
    implemented = finite_size_correction(*_sphere_at(r_over_lambda))
    assert (1.0 - implemented) / k_r**2 != pytest.approx(1.0 / 14.0, rel=1e-2)
    assert (1.0 / 14.0) / (5.0 / 98.0) == pytest.approx(1.4, rel=1e-12)


def test_finite_size_correction_validity_floor_is_recorded() -> None:
    """The truncated series goes negative at kR = sqrt(98/5) — a wall, not a bug.

    T-4.7 adds the structured out-of-regime warning; this pins where the leading
    -order form actually breaks so that nobody "fixes" the sign later.
    """
    zero_crossing = math.sqrt(98.0 / 5.0) / (2.0 * math.pi)
    assert zero_crossing == pytest.approx(0.70460896946282, rel=1e-12)
    assert finite_size_correction(*_sphere_at(zero_crossing)) == pytest.approx(0.0, abs=1e-12)
    assert finite_size_correction(*_sphere_at(0.9)) < 0.0
