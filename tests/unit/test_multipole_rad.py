"""Unit tests for gwtb.source.multipole_rad (T-2.3)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.source.multipole_rad import dipole_moment, dipole_second_derivative

_N_BODIES = 5


def _random_bodies(seed: int, n: int = _N_BODIES) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    masses = rng.uniform(1.0, 100.0, size=n)
    positions = rng.uniform(-5.0, 5.0, size=(n, 3))
    return masses, positions


# --- dipole_moment -----------------------------------------------------------


def test_dipole_moment_equals_mass_weighted_position_sum() -> None:
    masses, positions = _random_bodies(0)
    d = dipole_moment(masses, positions)
    expected = np.einsum("a,ai->i", masses, positions)
    np.testing.assert_allclose(d, expected, rtol=1e-15)


def test_dipole_moment_single_mass_on_axis() -> None:
    d = dipole_moment([2.0], [[3.0, 0.0, 0.0]])
    np.testing.assert_allclose(d, [6.0, 0.0, 0.0], rtol=1e-15)


def test_dipole_moment_zero_for_symmetric_pair() -> None:
    """Equal masses at +x and -x: the dipole (odd in x) vanishes exactly."""
    masses = [1.0, 1.0]
    positions = [[2.0, 0.0, 0.0], [-2.0, 0.0, 0.0]]
    d = dipole_moment(masses, positions)
    np.testing.assert_allclose(d, np.zeros(3), atol=1e-15)


def test_dipole_moment_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError):
        dipole_moment([1.0, 2.0, 3.0], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


def test_dipole_moment_rejects_float32() -> None:
    masses = np.array([1.0, 2.0], dtype=np.float32)
    positions = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float64)
    with pytest.raises(TypeError):
        dipole_moment(masses, positions)

    masses64 = np.array([1.0, 2.0], dtype=np.float64)
    positions32 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    with pytest.raises(TypeError):
        dipole_moment(masses64, positions32)


def test_dipole_moment_is_float64() -> None:
    masses, positions = _random_bodies(1)
    d = dipole_moment(masses, positions)
    assert d.dtype == np.float64
    assert d.shape == (3,)


# --- dipole_second_derivative -------------------------------------------------


def test_dipole_second_derivative_equals_momentum_derivative() -> None:
    rng = np.random.default_rng(2)
    masses = rng.uniform(1.0, 100.0, size=_N_BODIES)
    accelerations = rng.uniform(-10.0, 10.0, size=(_N_BODIES, 3))
    ddd = dipole_second_derivative(masses, accelerations)
    expected = np.einsum("a,ai->i", masses, accelerations)
    np.testing.assert_allclose(ddd, expected, rtol=1e-15)


def test_dipole_second_derivative_zero_for_momentum_conserving_configuration() -> None:
    """AC: zero for momentum-conserving input to atol 1e-12.

    Do NOT "fix" this to be nonzero — see docs/PHYSICS.md §2 and CLAUDE.md:
    the vanishing IS the physics (no dipole radiation for an isolated system).
    """
    rng = np.random.default_rng(20260726)
    for _ in range(20):
        masses = rng.uniform(1.0, 100.0, size=_N_BODIES)
        accelerations = rng.uniform(-10.0, 10.0, size=(_N_BODIES, 3))
        mean_acc = np.einsum("a,ai->i", masses, accelerations) / np.sum(masses)
        accelerations = accelerations - mean_acc

        ddd = dipole_second_derivative(masses, accelerations)
        scale = np.sum(masses) * np.max(np.linalg.norm(accelerations, axis=1))
        assert np.max(np.abs(ddd)) <= 1e-12 * scale


def test_dipole_second_derivative_nonzero_for_unbalanced_configuration() -> None:
    """Positive control: an unbalanced configuration must NOT vanish, so the
    zero-check above cannot be satisfied vacuously."""
    rng = np.random.default_rng(99)
    masses = rng.uniform(1.0, 100.0, size=_N_BODIES)
    accelerations = rng.uniform(-10.0, 10.0, size=(_N_BODIES, 3))
    ddd = dipole_second_derivative(masses, accelerations)
    scale = np.sum(masses) * np.max(np.linalg.norm(accelerations, axis=1))
    assert np.max(np.abs(ddd)) > 1e-3 * scale


def test_dipole_second_derivative_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError):
        dipole_second_derivative([1.0, 2.0, 3.0], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


def test_dipole_second_derivative_rejects_float32() -> None:
    masses = np.array([1.0, 2.0], dtype=np.float32)
    accelerations = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float64)
    with pytest.raises(TypeError):
        dipole_second_derivative(masses, accelerations)

    masses64 = np.array([1.0, 2.0], dtype=np.float64)
    accelerations32 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    with pytest.raises(TypeError):
        dipole_second_derivative(masses64, accelerations32)


def test_dipole_second_derivative_is_float64() -> None:
    masses, positions = _random_bodies(3)
    accelerations = np.random.default_rng(4).uniform(-1.0, 1.0, size=positions.shape)
    ddd = dipole_second_derivative(masses, accelerations)
    assert ddd.dtype == np.float64
    assert ddd.shape == (3,)
