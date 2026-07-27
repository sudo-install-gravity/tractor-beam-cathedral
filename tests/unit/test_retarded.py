"""Unit tests for gwtb.propagate.retarded (T-6.7)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.core.constants import c
from gwtb.propagate.retarded import PointSource, field_at
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
