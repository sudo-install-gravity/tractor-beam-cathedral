"""Unit tests for gwtb.source.memory (T-3.7)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.core.constants import AU
from gwtb.source.memory import linear_memory

_R = 40.0 * AU
_N_HAT = np.array([0.0, 0.0, 1.0])


def _symmetric_pair(v: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Two equal masses recoiling along x — momentum-conserving by construction."""
    masses = np.array([500.0, 500.0])
    rest = np.zeros((2, 3))
    moving = np.array([[v, 0.0, 0.0], [-v, 0.0, 0.0]])
    return masses, rest, moving


# --- AC: traceless and transverse -----------------------------------------


def test_result_is_traceless() -> None:
    masses, rest, moving = _symmetric_pair(1.0e3)
    h = linear_memory(masses, rest, moving, _R, _N_HAT)
    assert abs(np.trace(h)) < 1e-60


def test_result_is_transverse_to_n_hat() -> None:
    masses, rest, moving = _symmetric_pair(1.0e3)
    h = linear_memory(masses, rest, moving, _R, _N_HAT)
    np.testing.assert_allclose(h @ _N_HAT, np.zeros(3), atol=1e-60)


def test_result_is_symmetric() -> None:
    masses, rest, moving = _symmetric_pair(1.0e3)
    h = linear_memory(masses, rest, moving, _R, _N_HAT)
    np.testing.assert_allclose(h, h.T, rtol=0, atol=0)


def test_traceless_and_transverse_for_an_oblique_direction() -> None:
    masses, rest, moving = _symmetric_pair(2.5e3)
    n = np.array([1.0, 2.0, -3.0])
    n = n / np.linalg.norm(n)
    h = linear_memory(masses, rest, moving, _R, n)
    assert abs(np.trace(h)) < 1e-60
    np.testing.assert_allclose(h @ n, np.zeros(3), atol=1e-60)


# --- AC: zero when velocities are unchanged -------------------------------


def test_zero_when_velocities_unchanged() -> None:
    masses = np.array([100.0, 250.0, 7.0])
    v = np.array([[1.0, 2.0, 3.0], [-4.0, 5.0, 6.0], [7.0, -8.0, 9.0]])
    h = linear_memory(masses, v, v, _R, _N_HAT)
    np.testing.assert_array_equal(h, np.zeros((3, 3)))


def test_zero_from_rest_to_rest() -> None:
    masses, rest, _ = _symmetric_pair(1.0)
    h = linear_memory(masses, rest, rest, _R, _N_HAT)
    np.testing.assert_array_equal(h, np.zeros((3, 3)))


# --- AC: scales as 1/r -----------------------------------------------------


def test_scales_as_one_over_r() -> None:
    masses, rest, moving = _symmetric_pair(1.0e3)
    near = linear_memory(masses, rest, moving, _R, _N_HAT)
    far = linear_memory(masses, rest, moving, 10.0 * _R, _N_HAT)
    np.testing.assert_allclose(far, near / 10.0, rtol=1e-15)


def test_scales_as_one_over_r_across_four_decades() -> None:
    masses, rest, moving = _symmetric_pair(1.0e3)
    reference = linear_memory(masses, rest, moving, 1.0e9, _N_HAT)
    for factor in (1.0e1, 1.0e2, 1.0e3, 1.0e4):
        scaled = linear_memory(masses, rest, moving, 1.0e9 * factor, _N_HAT)
        np.testing.assert_allclose(scaled * factor, reference, rtol=1e-14)


# --- physical scaling ------------------------------------------------------


def test_scales_quadratically_with_velocity() -> None:
    """The source term is ``M v^k v^l``, so doubling v quadruples the memory."""
    masses, rest, slow = _symmetric_pair(1.0e3)
    _, _, fast = _symmetric_pair(2.0e3)
    h_slow = linear_memory(masses, rest, slow, _R, _N_HAT)
    h_fast = linear_memory(masses, rest, fast, _R, _N_HAT)
    np.testing.assert_allclose(h_fast, 4.0 * h_slow, rtol=1e-14)


def test_scales_linearly_with_mass() -> None:
    masses, rest, moving = _symmetric_pair(1.0e3)
    h_one = linear_memory(masses, rest, moving, _R, _N_HAT)
    h_two = linear_memory(2.0 * masses, rest, moving, _R, _N_HAT)
    np.testing.assert_allclose(h_two, 2.0 * h_one, rtol=1e-14)


def test_sign_reverses_when_initial_and_final_are_swapped() -> None:
    masses, rest, moving = _symmetric_pair(1.0e3)
    forward = linear_memory(masses, rest, moving, _R, _N_HAT)
    backward = linear_memory(masses, moving, rest, _R, _N_HAT)
    np.testing.assert_allclose(backward, -forward, rtol=1e-15)


def test_memory_is_independent_of_the_sign_of_the_velocities() -> None:
    """``v^k v^l`` is even in v: reversing every velocity changes nothing."""
    masses, rest, moving = _symmetric_pair(1.0e3)
    h_plus = linear_memory(masses, rest, moving, _R, _N_HAT)
    h_minus = linear_memory(masses, rest, -moving, _R, _N_HAT)
    np.testing.assert_allclose(h_minus, h_plus, rtol=1e-15)


def test_observer_along_the_motion_axis_sees_no_memory() -> None:
    """A quadrupole radiates nothing along its symmetry axis.

    Bodies recoiling along x produce a source tensor with only an ``xx``
    component; projected transverse to ``n_hat = x``, it vanishes identically.
    """
    masses, rest, moving = _symmetric_pair(1.0e3)
    h = linear_memory(masses, rest, moving, _R, np.array([1.0, 0.0, 0.0]))
    np.testing.assert_allclose(h, np.zeros((3, 3)), atol=1e-60)


# --- validation ------------------------------------------------------------


def test_rejects_non_unit_n_hat() -> None:
    masses, rest, moving = _symmetric_pair(1.0)
    with pytest.raises(ValueError, match="unit vector"):
        linear_memory(masses, rest, moving, _R, np.array([0.0, 0.0, 2.0]))


@pytest.mark.parametrize("bad_r", [0.0, -1.0])
def test_rejects_non_positive_r(bad_r: float) -> None:
    masses, rest, moving = _symmetric_pair(1.0)
    with pytest.raises(ValueError, match="positive"):
        linear_memory(masses, rest, moving, bad_r, _N_HAT)


def test_rejects_mismatched_body_counts() -> None:
    with pytest.raises(ValueError, match="bodies"):
        linear_memory(np.array([1.0, 2.0]), np.zeros((3, 3)), np.zeros((3, 3)), _R, _N_HAT)


def test_rejects_float32() -> None:
    """ADR-0002 §5: float32 is rejected, not upcast."""
    masses, rest, moving = _symmetric_pair(1.0)
    with pytest.raises(TypeError, match="float32"):
        linear_memory(masses, rest.astype(np.float32), moving, _R, _N_HAT)
