"""Unit tests for gwtb.propagate.tt_projection (T-1.6)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.propagate.tt_projection import apply_tt, tt_projector


def _random_unit_vectors(rng: np.random.Generator, n: int) -> np.ndarray:
    v = rng.normal(size=(n, 3))
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def _random_symmetric_matrices(rng: np.random.Generator, n: int) -> np.ndarray:
    a = rng.normal(size=(n, 3, 3))
    return a + np.transpose(a, (0, 2, 1))


@pytest.fixture(scope="module")
def n_hats() -> np.ndarray:
    rng = np.random.default_rng(20260726)
    return _random_unit_vectors(rng, 20)


@pytest.fixture(scope="module")
def matrices() -> np.ndarray:
    rng = np.random.default_rng(19740115)
    return _random_symmetric_matrices(rng, 20)


def test_apply_tt_is_idempotent(n_hats: np.ndarray, matrices: np.ndarray) -> None:
    for n_hat in n_hats:
        for m in matrices:
            once = apply_tt(m, n_hat)
            twice = apply_tt(once, n_hat)
            np.testing.assert_allclose(twice, once, rtol=1e-12, atol=1e-12)


def test_apply_tt_result_is_traceless(n_hats: np.ndarray, matrices: np.ndarray) -> None:
    for n_hat in n_hats:
        for m in matrices:
            projected = apply_tt(m, n_hat)
            scale = max(np.max(np.abs(projected)), 1e-300)
            assert abs(np.trace(projected)) <= 1e-12 * scale


def test_apply_tt_result_is_transverse(n_hats: np.ndarray, matrices: np.ndarray) -> None:
    for n_hat in n_hats:
        for m in matrices:
            projected = apply_tt(m, n_hat)
            scale = max(np.max(np.abs(projected)), 1e-300)
            assert np.max(np.abs(n_hat @ projected)) <= 1e-12 * scale


def test_apply_tt_matches_explicit_projector_contraction(
    n_hats: np.ndarray, matrices: np.ndarray
) -> None:
    for n_hat in n_hats:
        lam = tt_projector(n_hat)
        for m in matrices:
            via_apply = apply_tt(m, n_hat)
            via_einsum = np.einsum("ijkl,kl->ij", lam, m)
            np.testing.assert_allclose(via_apply, via_einsum, rtol=1e-12, atol=1e-12)


def test_apply_tt_rejects_non_unit_n_hat() -> None:
    with pytest.raises(ValueError):
        apply_tt(np.eye(3), np.array([1.0, 1.0, 0.0]))


def test_tt_projector_rejects_non_unit_n_hat() -> None:
    with pytest.raises(ValueError):
        tt_projector(np.array([2.0, 0.0, 0.0]))
