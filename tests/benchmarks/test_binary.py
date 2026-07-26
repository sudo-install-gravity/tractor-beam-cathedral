"""Benchmarks for the equal-mass circular binary (T-1.0, T-1.9) and the
Flanagan & Hughes (2005) worked-example errata (docs/ERRATA.md).

T-1.0 verifies the fixture itself — ``tests.benchmarks.helpers.circular_binary``
and ``binary_si`` — before anything downstream relies on it: barycentric,
correct analytic derivatives, correct Kepler relation.

T-1.9 then uses the fixture to reproduce the closed-form face-on waveform and
luminosity of an equal-mass circular binary.

Binding conventions (docs/BACKLOG.md T-1.9) — the signs below only reproduce
under these two, so getting either wrong fails with no obvious cause:

1. Phase origin: ``x_rel(t) = (a cos(omega t), a sin(omega t), 0)``, i.e. the
   T-1.0 fixture used unmodified (t=0 at ``x_rel = (a, 0, 0)``).
2. Polarization extraction: ``h_plus := (h[0,0] - h[1,1]) / 2``,
   ``h_cross := h[0,1]``.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from gwtb.bodies.multipole import quadrupole_second_derivative, quadrupole_third_derivative
from gwtb.source.quadrupole import luminosity, strain_tt
from tests.benchmarks.helpers import (
    ReferenceConstants,
    assert_relative,
    binary_si,
    circular_binary,
)

# --- T-1.0: fixture correctness ---------------------------------------------
#
# The barycentric check below is a floating-point cancellation of
# m1*x1 + m2*x2. Its absolute roundoff scales with the magnitude of the terms
# being cancelled (~M*a), so at binary_si()'s astronomical scale
# (M ~ 2e30 kg, a ~ 1e9 m) that roundoff floor is itself far above the
# atol=1e-9 the acceptance criterion asks for. atol=1e-9 is only a meaningful
# bar at a modest numeric scale, so the fixture's *mathematical* correctness
# (barycentric, correct derivatives, Kepler) is checked here at that scale;
# binary_si()'s *canonical parameter values* are checked separately below,
# using comparisons that don't depend on absolute scale.

_M1, _M2, _A, _T = 3.0, 5.0, 2.0, 1.7


def _omega(m1: float, m2: float, a: float, ref: ReferenceConstants) -> float:
    return math.sqrt(ref.G * (m1 + m2) / a**3)


def test_circular_binary_is_barycentric() -> None:
    masses, positions, _, _, _ = circular_binary(_M1, _M2, _A, _T)
    barycentre = np.einsum("a,ai->i", masses, positions)
    assert np.max(np.abs(barycentre)) <= 1e-9


def test_circular_binary_derivatives_match_central_differences() -> None:
    ref = ReferenceConstants()
    omega = _omega(_M1, _M2, _A, ref)
    h = 1e-3 / omega

    _, pos_0, vel_0, acc_0, jerk_0 = circular_binary(_M1, _M2, _A, _T)
    _, pos_p, vel_p, acc_p, _ = circular_binary(_M1, _M2, _A, _T + h)
    _, pos_m, vel_m, acc_m, _ = circular_binary(_M1, _M2, _A, _T - h)

    vel_numeric = (pos_p - pos_m) / (2.0 * h)
    acc_numeric = (vel_p - vel_m) / (2.0 * h)
    jerk_numeric = (acc_p - acc_m) / (2.0 * h)

    np.testing.assert_allclose(vel_numeric, vel_0, rtol=1e-6, atol=1e-9)
    np.testing.assert_allclose(acc_numeric, acc_0, rtol=1e-6, atol=1e-9)
    np.testing.assert_allclose(jerk_numeric, jerk_0, rtol=1e-6, atol=1e-9)


def test_circular_binary_omega_satisfies_kepler() -> None:
    ref = ReferenceConstants()
    b = binary_si()
    lhs = b.omega**2 * b.a**3
    rhs = ref.G * (b.m1 + b.m2)
    assert_relative(lhs, rhs, rtol=1e-12, what="Kepler's third law: omega^2 a^3 = G M")


def test_binary_si_canonical_parameters() -> None:
    b = binary_si()
    assert b.m1 == 1.0e30
    assert b.m2 == 1.0e30
    assert b.a == 1.0e9
    assert b.r == 1.0e20

    ref = ReferenceConstants()
    expected_omega = _omega(b.m1, b.m2, b.a, ref)
    assert_relative(b.omega, expected_omega, rtol=1e-12, what="binary_si().omega")
    assert_relative(b.t, 0.3 / b.omega, rtol=1e-12, what="binary_si().t")


# --- T-1.9: closed-form waveform and luminosity -----------------------------


def test_face_on_equal_mass_binary_matches_closed_form() -> None:
    ref = ReferenceConstants()
    b = binary_si()
    mu = b.m1 * b.m2 / (b.m1 + b.m2)
    iota = 0.0
    n_hat = np.array([0.0, 0.0, 1.0])

    q_ddot = quadrupole_second_derivative(b.masses, b.positions, b.velocities, b.accelerations)
    q_dddot = quadrupole_third_derivative(
        b.masses, b.positions, b.velocities, b.accelerations, b.jerks
    )

    h = strain_tt(q_ddot, b.r, n_hat)
    h_plus = (h[0, 0] - h[1, 1]) / 2.0
    h_cross = h[0, 1]
    power = luminosity(q_dddot)

    amplitude = 4.0 * ref.G * mu * b.omega**2 * b.a**2 / (ref.c**4 * b.r)
    expected_h_plus = -amplitude * (1.0 + math.cos(iota) ** 2) / 2.0 * math.cos(2.0 * b.omega * b.t)
    expected_h_cross = -amplitude * math.cos(iota) * math.sin(2.0 * b.omega * b.t)
    expected_power = (32.0 / 5.0) * (ref.G / ref.c**5) * mu**2 * b.a**4 * b.omega**6

    assert_relative(h_plus, expected_h_plus, rtol=1e-6, what="h_plus")
    assert_relative(h_cross, expected_h_cross, rtol=1e-6, what="h_cross")
    assert_relative(power, expected_power, rtol=1e-6, what="luminosity")


# --- Errata: Flanagan & Hughes (2005), Eqs. (4.41)-(4.42) -------------------


def test_errata_flanagan_hughes_4_41_4_42() -> None:
    """Corrected forms of FH (2005) Eqs. (4.41)-(4.42); see docs/ERRATA.md.

    ERR-001: the paper's worked circular-binary example prints
    ``I_22 = mu R^2 (cos^2(Omega t) - 1/3)``; the corrected form (matching the
    paper's own upstream Eq. 4.39) is ``sin^2(Omega t) - 1/3``.

    ERR-002: the paper's second time derivative is printed NON-symmetric, with
    ``(2,1)`` entry ``-sin(2 Omega t)``; a mass quadrupole moment is symmetric
    by construction, so this is impossible regardless of the algebra. The
    corrected ``(2,1)`` entry is ``+sin(2 Omega t)``.

    Both errors are scoped to Sec. 4.4's worked example only; the derivations
    in FH Sec. 4.1 (Eqs. 4.17, 4.19, 4.20, 4.22, 4.23) are correct and gwtb
    relies on them elsewhere.

    Do NOT "fix" this test to match the paper — the paper is wrong here, as
    established by differentiating its own Eq. (4.39) numerically (see
    docs/ERRATA.md for the full derivation and the independent verification).
    """
    mu = radius = omega = 1.0
    wt = 0.7391  # angle used in docs/ERRATA.md's verification
    h = 1e-4  # balances truncation (~h^2) against roundoff (~eps/h^2)

    def i_ij(t: float) -> np.ndarray:
        x = np.array([radius * math.cos(omega * t), radius * math.sin(omega * t), 0.0])
        return mu * (np.outer(x, x) - (radius**2 / 3.0) * np.eye(3))

    t0 = wt / omega
    ground_truth = (i_ij(t0 + h) - 2.0 * i_ij(t0) + i_ij(t0 - h)) / h**2

    # --- ERR-001: Eq. (4.41)'s I_22 component -----------------------------
    # The paper prints cos^2 on BOTH diagonal entries. Its own Eq. (4.39) gives
    # I_22 = mu (y^2 - R^2/3) = mu R^2 (sin^2 - 1/3).
    cos_wt, sin_wt = math.cos(wt), math.sin(wt)
    off_diag = mu * radius**2 * cos_wt * sin_wt

    i_as_printed = np.array(
        [
            [mu * radius**2 * (cos_wt**2 - 1 / 3), off_diag, 0.0],
            [off_diag, mu * radius**2 * (cos_wt**2 - 1 / 3), 0.0],  # printed: cos^2
            [0.0, 0.0, -mu * radius**2 / 3],
        ]
    )
    i_corrected = i_as_printed.copy()
    i_corrected[1, 1] = mu * radius**2 * (sin_wt**2 - 1 / 3)  # corrected: sin^2

    i_truth = i_ij(t0)
    assert np.max(np.abs(i_corrected - i_truth)) < 1e-15, (
        "corrected I_22 must reproduce the paper's own Eq. (4.39)"
    )
    assert np.max(np.abs(i_as_printed - i_truth)) > 1e-2, (
        "the printed cos^2 typo should disagree with Eq. (4.39) by O(0.1)"
    )
    # The printed form also breaks the trace relation that Eq. (4.39) enforces.
    assert abs(np.trace(i_corrected)) < 1e-15
    assert abs(np.trace(i_as_printed)) > 1e-2

    # --- ERR-002: Eq. (4.42)'s (2,1) sign ---------------------------------
    cos2, sin2 = math.cos(2.0 * wt), math.sin(2.0 * wt)
    prefactor = -2.0 * omega**2 * mu * radius**2

    as_printed = prefactor * np.array([[cos2, sin2, 0.0], [-sin2, -cos2, 0.0], [0.0, 0.0, 0.0]])
    corrected = prefactor * np.array([[cos2, sin2, 0.0], [sin2, -cos2, 0.0], [0.0, 0.0, 0.0]])

    # The printed (4.42) is not symmetric — impossible for a quadrupole moment.
    assert not np.allclose(as_printed, as_printed.T), "as-printed form should be non-symmetric"
    assert np.allclose(corrected, corrected.T, atol=1e-15), "corrected form must be symmetric"

    # The as-printed form disagrees with ground truth by O(1) (docs/ERRATA.md
    # measures 3.98 in these units); the corrected form agrees to
    # finite-difference precision.
    printed_error = np.max(np.abs(as_printed - ground_truth))
    corrected_error = np.max(np.abs(corrected - ground_truth))

    assert printed_error > 1.0, (
        f"expected the printed typo to differ from ground truth by O(1), got {printed_error:.3e}"
    )
    assert corrected_error < 1e-5, (
        f"corrected form should match ground truth (finite-difference limited), "
        f"got {corrected_error:.3e}"
    )


@pytest.mark.parametrize("seed", [0])
def test_errata_ground_truth_is_symmetric_by_construction(seed: int) -> None:
    """Sanity check on the ground-truth helper itself: I_ij = mu(x_i x_j - ...)
    is manifestly symmetric, so any asymmetry found upstream is a property of
    the *printed* formula, not of how this test computes its reference value.
    """
    rng = np.random.default_rng(seed)
    t = rng.uniform(0.0, 10.0)

    def i_ij(tt: float) -> np.ndarray:
        x = np.array([math.cos(tt), math.sin(tt), 0.0])
        return np.outer(x, x) - (1.0 / 3.0) * np.eye(3)

    m = i_ij(t)
    np.testing.assert_allclose(m, m.T, atol=1e-15)
