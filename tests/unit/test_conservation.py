"""Unit tests for gwtb.source.conservation (T-2.1)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.source.conservation import ConservationReport, audit

_N_BODIES = 5


def _balanced_configuration(seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    masses = rng.uniform(1.0, 100.0, size=_N_BODIES)
    accelerations = rng.uniform(-10.0, 10.0, size=(_N_BODIES, 3))
    mean_acc = np.einsum("a,ai->i", masses, accelerations) / np.sum(masses)
    accelerations = accelerations - mean_acc
    return masses, accelerations


def test_audit_returns_conservation_report() -> None:
    masses, accelerations = _balanced_configuration(0)
    report = audit(masses, accelerations)
    assert isinstance(report, ConservationReport)
    assert report.net_force.shape == (3,)


def test_audit_true_for_balanced_configuration() -> None:
    for seed in range(20):
        masses, accelerations = _balanced_configuration(seed)
        report = audit(masses, accelerations)
        assert report.is_conserving is True
        assert report.residual < 1e-12


def test_audit_false_for_unbalanced_configuration() -> None:
    rng = np.random.default_rng(99)
    masses = rng.uniform(1.0, 100.0, size=_N_BODIES)
    accelerations = rng.uniform(-10.0, 10.0, size=(_N_BODIES, 3))
    # Deliberately do NOT enforce momentum conservation.
    report = audit(masses, accelerations)
    assert report.is_conserving is False
    assert report.residual > 1e-3


def test_audit_net_force_matches_dipole_second_derivative() -> None:
    masses, accelerations = _balanced_configuration(1)
    report = audit(masses, accelerations)
    expected = np.einsum("a,ai->i", masses, accelerations)
    np.testing.assert_allclose(report.net_force, expected, rtol=1e-15)


def test_audit_residual_scales_linearly_with_imposed_imbalance() -> None:
    """A small, uncompensated perturbation to one body's acceleration should
    move the residual proportionally, for perturbations small relative to the
    configuration's characteristic acceleration (so a_char itself is not
    disturbed by the very imbalance being measured)."""
    masses, accelerations = _balanced_configuration(2)
    a_char = np.max(np.linalg.norm(accelerations, axis=1))
    direction = np.array([1.0, 0.0, 0.0])

    epsilons = np.array([1e-6, 2e-6, 4e-6]) * a_char
    residuals = []
    for eps in epsilons:
        perturbed = accelerations.copy()
        perturbed[0] += eps * direction
        residuals.append(audit(masses, perturbed).residual)

    residuals_arr = np.array(residuals)
    ratios = residuals_arr[1:] / residuals_arr[:-1]
    eps_ratios = epsilons[1:] / epsilons[:-1]
    np.testing.assert_allclose(ratios, eps_ratios, rtol=1e-3)


def test_audit_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError):
        audit([1.0, 2.0, 3.0], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


def test_audit_rejects_float32() -> None:
    masses = np.array([1.0, 2.0], dtype=np.float32)
    accelerations = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float64)
    with pytest.raises(TypeError):
        audit(masses, accelerations)

    masses64 = np.array([1.0, 2.0], dtype=np.float64)
    accelerations32 = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float32)
    with pytest.raises(TypeError):
        audit(masses64, accelerations32)


def test_audit_net_force_is_float64() -> None:
    masses, accelerations = _balanced_configuration(3)
    report = audit(masses, accelerations)
    assert report.net_force.dtype == np.float64
