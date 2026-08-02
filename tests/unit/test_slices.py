"""Unit tests for gwtb.viz.slices (T-7.1, T-7.2, T-7.3)."""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure

from gwtb.viz.slices import animate_propagation, extract_slice, plot_strain_slice


def _linear_field(position: np.ndarray) -> np.ndarray:
    """A simple, exactly-known field for shape/coordinate testing."""
    h = np.zeros((3, 3))
    h[0, 0] = position[0]
    h[1, 1] = -position[0]
    return h


# --- T-7.1: extract_slice ----------------------------------------------------


def test_extract_slice_shape() -> None:
    """AC: correct shape."""
    s = extract_slice(_linear_field, "xy", extent=10.0, resolution=15)
    assert s.coord1.shape == (15,)
    assert s.coord2.shape == (15,)
    assert s.values.shape == (15, 15, 3, 3)


def test_extract_slice_coordinates_match_the_requested_extent() -> None:
    """AC: coordinates match the requested extent to rtol 1e-12."""
    extent = 3.7e6
    s = extract_slice(_linear_field, "xz", extent=extent, resolution=21)
    assert s.coord1[0] == pytest.approx(-extent, rel=1e-12)
    assert s.coord1[-1] == pytest.approx(extent, rel=1e-12)
    assert s.coord2[0] == pytest.approx(-extent, rel=1e-12)
    assert s.coord2[-1] == pytest.approx(extent, rel=1e-12)


def test_extract_slice_evaluates_the_field_correctly() -> None:
    s = extract_slice(_linear_field, "xy", extent=10.0, resolution=5)
    for a, x in enumerate(s.coord1):
        for b in range(len(s.coord2)):
            assert s.values[a, b, 0, 0] == pytest.approx(x)


def test_extract_slice_fixed_coordinate_is_recorded() -> None:
    s = extract_slice(_linear_field, "xy", extent=10.0, resolution=5, fixed_coordinate=42.0)
    assert s.fixed_coordinate == 42.0


def test_extract_slice_plane_axes_are_correct() -> None:
    """Each named plane must vary the right two axes and hold the third fixed."""

    def probe(position: np.ndarray) -> np.ndarray:
        h = np.zeros((3, 3))
        h[0, 0], h[1, 1], h[2, 2] = position
        return h

    for plane, fixed_axis in (("xy", 2), ("xz", 1), ("yz", 0)):
        s = extract_slice(probe, plane, extent=5.0, resolution=4, fixed_coordinate=9.0)
        fixed_values = s.values[:, :, fixed_axis, fixed_axis]
        np.testing.assert_allclose(fixed_values, 9.0)


def test_extract_slice_rejects_unknown_plane() -> None:
    with pytest.raises(ValueError, match="plane"):
        extract_slice(_linear_field, "bogus", 10.0, 5)


def test_extract_slice_rejects_too_small_resolution() -> None:
    with pytest.raises(ValueError, match="resolution"):
        extract_slice(_linear_field, "xy", 10.0, 1)


# --- T-7.2: plot_strain_slice ------------------------------------------------


def test_plot_strain_slice_renders_headless() -> None:
    """AC: figure renders headless (Agg)."""
    s = extract_slice(_linear_field, "xy", extent=10.0, resolution=11)
    fig = plot_strain_slice(s)
    assert isinstance(fig, Figure)
    plt.close(fig)


def test_plot_strain_slice_colorbar_is_symmetric_about_zero() -> None:
    """AC: colorbar symmetric about zero."""
    s = extract_slice(_linear_field, "xy", extent=10.0, resolution=11)
    fig = plot_strain_slice(s)
    im = fig.axes[0].collections[0]
    vmin, vmax = im.get_clim()
    assert vmin == pytest.approx(-vmax, rel=1e-12)
    plt.close(fig)


def test_plot_strain_slice_zero_field_does_not_crash() -> None:
    s = extract_slice(lambda p: np.zeros((3, 3)), "xy", extent=10.0, resolution=5)
    fig = plot_strain_slice(s)
    plt.close(fig)


# --- T-7.3: animate_propagation ----------------------------------------------


def _time_field(position: np.ndarray, t: float) -> np.ndarray:
    h = np.zeros((3, 3))
    h[0, 0] = position[0] * np.cos(t)
    h[1, 1] = -h[0, 0]
    return h


def test_animate_propagation_frame_count_matches_times(tmp_path) -> None:
    """AC: frame count matches the time array."""
    times = np.linspace(0.0, 1.0, 5)
    path = str(tmp_path / "anim.gif")
    n_frames = animate_propagation(_time_field, "xy", 10.0, 6, times, path)
    assert n_frames == len(times)


def test_animate_propagation_writes_a_headless_gif(tmp_path) -> None:
    """AC: writes a gif headless."""
    times = np.linspace(0.0, 1.0, 3)
    path = str(tmp_path / "anim.gif")
    animate_propagation(_time_field, "xy", 10.0, 5, times, path)
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0


def test_animate_propagation_rejects_empty_times(tmp_path) -> None:
    with pytest.raises(ValueError, match="times"):
        animate_propagation(_time_field, "xy", 10.0, 5, np.array([]), str(tmp_path / "x.gif"))
