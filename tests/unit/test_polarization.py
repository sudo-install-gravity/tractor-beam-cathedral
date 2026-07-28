"""Unit tests for gwtb.propagate.polarization (T-5.1, T-5.4).

The two assertions that carry weight here are the ones that separate spin-2 from
spin-1, and both are checked directly rather than assumed:

* the basis transforms by ``e^(2i psi)`` and has period ``pi``
* the linear element pattern is zero on-axis — the inverse of a dipole antenna
"""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.bodies.multipole import quadrupole_second_derivative
from gwtb.propagate.polarization import (
    element_pattern_linear,
    element_pattern_rotating,
    polarization_basis,
)
from gwtb.propagate.tt_projection import apply_tt

RNG = np.random.default_rng(20260727)


def _directions(n: int = 20) -> list[np.ndarray]:
    v = RNG.normal(size=(n, 3))
    dirs = [x / np.linalg.norm(x) for x in v]
    return [*dirs, np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, -1.0])]


# --- T-5.1: polarization basis ------------------------------------------------


@pytest.mark.parametrize("n_hat", _directions())
def test_basis_is_traceless_and_transverse(n_hat: np.ndarray) -> None:
    for e in polarization_basis(n_hat):
        assert abs(np.trace(e)) < 1e-12
        assert np.abs(n_hat @ e).max() < 1e-12
        np.testing.assert_allclose(e, e.T, atol=1e-15)


@pytest.mark.parametrize("n_hat", _directions())
def test_basis_is_orthonormal_under_double_contraction(n_hat: np.ndarray) -> None:
    """AC: ``e_A : e_B = 2 delta_AB``."""
    e_plus, e_cross = polarization_basis(n_hat)
    assert np.einsum("ij,ij->", e_plus, e_plus) == pytest.approx(2.0, abs=1e-12)
    assert np.einsum("ij,ij->", e_cross, e_cross) == pytest.approx(2.0, abs=1e-12)
    assert abs(np.einsum("ij,ij->", e_plus, e_cross)) < 1e-12


@pytest.mark.parametrize("n_hat", _directions(8))
@pytest.mark.parametrize("psi", [0.1, 0.5, 1.0, np.pi / 4, np.pi / 3])
def test_frame_rotation_transforms_amplitudes_by_exp_2i_psi(n_hat: np.ndarray, psi: float) -> None:
    """AC: rotating the basis by psi transforms amplitudes by e^(2i psi).

    Asserted directly, not assumed. Decompose a fixed TT tensor in both the
    canonical frame and one rotated by ``psi``; the complex amplitude
    ``h = h_plus - i h_cross`` must pick up exactly ``e^(2i psi)``.
    """
    m = RNG.normal(size=(3, 3))
    h = apply_tt(m + m.T, n_hat)

    def amplitude(rot: float) -> complex:
        e_p, e_c = polarization_basis(n_hat, rot)
        return 0.5 * np.einsum("ij,ij->", h, e_p) - 0.5j * np.einsum("ij,ij->", h, e_c)

    rotated, expected = amplitude(psi), amplitude(0.0) * np.exp(2j * psi)
    assert rotated == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("n_hat", _directions(8))
def test_basis_has_period_pi_not_two_pi(n_hat: np.ndarray) -> None:
    """The spin-2 signature: period pi. A spin-1 field would need 2 pi."""
    base = polarization_basis(n_hat, 0.0)
    for e_ref, e_pi in zip(base, polarization_basis(n_hat, np.pi), strict=True):
        np.testing.assert_allclose(e_pi, e_ref, atol=1e-12)
    # ...and half a period inverts the sign, rather than returning to itself.
    for e_ref, e_half in zip(base, polarization_basis(n_hat, np.pi / 2), strict=True):
        np.testing.assert_allclose(e_half, -e_ref, atol=1e-12)


def test_45_degree_rotation_maps_plus_onto_cross() -> None:
    """h_plus and h_cross are 45 degrees apart, not 90."""
    n = np.array([0.0, 0.0, 1.0])
    e_plus, e_cross = polarization_basis(n, 0.0)
    rot_plus, _ = polarization_basis(n, np.pi / 4)
    np.testing.assert_allclose(rot_plus, e_cross, atol=1e-12)


