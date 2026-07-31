"""Unit tests for gwtb.propagate.retarded (T-6.7)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.core.constants import c
from gwtb.propagate.retarded import PointSource, field_at, propagate
from gwtb.source.quadrupole import strain_tt


def _oscillating_q_ddot(omega: float, amp: float) -> callable:
    def q_ddot(t: float) -> np.ndarray:
        q = np.zeros((3, 3))
        q[0, 0] = amp * np.cos(omega * t)
        q[1, 1] = -amp * np.cos(omega * t) / 2.0
        q[2, 2] = -amp * np.cos(omega * t) / 2.0
        return q

    return q_ddot


def test_single_source_reproduces_strain_tt_exactly() -> None:
    q_func = _oscillating_q_ddot(omega=1.0, amp=1.0)
    position = np.array([0.0, 0.0, 0.0])
    field_point = np.array([0.0, 0.0, 1.0e10])
    time = 123.4

    source = PointSource(position=position, q_ddot=q_func)
    h = field_at([source], field_point, time)

    r = float(np.linalg.norm(field_point - position))
    n_hat = (field_point - position) / r
    expected = strain_tt(q_func(time - r / c), r, n_hat)
    np.testing.assert_allclose(h, expected, rtol=1e-12)


def test_per_element_retardation_differs_from_array_center_retardation() -> None:
    """A test where using a single array-center retarded time instead of
    per-element retarded time gives a detectably different answer."""
    omega = 2.0 * np.pi * c / 10.0  # wavelength ~10 m: sensitive to path-length differences
    q_func = _oscillating_q_ddot(omega=omega, amp=1.0)

    # Elements separated along the line of sight, so their distances to the
    # field point (and hence retarded times) genuinely differ.
    d = 5.0  # element half-separation, m -- comparable to the wavelength
    pos_a = np.array([0.0, 0.0, d])
    pos_b = np.array([0.0, 0.0, -d])
    field_point = np.array([0.0, 0.0, 1.0e6])
    time = 0.0

    source_a = PointSource(position=pos_a, q_ddot=q_func)
    source_b = PointSource(position=pos_b, q_ddot=q_func)
    h_per_element = field_at([source_a, source_b], field_point, time)

    # Naive array-center retardation: both elements evaluated at the same
    # (array-center) retarded time, but each still at its own distance/n_hat.
    r_center = float(np.linalg.norm(field_point))
    t_ret_center = time - r_center / c
    h_center = np.zeros((3, 3))
    for source in (source_a, source_b):
        r = float(np.linalg.norm(field_point - source.position))
        n_hat = (field_point - source.position) / r
        h_center += strain_tt(q_func(t_ret_center), r, n_hat)

    assert np.max(np.abs(h_per_element - h_center)) > 1e-3 * np.max(np.abs(h_per_element))


def test_field_at_rejects_field_point_at_source() -> None:
    q_func = _oscillating_q_ddot(omega=1.0, amp=1.0)
    source = PointSource(position=np.zeros(3), q_ddot=q_func)
    with pytest.raises(ValueError):
        field_at([source], np.zeros(3), 0.0)


def test_field_at_rejects_empty_sources() -> None:
    with pytest.raises(ValueError):
        field_at([], np.array([0.0, 0.0, 1.0]), 0.0)


def test_propagate_amplitude_scales_as_one_over_r() -> None:
    """T-6.8: amplitude scales as 1/r to rtol 1e-9 over r in [1e9, 6e12] m.

    Uses a time-independent q_ddot so retardation (which varies hugely across
    this radius range) cannot alias into an apparent amplitude change; that
    isolates the 1/r falloff this AC is actually about.
    """
    q_func = _oscillating_q_ddot(omega=0.0, amp=1.0)
    source = PointSource(position=np.zeros(3), q_ddot=q_func)

    radii = np.geomspace(1.0e9, 6.0e12, 8)
    field_points = np.stack([np.zeros_like(radii), np.zeros_like(radii), radii], axis=1)
    times = np.array([0.0])

    h = propagate([source], field_points, times)
    assert h.shape == (radii.shape[0], 1, 3, 3)
    assert h.dtype == np.float64

    amplitude = np.max(np.abs(h[:, 0]).reshape(radii.shape[0], -1), axis=1)
    np.testing.assert_allclose(amplitude * radii, amplitude[0] * radii[0], rtol=1e-9)


def test_propagate_matches_field_at_per_point_and_time() -> None:
    q_func = _oscillating_q_ddot(omega=1.0, amp=1.0)
    source = PointSource(position=np.array([1.0, 0.0, 0.0]), q_ddot=q_func)

    field_points = np.array([[0.0, 0.0, 1.0e10], [0.0, 1.0e10, 0.0]])
    times = np.array([0.0, 10.0])

    h = propagate([source], field_points, times)
    for m, field_point in enumerate(field_points):
        for n, time in enumerate(times):
            expected = field_at([source], field_point, float(time))
            np.testing.assert_allclose(h[m, n], expected, rtol=1e-12)
