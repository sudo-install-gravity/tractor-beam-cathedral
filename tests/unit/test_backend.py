"""Unit tests for gwtb.core.backend (T-11.1, T-11.2)."""

from __future__ import annotations

import time

import numpy as np
import pytest

from gwtb.core.backend import field_grid, get_backend
from gwtb.core.constants import c


def _sum_of_squares(xp: object, arr: np.ndarray) -> float:
    return float(xp.sum(arr * arr))  # type: ignore[attr-defined]


def test_numpy_and_numba_backends_agree() -> None:
    rng = np.random.default_rng(0)
    arr = rng.uniform(-1.0, 1.0, size=1000)

    numpy_backend = get_backend("numpy")
    numba_backend = get_backend("numba")

    plain = _sum_of_squares(numpy_backend.xp, arr)

    @numba_backend.jit
    def _kernel(a: np.ndarray) -> float:
        total = 0.0
        for i in range(a.shape[0]):
            total += a[i] * a[i]
        return total

    jitted = float(_kernel(arr))
    assert jitted == pytest.approx(plain, rel=1e-12)


def test_numpy_jit_is_identity() -> None:
    backend = get_backend("numpy")

    def f(x: int) -> int:
        return x + 1

    assert backend.jit(f) is f


def test_unknown_backend_raises() -> None:
    with pytest.raises(ValueError):
        get_backend("bogus")


def _random_grid_scenario(rng: np.random.Generator, n_sources: int, n_points: int) -> tuple:
    positions = rng.uniform(-10.0, 10.0, size=(n_sources, 3))
    q_ddots = rng.uniform(-1.0, 1.0, size=(n_sources, 3, 3))
    q_ddots = q_ddots + np.transpose(q_ddots, (0, 2, 1))  # symmetric, as physical q_ddot is
    field_points = rng.uniform(1.0e9, 2.0e9, size=(n_points, 3))
    return positions, q_ddots, field_points


def test_field_grid_numba_matches_numpy() -> None:
    """T-11.2: JIT-compiled kernel matches the numpy path to rtol 1e-12."""
    rng = np.random.default_rng(1)
    positions, q_ddots, field_points = _random_grid_scenario(rng, n_sources=3, n_points=64)

    numpy_backend = get_backend("numpy")
    numba_backend = get_backend("numba")

    h_numpy = field_grid(positions, q_ddots, field_points, numpy_backend)
    h_numba = field_grid(positions, q_ddots, field_points, numba_backend)

    assert h_numpy.shape == (64, 3, 3)
    np.testing.assert_allclose(h_numba, h_numpy, rtol=1e-12)


def test_field_grid_numba_matches_field_at() -> None:
    """Cross-check against gwtb.propagate.retarded.field_at's reference formula."""
    from gwtb.propagate.retarded import PointSource, field_at

    rng = np.random.default_rng(2)
    positions, q_ddots, field_points = _random_grid_scenario(rng, n_sources=2, n_points=5)

    numba_backend = get_backend("numba")
    h_grid = field_grid(positions, q_ddots, field_points, numba_backend)

    sources = [
        PointSource(position=positions[a], q_ddot=lambda t, a=a: q_ddots[a]) for a in range(2)
    ]
    for m, fp in enumerate(field_points):
        expected = field_at(sources, fp, 0.0)
        np.testing.assert_allclose(h_grid[m], expected, rtol=1e-12)


def test_field_grid_single_slice_diverges_when_grid_light_crossing_time_is_not_negligible() -> None:
    """field_grid's single-q_ddot-per-grid approximation is only valid when
    the grid's light-crossing time is negligible next to the timescale on
    which q_ddot varies (see the docstring). This constructs a case where it
    is not — a grid spanning several wavelengths of an oscillating source —
    and confirms field_grid then visibly disagrees with the exact per-point
    retardation of field_at/propagate, rather than silently matching it."""
    from gwtb.propagate.retarded import PointSource, field_at

    omega = 1.0

    def q_ddot(t: float) -> np.ndarray:
        q = np.zeros((3, 3))
        q[0, 0] = np.cos(omega * t)
        q[1, 1] = -np.cos(omega * t) / 2.0
        q[2, 2] = -np.cos(omega * t) / 2.0
        return q

    position = np.array([0.0, 0.0, 0.0])
    source = PointSource(position=position, q_ddot=q_ddot)

    wavelength = 2.0 * np.pi * c / omega
    r_vals = np.linspace(1.0e9, 1.0e9 + 1.5 * wavelength, 5)
    field_points = np.stack([np.zeros_like(r_vals), np.zeros_like(r_vals), r_vals], axis=1)

    exact = np.array([field_at([source], fp, 0.0) for fp in field_points])

    q_fixed = np.array([q_ddot(0.0)])
    approx = field_grid(np.array([position]), q_fixed, field_points, get_backend("numpy"))

    max_diff = np.max(np.abs(exact - approx), axis=(1, 2))
    max_scale = np.max(np.abs(exact), axis=(1, 2))
    relative = max_diff / max_scale
    assert np.max(relative) > 0.1, (
        "expected field_grid's fixed-q_ddot approximation to visibly diverge from "
        "field_at's exact per-point retardation over a multi-wavelength grid"
    )


def test_field_grid_numba_10x_faster_on_128_cubed_grid() -> None:
    """T-11.2 AC: >=10x faster than the numpy path on a 128^3 grid.

    Running the numpy (uncompiled) path over the full 2M-point grid would
    make this test itself slow; instead it measures numpy's per-point cost
    on a small subset and numba's per-point cost on the full 128^3 grid, and
    compares throughput. Kernel correctness is asserted separately above.
    """
    rng = np.random.default_rng(3)
    n_full = 128**3
    positions, q_ddots, field_points_full = _random_grid_scenario(rng, n_sources=1, n_points=n_full)

    numba_backend = get_backend("numba")
    field_grid(positions, q_ddots, field_points_full[:8], numba_backend)  # warm up JIT

    t0 = time.perf_counter()
    field_grid(positions, q_ddots, field_points_full, numba_backend)
    numba_per_point = (time.perf_counter() - t0) / n_full

    numpy_backend = get_backend("numpy")
    n_subset = 20000
    t0 = time.perf_counter()
    field_grid(positions, q_ddots, field_points_full[:n_subset], numpy_backend)
    numpy_per_point = (time.perf_counter() - t0) / n_subset

    assert numpy_per_point / numba_per_point >= 10.0