def test_basis_rejects_non_unit_direction() -> None:
    with pytest.raises(ValueError):
        polarization_basis(np.array([0.0, 0.0, 2.0]))


# --- T-5.4: element patterns --------------------------------------------------


def _pol_from_quadrupole(q_ddot: np.ndarray, n: np.ndarray) -> tuple[float, float]:
    h = apply_tt(q_ddot, n)
    e_p, e_c = polarization_basis(n)
    return 0.5 * np.einsum("ij,ij->", h, e_p), 0.5 * np.einsum("ij,ij->", h, e_c)


@pytest.mark.parametrize("deg", [0, 30, 45, 60, 90])
def test_linear_pattern_matches_quadrupole_calculation(deg: float) -> None:
    """Cross-check the closed form against the validated quadrupole path."""
    th = np.radians(deg)
    n = np.array([np.sin(th), 0.0, np.cos(th)])
    z = np.array([0.0, 0.0, 1.0])
    x = np.array([z, -z])
    q = quadrupole_second_derivative([1.0, 1.0], x, np.zeros((2, 3)), np.array([-z, z]))
    hp, hx = _pol_from_quadrupole(q, n)
    expected, _ = element_pattern_linear(th)
    assert abs(hp) / 2.0 == pytest.approx(float(expected), abs=1e-9)
    assert abs(hx) < 1e-12


def test_linear_pattern_is_zero_on_axis_and_maximal_broadside() -> None:
    """AC: the OPPOSITE of a dipole antenna pattern — asserted explicitly.

    A linear mass quadrupole radiates nothing along its own axis of motion.
    Anyone substituting spin-1 intuition gets a beam pointed exactly where the
    source is silent.
    """
    on_axis, _ = element_pattern_linear(0.0)
    broadside, _ = element_pattern_linear(np.pi / 2)
    assert float(on_axis) == pytest.approx(0.0, abs=1e-15)
    assert float(broadside) == pytest.approx(1.0, abs=1e-15)
    assert float(broadside) > float(on_axis)

    th = np.linspace(0.0, np.pi / 2, 50)
    pattern, _ = element_pattern_linear(th)
    assert np.all(np.diff(pattern) > 0), "pattern must rise monotonically off-axis"


@pytest.mark.parametrize("deg", [0, 30, 45, 60, 90])
def test_rotating_pattern_matches_quadrupole_calculation(deg: float) -> None:
    """Cross-check against the validated quadrupole path, at the analytic peak.

    The orbital phase is set to the known peak rather than scanned for it: a
    400-point sweep leaves an 8e-6 residual that falls as 1/N², which is a
    sampling artifact and not physics. Measuring at the peak removes it.
    """
    th = np.radians(deg)
    n = np.array([np.sin(th), 0.0, np.cos(th)])
    norm = 4.0

    peaks = []
    for phase in (0.0, np.pi / 4):  # h_plus peaks at 0, h_cross a quarter later
        c, s = np.cos(phase), np.sin(phase)
        x = np.array([[c, s, 0.0], [-c, -s, 0.0]])
        v = np.array([[-s, c, 0.0], [s, -c, 0.0]])
        peaks.append(_pol_from_quadrupole(quadrupole_second_derivative([1.0, 1.0], x, v, -x), n))

    exp_p, exp_x = element_pattern_rotating(th)
    assert abs(peaks[0][0]) / norm == pytest.approx(float(exp_p), abs=1e-12)
    assert abs(peaks[1][1]) / norm == pytest.approx(abs(float(exp_x)), abs=1e-12)


def test_rotating_pattern_is_circular_face_on_and_linear_edge_on() -> None:
    hp, hx = element_pattern_rotating(0.0)
    assert float(hp) == pytest.approx(1.0) and abs(float(hx)) == pytest.approx(1.0)

    hp, hx = element_pattern_rotating(np.pi / 2)
    assert float(hp) == pytest.approx(0.5) and float(hx) == pytest.approx(0.0, abs=1e-15)


def test_patterns_accept_arrays() -> None:
    th = np.linspace(0.0, np.pi, 7)
    for fn in (element_pattern_rotating, element_pattern_linear):
        hp, hx = fn(th)
        assert hp.shape == th.shape and hx.shape == th.shape
        assert hp.dtype == np.float64
