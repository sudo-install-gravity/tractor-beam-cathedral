"""Unit tests for gwtb.source.quadrupole (T-1.7, T-1.8)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.source.quadrupole import luminosity, strain_tt


def _random_symmetric(rng: np.random.Generator) -> np.ndarray:
    a = rng.normal(size=(3, 3))
    return a + a.T


# --- T-1.7 -------------------------------------------------------------------


def test_strain_tt_is_traceless_and_transverse() -> None:
    rng = np.random.default_rng(7)
    q_ddot = _random_symmetric(rng)
    n_hat = np.array([0.0, 0.0, 1.0])
    h = strain_tt(q_ddot, 1e20, n_hat)

    scale = np.max(np.abs(h))
    assert abs(np.trace(h)) <= 1e-12 * scale
    assert np.max(np.abs(n_hat @ h)) <= 1e-12 * scale


def test_strain_tt_halving_r_doubles_amplitude() -> None:
    rng = np.random.default_rng(11)
    q_ddot = _random_symmetric(rng)
    n_hat = np.array([0.0, 0.0, 1.0])
    r = 3.0e20

    h_full = strain_tt(q_ddot, r, n_hat)
    h_half = strain_tt(q_ddot, r / 2.0, n_hat)
    np.testing.assert_allclose(h_half, 2.0 * h_full, rtol=1e-12)


def test_strain_tt_rejects_non_positive_r() -> None:
    q_ddot = np.eye(3)
    n_hat = np.array([0.0, 0.0, 1.0])
    with pytest.raises(ValueError):
        strain_tt(q_ddot, 0.0, n_hat)
    with pytest.raises(ValueError):
        strain_tt(q_ddot, -1.0, n_hat)


# --- T-1.8 -------------------------------------------------------------------


def test_luminosity_returns_nonnegative_float() -> None:
    rng = np.random.default_rng(13)
    q_dddot = _random_symmetric(rng)
    power = luminosity(q_dddot)
    assert isinstance(power, float)
    assert power >= 0.0


def test_luminosity_of_zero_is_zero() -> None:
    assert luminosity(np.zeros((3, 3))) == 0.0
