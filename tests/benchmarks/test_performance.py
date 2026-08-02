"""Benchmark: performance across grid sizes (T-11.6).

AC: records timings; fails if a 128^3 evaluation exceeds 60 s on CPU (the G2
watch threshold — see docs/BACKLOG.md Sprint 6 gate).
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from gwtb.core.backend import field_grid, get_backend

_G2_THRESHOLD_S = 60.0


def _grid(n_per_axis: int, extent: float = 1.0e6) -> np.ndarray:
    axis = np.linspace(-extent, extent, n_per_axis)
    gx, gy, gz = np.meshgrid(axis, axis, axis, indexing="ij")
    return np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=-1)


@pytest.mark.parametrize("n_per_axis", [8, 16, 32])
def test_records_timing_across_grid_sizes(n_per_axis: int) -> None:
    """Records (does not gate on) timings for a range of grid sizes, so a
    scaling trend is visible in the test output even though only the 128^3
    case below carries a hard budget."""
    positions = np.array([[0.0, 0.0, 0.0]])
    q_ddots = np.array([[[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 0.0]]])
    field_points = _grid(n_per_axis)
    backend = get_backend("numba")

    field_grid(positions, q_ddots, field_points[:8], backend)  # warm up JIT

    t0 = time.perf_counter()
    field_grid(positions, q_ddots, field_points, backend)
    elapsed = time.perf_counter() - t0

    print(f"\n{n_per_axis}^3 = {field_points.shape[0]} points: {elapsed:.3f} s")
    assert elapsed >= 0.0  # always true; the print is the record


def test_128_cubed_completes_within_the_g2_threshold() -> None:
    """AC: fails if a 128^3 evaluation exceeds 60 s on CPU."""
    positions = np.array([[0.0, 0.0, 0.0]])
    q_ddots = np.array([[[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 0.0]]])
    field_points = _grid(128)
    backend = get_backend("numba")

    field_grid(positions, q_ddots, field_points[:8], backend)  # warm up JIT, excluded from timing

    t0 = time.perf_counter()
    result = field_grid(positions, q_ddots, field_points, backend)
    elapsed = time.perf_counter() - t0

    print(f"\n128^3 = {field_points.shape[0]} points: {elapsed:.3f} s")
    assert result.shape == (128**3, 3, 3)
    assert elapsed < _G2_THRESHOLD_S, (
        f"128^3 grid took {elapsed:.1f}s, exceeding the G2 watch threshold of {_G2_THRESHOLD_S}s"
    )
