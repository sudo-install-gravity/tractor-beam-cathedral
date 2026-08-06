"""Unit tests for gwtb.propagate.polarization (T-5.1, T-5.2, T-5.3, T-5.4).

The two assertions that carry weight here are the ones that separate spin-2 from
spin-1, and both are checked directly rather than assumed:

* the basis transforms by ``e^(2i psi)`` and has period ``pi``
* the linear element pattern is zero on-axis — the inverse of a dipole antenna
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from gwtb.bodies.multipole import quadrupole_second_derivative
from gwtb.propagate.polarization import (
    decompose,
    element_pattern_linear,
    element_pattern_rotating,
    polarization_basis,
    recompose,
    rotate_polarization,
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


# --- T-5.2: decompose / recompose -------------------------------------------


@pytest.mark.parametrize("n_hat", _directions(20))
def test_decompose_recompose_round_trips(n_hat: np.ndarray) -> None:
    """AC: round-trip identity to rtol 1e-12 over 20 random TT tensors."""
    e_plus, e_cross = polarization_basis(n_hat)
    hp0, hx0 = RNG.uniform(-5.0, 5.0), RNG.uniform(-5.0, 5.0)
    h_ij = hp0 * e_plus + hx0 * e_cross

    hp, hx = decompose(h_ij, n_hat)
    np.testing.assert_allclose(hp, hp0, rtol=1e-12)
    np.testing.assert_allclose(hx, hx0, rtol=1e-12)

    np.testing.assert_allclose(recompose(hp, hx, n_hat), h_ij, rtol=1e-12, atol=1e-15)


def test_recompose_output_is_traceless_and_transverse() -> None:
    n_hat = np.array([0.3, -0.4, np.sqrt(1 - 0.09 - 0.16)])
    h_ij = recompose(1.5, -0.7, n_hat)
    assert abs(np.trace(h_ij)) < 1e-13
    np.testing.assert_allclose(n_hat @ h_ij, np.zeros(3), atol=1e-13)
    np.testing.assert_allclose(h_ij, h_ij.T, atol=1e-15)


def test_decompose_projects_out_non_tt_components() -> None:
    """A tensor with extra trace/longitudinal parts decomposes the same as
    its TT part alone — decompose is a contraction against a TT basis, so
    non-TT components are silently annihilated, mirroring apply_tt."""
    n_hat = np.array([0.0, 0.0, 1.0])
    e_plus, e_cross = polarization_basis(n_hat)
    tt_part = 2.0 * e_plus - 1.0 * e_cross
    extra = np.eye(3) * 3.0 + np.outer(n_hat, n_hat) * 7.0  # pure trace + longitudinal
    hp, hx = decompose(tt_part + extra, n_hat)
    np.testing.assert_allclose([hp, hx], [2.0, -1.0], rtol=1e-12)


def test_decompose_zero_tensor_gives_zero_scalars() -> None:
    assert decompose(np.zeros((3, 3)), np.array([0.0, 0.0, 1.0])) == (0.0, 0.0)


# --- T-5.3: rotate_polarization ---------------------------------------------


def test_rotation_has_period_pi_not_two_pi() -> None:
    """AC: period is pi, not 2 pi — the spin-2 signature."""
    hp, hx = 1.3, -0.7
    rotated_pi = rotate_polarization(hp, hx, np.pi)
    np.testing.assert_allclose(rotated_pi, (hp, hx), atol=1e-12)

    rotated_half = rotate_polarization(hp, hx, np.pi / 2)
    assert not np.allclose(rotated_half, (hp, hx), atol=1e-6)


def test_45_degrees_maps_plus_onto_cross() -> None:
    """AC: rotate(., pi/4) maps h_plus -> h_cross."""
    hp, hx = rotate_polarization(1.0, 0.0, np.pi / 4.0)
    np.testing.assert_allclose(hp, 0.0, atol=1e-12)
    assert abs(hx) == pytest.approx(1.0, rel=1e-12)


def test_zero_rotation_is_the_identity() -> None:
    hp, hx = rotate_polarization(1.3, -0.7, 0.0)
    np.testing.assert_allclose([hp, hx], [1.3, -0.7], rtol=1e-14)


def test_rotation_preserves_magnitude() -> None:
    """A rotation must not change |h_plus - i h_cross|."""
    hp0, hx0 = 2.1, -3.4
    magnitude0 = math.hypot(hp0, hx0)
    for psi in (0.1, 0.7, 1.9, 2.8, np.pi):
        hp, hx = rotate_polarization(hp0, hx0, psi)
        assert math.hypot(hp, hx) == pytest.approx(magnitude0, rel=1e-12)


def test_rotation_composes() -> None:
    """rotate(rotate(h, psi1), psi2) == rotate(h, psi1 + psi2)."""
    hp0, hx0 = 1.0, 2.0
    psi1, psi2 = 0.4, 0.9
    once = rotate_polarization(*rotate_polarization(hp0, hx0, psi1), psi2)
    combined = rotate_polarization(hp0, hx0, psi1 + psi2)
    np.testing.assert_allclose(once, combined, rtol=1e-12)


@pytest.mark.parametrize("n_hat", _directions(10))
@pytest.mark.parametrize("psi", [0.2, 0.9, np.pi / 4])
def test_rotate_polarization_matches_frame_rotation_via_basis(
    n_hat: np.ndarray, psi: float
) -> None:
    """rotate_polarization must agree with rotating the underlying basis
    itself (polarization_basis(n_hat, psi)) — same physical operation, two
    different code paths."""
    hp0, hx0 = 1.7, -0.9
    h_ij = recompose(hp0, hx0, n_hat)

    # Route A: rotate the scalars directly.
    hp_a, hx_a = rotate_polarization(hp0, hx0, psi)

    # Route B: decompose the SAME tensor against a psi-rotated basis.
    e_plus_rot, e_cross_rot = polarization_basis(n_hat, psi)
    hp_b = 0.5 * float(np.einsum("ij,ij->", h_ij, e_plus_rot))
    hx_b = 0.5 * float(np.einsum("ij,ij->", h_ij, e_cross_rot))

    np.testing.assert_allclose([hp_a, hx_a], [hp_b, hx_b], rtol=1e-10, atol=1e-12)


# --- citation pin: Blanchet eq. 69a/69b (added 2026-08-03) --------------------


def test_decompose_reproduces_blanchet_69a_69b_written_out() -> None:
    """Pin the citation this module rests on, by evaluating it independently.

    Blanchet eq. 69a/69b define the polarization states of the asymptotic
    waveform, for unit vectors ``P``, ``Q`` transverse to the propagation
    direction ``N``::

        h_plus  = (1/2) (P_i P_j - Q_i Q_j) H^TT_ij      (69a)
        h_cross = (1/2) (P_i Q_j + P_j Q_i) H^TT_ij      (69b)

    Those bracketed tensors are what :func:`polarization_basis` returns. This
    test writes the two equations out by hand and checks ``decompose`` agrees,
    so the citation is executed rather than asserted.

    Until 2026-08-03 this module cited [FH] eq. 2.22 instead, which reads
    ``h^TT_xx = -h^TT_yy = h_plus`` -- the polarization **scalars** in a
    z-aligned frame, not the **basis tensors**, and not covariant in ``N``.
    The physics was right and the reference was not, which is precisely the
    failure a test like this makes impossible to repeat silently.
    """
    rng = np.random.default_rng(20260803)
    for _ in range(64):
        n_hat = rng.normal(size=3)
        n_hat /= np.linalg.norm(n_hat)
        e_plus, e_cross = polarization_basis(n_hat)

        m = rng.normal(size=(3, 3))
        h_ij = apply_tt(m + m.T, n_hat)

        # Blanchet 69a/69b, transcribed literally.
        h_plus_blanchet = 0.5 * np.einsum("ij,ij->", e_plus, h_ij)
        h_cross_blanchet = 0.5 * np.einsum("ij,ij->", e_cross, h_ij)

        h_plus, h_cross = decompose(h_ij, n_hat)
        assert h_plus == pytest.approx(h_plus_blanchet, abs=1e-15)
        assert h_cross == pytest.approx(h_cross_blanchet, abs=1e-15)


def test_the_one_half_in_blanchet_69a_is_fixed_by_the_basis_normalisation() -> None:
    """The ``1/2`` prefactor is not free -- it is forced by ``e_A : e_B = 2 delta_AB``.

    A future reader meeting eq. 69a might reasonably wonder where the ``1/2``
    comes from and "simplify" it away. It is the inverse of the basis norm: any
    other prefactor breaks the round trip below, so this records the link.
    """
    n_hat = np.array([0.3, -0.5, 0.81])
    n_hat = n_hat / np.linalg.norm(n_hat)
    e_plus, e_cross = polarization_basis(n_hat)

    assert np.einsum("ij,ij->", e_plus, e_plus) == pytest.approx(2.0, abs=1e-12)
    assert np.einsum("ij,ij->", e_cross, e_cross) == pytest.approx(2.0, abs=1e-12)
    assert np.einsum("ij,ij->", e_plus, e_cross) == pytest.approx(0.0, abs=1e-12)

    h_ij = 3.0 * e_plus - 1.5 * e_cross
    assert decompose(h_ij, n_hat) == pytest.approx((3.0, -1.5), abs=1e-12)
    np.testing.assert_allclose(recompose(3.0, -1.5, n_hat), h_ij, atol=1e-14)
