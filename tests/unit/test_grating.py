"""Unit tests for gwtb.array.grating (T-5.8)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.array.geometry import linear_array
from gwtb.array.grating import has_grating_lobes, max_spacing


def test_max_spacing_hemisphere_scan_at_1hz() -> None:
    c = 299792458.0
    wavelength = c / 1.0
    d_max = max_spacing(wavelength, scan_angle_max=np.pi / 2.0)
    assert d_max == pytest.approx(1.5e8, rel=1e-3)


def test_max_spacing_broadside_only_is_full_wavelength() -> None:
    d_max = max_spacing(wavelength=1.0, scan_angle_max=0.0)
    assert d_max == pytest.approx(1.0, rel=1e-12)


def test_has_grating_lobes_true_for_oversized_spacing() -> None:
    geometry = linear_array(4, spacing=2.0)
    assert has_grating_lobes(geometry, wavelength=1.0, scan_angle_max=0.0) is True


def test_has_grating_lobes_false_for_half_wavelength_spacing() -> None:
    geometry = linear_array(4, spacing=0.4)
    assert has_grating_lobes(geometry, wavelength=1.0, scan_angle_max=np.pi / 2.0) is False
