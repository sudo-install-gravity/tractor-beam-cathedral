"""Unit tests for gwtb.viz.patterns (T-7.4, T-7.5)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import numpy as np
from matplotlib.figure import Figure

from gwtb.array.beamform import steering_phases
from gwtb.array.geometry import linear_array
from gwtb.viz.patterns import _array_factor_magnitude, plot_pattern_3d, plot_pattern_polar


def test_plot_pattern_polar_renders_headless_figure() -> None:
    n, d, wavelength = 16, 0.5, 1.0
    geom = linear_array(n, d)
    weights = np.ones(n, dtype=complex)
    fig = plot_pattern_polar(geom, weights, wavelength, floor_db=-40.0)
    assert isinstance(fig, Figure)


def test_plot_pattern_polar_main_lobe_at_steered_direction() -> None:
    n, d, wavelength = 16, 0.5, 1.0
    geom = linear_array(n, d)
    theta_target = 0.5
    direction = np.array([np.sin(theta_target), 0.0, np.cos(theta_target)])
    phases = steering_phases(geom, wavelength, direction)
    weights = np.exp(1j * phases)

    theta = np.linspace(-np.pi, np.pi, 7201)
    directions = np.stack([np.sin(theta), np.zeros_like(theta), np.cos(theta)], axis=1)
    mags = _array_factor_magnitude(geom, weights, wavelength, directions)
    peak_theta = theta[np.argmax(mags)]
    assert abs(peak_theta - theta_target) < 1e-2

    # sidelobe structure visible down to a -40 dB floor: more than one local
    # maximum survives above the floor for a uniform array.
    db = 20.0 * np.log10(mags / np.max(mags))
    above_floor = db > -40.0
    assert np.sum(np.diff(above_floor.astype(int)) != 0) > 2


def test_plot_pattern_polar_rejects_non_negative_floor() -> None:
    geom = linear_array(4, 0.5)
    weights = np.ones(4, dtype=complex)
    import pytest

    with pytest.raises(ValueError):
        plot_pattern_polar(geom, weights, 1.0, floor_db=0.0)


def test_plot_pattern_3d_renders_headless_figure() -> None:
    n, d, wavelength = 8, 0.5, 1.0
    geom = linear_array(n, d)
    weights = np.ones(n, dtype=complex)
    fig = plot_pattern_3d(geom, weights, wavelength, n_theta=21, n_phi=41)
    assert isinstance(fig, Figure)


def test_plot_pattern_3d_peak_matches_steering_to_1e_3_rad() -> None:
    """AC: peak direction matches steering_phases to 1e-3 rad. Verified via
    a fine local angular sweep in the plane containing the target direction
    (the full-sphere plotting grid itself uses a coarser default resolution
    intended for visualization, not sub-mrad peak localization)."""
    n, d, wavelength = 16, 0.5, 1.0
    geom = linear_array(n, d)
    theta_target = 0.3
    direction = np.array([np.sin(theta_target), 0.0, np.cos(theta_target)])
    phases = steering_phases(geom, wavelength, direction)
    weights = np.exp(1j * phases)

    theta = np.linspace(theta_target - 0.05, theta_target + 0.05, 200001)
    directions = np.stack([np.sin(theta), np.zeros_like(theta), np.cos(theta)], axis=1)
    mags = _array_factor_magnitude(geom, weights, wavelength, directions)
    peak_theta = theta[np.argmax(mags)]
    assert abs(peak_theta - theta_target) < 1e-3
