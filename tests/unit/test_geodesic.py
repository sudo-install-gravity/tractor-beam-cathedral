"""Unit tests for gwtb.target.geodesic (T-8.1)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.propagate.tt_projection import apply_tt
from gwtb.target.geodesic import deviation_acceleration

_N_HAT = np.array([0.0, 0.0, 1.0])


def _random_tt(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    raw = rng.uniform(-5.0, 5.0, size=(3, 3))
    raw = raw + raw.T
    return apply_tt(raw, _N_HAT)


def test_matches_the_closed_form() -> None:
    h = _random_tt(0)
    xi = np.array([1.0, 2.0, 3.0])
    result = deviation_acceleration(h, xi)
    np.testing.assert_allclose(result, 0.5 * (h @ xi), rtol=1e-14)


def test_scales_linearly_with_h_and_separation() -> None:
    h = _random_tt(1)
    xi = np.array([1.0, -2.0, 0.5])
    base = deviation_acceleration(h, xi)
    np.testing.assert_allclose(deviation_acceleration(2.0 * h, xi), 2.0 * base, rtol=1e-13)
    np.testing.assert_allclose(deviation_acceleration(h, 3.0 * xi), 3.0 * base, rtol=1e-13)


def test_zero_separation_gives_zero_acceleration() -> None:
    h = _random_tt(2)
    np.testing.assert_array_equal(deviation_acceleration(h, np.zeros(3)), np.zeros(3))


def test_zero_strain_gives_zero_acceleration() -> None:
    xi = np.array([1.0, 2.0, 3.0])
    np.testing.assert_array_equal(deviation_acceleration(np.zeros((3, 3)), xi), np.zeros(3))


# --- AC: transverse to propagation -----------------------------------------


@pytest.mark.parametrize("seed", range(5))
def test_result_is_transverse_to_the_propagation_direction(seed: int) -> None:
    """A TT h_ij, contracted with ANY separation vector — including one with
    a component along n_hat — gives an acceleration with no component along
    n_hat, because h_ij's own rows/columns along n_hat vanish."""
    h = _random_tt(seed)
    rng = np.random.default_rng(seed + 100)
    xi = rng.uniform(-3.0, 3.0, size=3)  # generic direction, not transverse
    result = deviation_acceleration(h, xi)
    assert abs(result @ _N_HAT) < 1e-12 * max(np.max(np.abs(result)), 1e-300)


def test_separation_purely_along_propagation_gives_zero() -> None:
    h = _random_tt(3)
    xi_parallel = 5.0 * _N_HAT
    result = deviation_acceleration(h, xi_parallel)
    np.testing.assert_allclose(result, np.zeros(3), atol=1e-12)


# --- AC: net acceleration of the center of mass is zero --------------------


def test_net_acceleration_of_the_center_of_mass_is_zero() -> None:
    """The defining property of geodesic deviation, asserted directly.

    A GW is curvature, not force: it never accelerates a body's center of
    mass. For any set of masses, the pairwise-averaged separation about the
    centroid is identically zero, so the mass-weighted mean of
    deviation_acceleration evaluated over separations-from-centroid is zero
    by linearity — asserted here as an explicit computation, not merely an
    algebraic aside.
    """
    h = _random_tt(4)
    positions = np.array([[1.0, 2.0, -1.0], [-3.0, 0.5, 2.0], [4.0, -4.0, 0.0], [-2.0, 1.5, -1.0]])
    masses = np.array([2.0, 5.0, 1.0, 3.0])
    centroid = np.einsum("a,ai->i", masses, positions) / masses.sum()
    separations = positions - centroid

    per_body = np.array([deviation_acceleration(h, xi) for xi in separations])
    net = np.einsum("a,ai->i", masses, per_body) / masses.sum()
    np.testing.assert_allclose(net, np.zeros(3), atol=1e-12)


def test_relative_acceleration_between_two_bodies_is_generically_nonzero() -> None:
    """Positive control: the tidal (relative) effect is real even though the
    center-of-mass effect vanishes — the zero above must not be vacuous."""
    h = _random_tt(5)
    xi = np.array([1.0, -1.0, 0.0])
    result = deviation_acceleration(h, xi)
    assert np.max(np.abs(result)) > 0.0


# --- validation --------------------------------------------------------------


def test_rejects_wrong_h_shape() -> None:
    with pytest.raises(ValueError, match=r"\(3, 3\)"):
        deviation_acceleration(np.zeros((2, 2)), np.zeros(3))


def test_rejects_wrong_separation_shape() -> None:
    with pytest.raises(ValueError, match=r"\(3,\)"):
        deviation_acceleration(np.zeros((3, 3)), np.zeros(2))


def test_rejects_float32() -> None:
    """ADR-0002 §5: float32 is rejected, not upcast."""
    h = _random_tt(6)
    with pytest.raises(TypeError, match="float32"):
        deviation_acceleration(h.astype(np.float32), np.array([1.0, 0.0, 0.0]))
