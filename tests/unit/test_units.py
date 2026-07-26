"""Unit tests for gwtb.core.units (T-1.2)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.core.units import DEFAULT_REFERENCE, StrainScale


def test_round_trip_identity_over_strain_range() -> None:
    scale = StrainScale()
    x = np.logspace(-45, -35, 50)
    round_tripped = scale.from_scaled(scale.to_scaled(x))
    np.testing.assert_allclose(round_tripped, x, rtol=1e-15)


def test_to_scaled_maps_reference_to_one_exactly() -> None:
    scale = StrainScale()
    assert scale.to_scaled(1e-40) == 1.0


def test_from_scaled_maps_one_to_reference() -> None:
    scale = StrainScale()
    assert scale.from_scaled(1.0) == DEFAULT_REFERENCE


def test_default_reference_value() -> None:
    assert StrainScale().reference == 1e-40


def test_custom_reference() -> None:
    scale = StrainScale(reference=1e-21)
    assert scale.to_scaled(1e-21) == 1.0
    assert scale.from_scaled(2.0) == pytest.approx(2e-21, rel=1e-15)


def test_rejects_zero_reference() -> None:
    with pytest.raises(ValueError):
        StrainScale(reference=0.0)


def test_rejects_negative_reference() -> None:
    with pytest.raises(ValueError):
        StrainScale(reference=-1e-40)


def test_rejects_non_finite_reference() -> None:
    with pytest.raises(ValueError):
        StrainScale(reference=float("inf"))
    with pytest.raises(ValueError):
        StrainScale(reference=float("nan"))


def test_accepts_scalar_and_array() -> None:
    scale = StrainScale()
    scalar_result = scale.to_scaled(1e-40)
    assert isinstance(scalar_result, float)

    array_result = scale.to_scaled(np.array([1e-40, 2e-40]))
    assert isinstance(array_result, np.ndarray)
    np.testing.assert_allclose(array_result, [1.0, 2.0], rtol=1e-15)
