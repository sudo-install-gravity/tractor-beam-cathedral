"""Unit tests for gwtb.core.backend (T-11.1)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.core.backend import get_backend


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
