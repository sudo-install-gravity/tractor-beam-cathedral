"""Unit tests for gwtb.source.multipole_rad (T-2.3, T-2.4)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.core.constants import AU
from gwtb.source.conservation import UNPHYSICAL_STAMP, StampedResult
from gwtb.source.multipole_rad import (
    dipole_moment,
    dipole_second_derivative,
    dipole_strain,
)

_N_BODIES = 5
_R = 40.0 * AU
_N_HAT = np.array([0.0, 0.0, 1.0])


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


# --- dipole_strain (T-2.4) ---------------------------------------------------

_D_DDOT = np.array([1.0e3, 2.0e3, -5.0e2])


def test_always_returns_a_stamped_result() -> None:
    r = dipole_strain(_D_DDOT, _R, _N_HAT)
    assert isinstance(r, StampedResult)
    assert r.is_unphysical is True
    assert r.provenance is not None
    assert UNPHYSICAL_STAMP in r.provenance


def test_raises_for_momentum_conserving_source() -> None:
    with pytest.raises(ValueError, match="momentum"):
        dipole_strain(np.zeros(3), _R, _N_HAT)


def test_allow_trivial_permits_the_zero_case_and_still_stamps() -> None:
    r = dipole_strain(np.zeros(3), _R, _N_HAT, allow_trivial=True)
    assert r.is_unphysical is True
    np.testing.assert_array_equal(r.value, np.zeros((3, 3)))


def test_result_is_symmetric_traceless_and_transverse() -> None:
    h = dipole_strain(_D_DDOT, _R, _N_HAT).value
    np.testing.assert_allclose(h, h.T, rtol=1e-14)
    assert abs(np.trace(h)) < 1e-9 * np.max(np.abs(h))
    np.testing.assert_allclose(h @ _N_HAT, np.zeros(3), atol=1e-9 * np.max(np.abs(h)))


def test_result_is_independent_of_r() -> None:
    """Documented, not accidental: unlike genuine radiation, this diagnostic
    does not fall off with distance — evidence it is not a physical field.
    """
    near = dipole_strain(_D_DDOT, 1.0e6, _N_HAT).value
    far = dipole_strain(_D_DDOT, 1.0e15, _N_HAT).value
    np.testing.assert_allclose(near, far, rtol=1e-12)


def test_scales_quadratically_with_d_ddot() -> None:
    """The construction is a self-outer-square, so it is quadratic in d_ddot."""
    a = dipole_strain(_D_DDOT, _R, _N_HAT).value
    b = dipole_strain(3.0 * _D_DDOT, _R, _N_HAT).value
    np.testing.assert_allclose(b, 9.0 * a, rtol=1e-13)


def test_vanishes_when_d_ddot_is_parallel_to_n_hat() -> None:
    """The expected on-axis null — not the unconditional-zero bug of the
    n_hat-symmetrized construction this function does NOT use.
    """
    h = dipole_strain(np.array([0.0, 0.0, 7.0e3]), _R, _N_HAT).value
    np.testing.assert_allclose(h, np.zeros((3, 3)), atol=1e-30)


def test_nonzero_when_d_ddot_is_transverse_to_n_hat() -> None:
    h = dipole_strain(np.array([7.0e3, 0.0, 0.0]), _R, _N_HAT).value
    assert np.max(np.abs(h)) > 0.0


def test_magnitude_is_finite_and_positive_for_a_generic_transverse_input() -> None:
    """Not a magnitude claim against the quadrupole channel — this function's
    docstring is explicit that no citable formula, and therefore no specific
    predicted ratio, applies to this diagnostic. CLAUDE.md rule 2's "~1e10x"
    figure describes a different comparison (a genuinely single accelerating
    body's own quadrupole against the symmetric two-body construction, per
    ADR-0004), not this construction.
    """
    h = dipole_strain(np.array([1.0e4, 0.0, 0.0]), _R, _N_HAT).value
    magnitude = np.max(np.abs(h))
    assert np.isfinite(magnitude)
    assert magnitude > 0.0


def test_validation() -> None:
    with pytest.raises(ValueError, match=r"\(3,\)"):
        dipole_strain([1.0, 2.0], _R, _N_HAT)
    with pytest.raises(ValueError, match="unit vector"):
        dipole_strain(_D_DDOT, _R, np.array([0.0, 0.0, 2.0]))
    with pytest.raises(ValueError, match="positive"):
        dipole_strain(_D_DDOT, -1.0, _N_HAT)
    with pytest.raises(TypeError, match="float32"):
        dipole_strain(_D_DDOT.astype(np.float32), _R, _N_HAT)
