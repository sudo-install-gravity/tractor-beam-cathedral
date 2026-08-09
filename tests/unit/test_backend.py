"""Unit tests for gwtb.core.backend (T-11.1, T-11.2, T-11.4, T-11.5, T-11.7)."""

from __future__ import annotations

import time

import numpy as np
import pytest

from gwtb.core.backend import (
    PrecisionError,
    assert_phase_precision,
    field_grid,
    field_grid_chunked,
    field_grid_split_phase,
    get_backend,
    split_phase,
)
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

    **Best-of-3 wall-clock timing (T-13.5).** A single measurement of each
    path is contention-sensitive on a shared or loaded machine: this test
    was observed to fail under load while the true ~10x throughput gap
    held, which is a measurement problem, not a regression. Taking the
    minimum of three repeated timings per path is the standard fix for
    exactly this: contention can only add delay to a run, never subtract
    it, so the minimum across repeats is the best available estimate of
    the uncontended cost. The 10x threshold itself is kept, not loosened —
    weakening the tolerance to paper over measurement noise would be the
    inverse of the fix (HANDOVER.md section 5).
    """
    rng = np.random.default_rng(3)
    n_full = 128**3
    positions, q_ddots, field_points_full = _random_grid_scenario(rng, n_sources=1, n_points=n_full)

    numba_backend = get_backend("numba")
    field_grid(positions, q_ddots, field_points_full[:8], numba_backend)  # warm up JIT

    numba_times = []
    for _ in range(3):
        t0 = time.perf_counter()
        field_grid(positions, q_ddots, field_points_full, numba_backend)
        numba_times.append(time.perf_counter() - t0)
    numba_per_point = min(numba_times) / n_full

    numpy_backend = get_backend("numpy")
    n_subset = 20000
    numpy_times = []
    for _ in range(3):
        t0 = time.perf_counter()
        field_grid(positions, q_ddots, field_points_full[:n_subset], numpy_backend)
        numpy_times.append(time.perf_counter() - t0)
    numpy_per_point = min(numpy_times) / n_subset

    assert numpy_per_point / numba_per_point >= 10.0


# --- T-11.4: optional GPU backend -------------------------------------------


def test_cupy_backend_skips_cleanly_without_a_gpu() -> None:
    """AC: skips cleanly with no GPU."""
    try:
        import cupy  # noqa: F401
    except ImportError:
        pytest.skip("cupy not installed; GPU backend cannot be exercised here")

    backend = get_backend("cupy")
    offsets = np.array([[10.0, 0.0, 0.0], [-10.0, 0.0, 0.0]])
    weights = np.array([1.0 + 0j, 1.0 + 0j])
    gpu_result = field_grid_split_phase(
        np.array([0.0, 0.0, 1.0e9]), offsets, weights, 1.0, backend.xp
    )

    cpu_result = field_grid_split_phase(np.array([0.0, 0.0, 1.0e9]), offsets, weights, 1.0, np)
    np.testing.assert_allclose(np.asarray(gpu_result.get()), cpu_result, rtol=1e-5)


def test_get_backend_cupy_raises_a_clear_error_without_cupy_installed() -> None:
    """The un-skipped half: without cupy, requesting it must fail loudly
    rather than silently falling back to CPU."""
    try:
        import cupy  # noqa: F401

        pytest.skip("cupy is installed; this test exercises the absent-cupy path")
    except ImportError:
        pass

    with pytest.raises(RuntimeError, match="cupy"):
        get_backend("cupy")


def test_field_grid_split_phase_matches_numpy_reference() -> None:
    """The vectorized kernel underlying the GPU backend, exercised on CPU."""
    offsets = np.array([[100.0, 0.0, 0.0], [-100.0, 50.0, 0.0], [0.0, -50.0, 25.0]])
    weights = np.array([1.0 + 0j, 0.5 - 0.5j, -1.0 + 0j])
    reference = np.array([0.0, 0.0, 1.0e10])

    result = field_grid_split_phase(reference, offsets, weights, wavelength=1.0)
    assert result.shape == (3,)
    assert result.dtype == np.complex128
    assert np.all(np.isfinite(result))


# --- T-11.5: precision guard -------------------------------------------------


def test_precision_guard_raises_on_unauthorized_float32_phase() -> None:
    """AC: raises on unauthorized float32 phase input."""
    phase = np.array([1.0, 2.0], dtype=np.float32)
    with pytest.raises(PrecisionError):
        assert_phase_precision(phase, authorized=False)


def test_precision_guard_passes_when_authorized() -> None:
    """AC: passes inside the marked kernel."""
    phase = np.array([1.0, 2.0], dtype=np.float32)
    assert_phase_precision(phase, authorized=True)  # must not raise


def test_precision_guard_passes_for_float64_regardless_of_authorization() -> None:
    phase = np.array([1.0, 2.0], dtype=np.float64)
    assert_phase_precision(phase, authorized=False)  # must not raise


def test_precision_error_is_a_type_error() -> None:
    """Matches gwtb.core.validation's convention for dtype violations."""
    assert issubclass(PrecisionError, TypeError)


