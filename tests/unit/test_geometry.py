"""Unit tests for gwtb.array.geometry (T-5.5, T-5.6, T-5.7)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.array.geometry import linear_array, planar_array, sparse_array


def test_linear_array_count_and_spacing() -> None:
    pos = linear_array(8, 2.5)
    assert pos.shape == (8, 3)
    x = pos[:, 0]
    diffs = np.diff(np.sort(x))
    np.testing.assert_allclose(diffs, 2.5, rtol=1e-12)


def test_linear_array_centered_on_origin() -> None:
    pos = linear_array(7, 1.0)
    assert np.mean(pos[:, 0]) == pytest.approx(0.0, abs=1e-12)
    pos_even = linear_array(8, 1.0)
    assert np.mean(pos_even[:, 0]) == pytest.approx(0.0, abs=1e-12)


def test_planar_array_element_count() -> None:
    pos = planar_array(4, 5, 1.0, 2.0)
    assert pos.shape == (20, 3)


def test_planar_array_coplanar() -> None:
    pos = planar_array(3, 3, 0.5, 0.5)
    np.testing.assert_allclose(pos[:, 2], 0.0, atol=1e-12)


def test_sparse_array_reproducible_for_fixed_seed() -> None:
    a = sparse_array(50, aperture=100.0, seed=42)
    b = sparse_array(50, aperture=100.0, seed=42)
    np.testing.assert_array_equal(a, b)


def test_sparse_array_different_seed_differs() -> None:
    a = sparse_array(50, aperture=100.0, seed=1)
    b = sparse_array(50, aperture=100.0, seed=2)
    assert not np.array_equal(a, b)


def test_sparse_array_within_aperture() -> None:
    pos = sparse_array(200, aperture=10.0, seed=7)
    r = np.linalg.norm(pos[:, :2], axis=1)
    assert np.all(r <= 5.0 + 1e-9)