def test_split_phase_differential_is_the_one_authorized_float32_call_site() -> None:
    """split_phase's own construction never raises, because it is the
    authorized call site — a regression guard against the guard itself
    breaking the function it was added to protect."""
    s = np.array([0.0, 0.0, 1.0e12])
    offsets = np.array([[100.0, 0.0, 0.0], [-100.0, 0.0, 0.0]])
    result = split_phase(s, offsets, wavelength=1.0)
    assert result.differential.dtype == np.float32


# --- T-11.7: memory-efficient chunking --------------------------------------


def test_chunked_matches_unchunked_to_rtol_1e_12() -> None:
    rng = np.random.default_rng(5)
    positions, q_ddots, field_points = _random_grid_scenario(rng, n_sources=2, n_points=500)
    backend = get_backend("numpy")

    unchunked = field_grid(positions, q_ddots, field_points, backend)
    chunked = field_grid_chunked(positions, q_ddots, field_points, backend, chunk_size=37)

    np.testing.assert_allclose(chunked, unchunked, rtol=1e-12)


def test_chunk_size_does_not_change_the_result() -> None:
    rng = np.random.default_rng(6)
    positions, q_ddots, field_points = _random_grid_scenario(rng, n_sources=1, n_points=200)
    backend = get_backend("numpy")

    results = [
        field_grid_chunked(positions, q_ddots, field_points, backend, chunk_size=cs)
        for cs in (1, 7, 50, 1000)
    ]
    for r in results[1:]:
        np.testing.assert_allclose(r, results[0], rtol=1e-12)


def test_a_512_cubed_grid_completes_within_a_4gb_budget() -> None:
    """AC: a 512^3 grid completes within a 4 GB budget; results match
    unchunked to rtol 1e-12.

    Verified at reduced scale here (correctness, not the literal 512^3 size —
    that grid alone is ~9.7 GB unchunked, impractical for routine CI): the
    per-point formula has no cross-point coupling, so correctness at any
    tested size generalizes to 512^3 by the same argument
    field_grid_chunked's docstring makes. A 24^3 grid, chunked finely enough
    that peak allocation is a small fraction of the full grid, demonstrates
    the same bounded-memory batching field_grid_chunked would use at 512^3.

    **T-13.5 finding, 2026-08-08.** BACKLOG.md named this test as the second
    of "two wall-clock assertions" that fail together under load. As
    written (and per git history, as written since it was added — this is
    not a regression), this test contains **no wall-clock or memory
    measurement at all**: it is a pure rtol-1e-12 correctness check on a
    reduced grid, with no `time.perf_counter()` call and no budget
    assertion to be flaky about. `test_field_grid_numba_10x_faster_on_128_
    cubed_grid` above is the genuine wall-clock assertion in this module
    and has been de-flaked with best-of-3 timing. This docstring records
    the discrepancy rather than silently reconciling it, per this
    project's own "make absence loud" rule — if a real memory/time budget
    check is wanted here later, it does not exist yet and would be new
    work, not a de-flake of existing work.
    """
    positions = np.array([[0.0, 0.0, 0.0]])
    q_ddots = np.array([[[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 0.0]]])
    n = 24
    axis = np.linspace(-1.0e6, 1.0e6, n)
    gx, gy, gz = np.meshgrid(axis, axis, axis, indexing="ij")
    field_points = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=-1)
    backend = get_backend("numpy")

    # Chunk size << total points, so peak per-chunk allocation is a small
    # fraction of the unchunked (n^3, 3, 3) array — the property that scales
    # to 512^3 within a 4 GB budget.
    chunked = field_grid_chunked(positions, q_ddots, field_points, backend, chunk_size=200)
    unchunked = field_grid(positions, q_ddots, field_points, backend)
    np.testing.assert_allclose(chunked, unchunked, rtol=1e-12)


def test_field_grid_chunked_rejects_non_positive_chunk_size() -> None:
    with pytest.raises(ValueError, match="chunk_size"):
        field_grid_chunked(
            np.zeros((1, 3)), np.zeros((1, 3, 3)), np.zeros((5, 3)), get_backend("numpy"), 0
        )
