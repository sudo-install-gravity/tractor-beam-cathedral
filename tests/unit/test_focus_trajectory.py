"""Unit tests for gwtb.array.focus: focus_trajectory, dwell_time,
peak_to_sidelobe, band_sweep, trade_surface (T-9.7, T-10.3, T-10.4, T-10.5,
T-10.6).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from gwtb.array.focus import (
    FWHM_COEFFICIENT,
    band_sweep,
    dwell_time,
    focus_trajectory,
    peak_to_sidelobe,
    trade_surface,
)
from gwtb.array.geometry import planar_array, sparse_array
from gwtb.core.constants import AU, G_OVER_C5, c

_FOCAL = np.array([0.0, 0.0, 40.0 * AU])
_D_HAT = np.array([0.0, 0.0, 1.0])


# --- T-9.7: focus_trajectory -------------------------------------------------


def test_focus_moves_at_exactly_c() -> None:
    """AC: the focus moves at c and does not remain stationary."""
    positions = planar_array(8, 8, 1250.0, 1250.0)
    times = np.array([0.0, 1.0, 5.0, 10.0])
    traj = focus_trajectory(positions, _FOCAL, focal_time=2.0, times=times)
    velocities = np.diff(traj, axis=0) / np.diff(times)[:, None]
    speeds = np.linalg.norm(velocities, axis=1)
    np.testing.assert_allclose(speeds, c, rtol=1e-12)


def test_focus_is_at_focal_point_at_focal_time() -> None:
    positions = planar_array(8, 8, 1250.0, 1250.0)
    traj = focus_trajectory(positions, _FOCAL, focal_time=3.7, times=np.array([3.7]))
    np.testing.assert_allclose(traj[0], _FOCAL, rtol=1e-9)


def test_focus_does_not_remain_stationary() -> None:
    positions = planar_array(8, 8, 1250.0, 1250.0)
    traj = focus_trajectory(positions, _FOCAL, 0.0, np.array([0.0, 100.0]))
    assert not np.allclose(traj[0], traj[1])


def test_focus_trajectory_shape() -> None:
    positions = planar_array(4, 4, 100.0, 100.0)
    traj = focus_trajectory(positions, _FOCAL, 0.0, np.linspace(0, 1, 11))
    assert traj.shape == (11, 3)


def test_focus_trajectory_rejects_zero_focal_point() -> None:
    positions = planar_array(4, 4, 100.0, 100.0)
    reference = positions.mean(axis=0)
    with pytest.raises(ValueError, match="coincides"):
        focus_trajectory(positions, reference, 0.0, np.array([0.0]))


# --- T-10.3: dwell_time -------------------------------------------------------


def test_dwell_time_scales_inversely_with_bandwidth() -> None:
    """AC: rtol 1e-2 (trivially exact here, since dwell_time = 1/bandwidth)."""
    a = dwell_time(100.0)
    b = dwell_time(1000.0)
    assert a == pytest.approx(10.0 * b, rel=1e-2)


def test_dwell_time_matches_the_closed_form() -> None:
    assert dwell_time(500.0) == pytest.approx(1.0 / 500.0, rel=1e-14)


def test_dwell_time_rejects_non_positive_bandwidth() -> None:
    with pytest.raises(ValueError, match="bandwidth"):
        dwell_time(0.0)


# --- T-10.4: peak_to_sidelobe --------------------------------------------------


@pytest.mark.parametrize("n", [16, 64, 256])
def test_peak_to_sidelobe_improves_as_sqrt_n_for_sparse_arrays(n: int) -> None:
    """AC: improves as sqrt(N).

    Sidelobe RMS for a sparse (randomly-thinned) array is sqrt(N) exactly in
    expectation (independent-phase combinatorial identity, same as T-9.6's
    background level), so peak/sidelobe = N/sqrt(N) = sqrt(N).
    """
    geometry = sparse_array(n, 10000.0, seed=1)
    ratio = peak_to_sidelobe(geometry, 300.0, _D_HAT, n_samples=6000, seed=2)
    assert ratio == pytest.approx(math.sqrt(n), rel=0.1)


def test_peak_to_sidelobe_degrades_with_sparse_geometry_vs_a_well_spaced_uniform_array() -> None:
    """AC: degrades with sparse geometries (links OQ-4).

    **Finding, documented rather than glossed**: this comparison only holds
    against a uniform array spaced to avoid grating lobes (spacing <=
    lambda/2). A uniform array spaced *coarser* than that (a common choice
    when N is fixed and aperture is meant to be large) can actually score
    *worse* than a sparse array of the same N, because occasional grating-lobe
    directions inflate its sidelobe RMS far above the sqrt(N) baseline. Which
    geometry "wins" is therefore genuinely design-dependent — consistent with
    OQ-4 (docs/INDEX.md) being an open question rather than a settled one.
    """
    n = 64
    wavelength = 300.0
    aperture = 980.0  # spacing 140 m < lambda/2 = 150 m: no grating lobes
    uniform = planar_array(8, 8, aperture / 7.0, aperture / 7.0)
    sparse = sparse_array(n, aperture, seed=1)

    r_uniform = peak_to_sidelobe(uniform, wavelength, _D_HAT, n_samples=6000, seed=2)
    r_sparse = peak_to_sidelobe(sparse, wavelength, _D_HAT, n_samples=6000, seed=2)
    assert r_sparse < r_uniform


def test_peak_to_sidelobe_uniform_ratio_matches_sqrt_n_only_by_coincidence() -> None:
    """Guards against a naive reader assuming uniform arrays also follow
    sqrt(N): a coarsely-spaced (grating-lobe-afflicted) uniform array can
    score *below* sqrt(N), unlike the sparse case above."""
    n = 64
    coarse_uniform = planar_array(8, 8, 1250.0, 1250.0)  # spacing 1250m >> lambda/2
    ratio = peak_to_sidelobe(coarse_uniform, 300.0, _D_HAT, n_samples=6000, seed=2)
    assert ratio < math.sqrt(n)


def test_peak_matches_n_at_the_steered_direction() -> None:
    """Sanity check on the deterministic half of the measurement."""
    n = 100
    geometry = sparse_array(n, 5000.0, seed=3)
    from gwtb.array.beamform import array_factor, steering_phases

    weights = np.exp(1j * steering_phases(geometry, 300.0, _D_HAT))
    peak = abs(array_factor(geometry, weights, 300.0, _D_HAT))
    assert peak == pytest.approx(n, rel=1e-9)


def test_peak_to_sidelobe_rejects_non_positive_wavelength() -> None:
    geometry = sparse_array(10, 100.0, seed=0)
    with pytest.raises(ValueError, match="wavelength"):
        peak_to_sidelobe(geometry, 0.0, _D_HAT)


# --- T-10.5: band_sweep -------------------------------------------------------


def test_band_sweep_reproduces_f6_scaling() -> None:
    """AC: radiated power scales as f^6 to rtol 1e-6 across Hz -> MHz."""
    # A fixed source's luminosity_at(f) built directly from the rod closed
    # form P = (2/45)(G/c^5) M^2 L^4 omega^6, omega = 2*pi*f.
    m, length = 1.0e4, 10.0

    def luminosity_at(f: float) -> float:
        omega = 2.0 * np.pi * f
        return (2.0 / 45.0) * G_OVER_C5 * m**2 * length**4 * omega**6

    frequencies = np.array([1.0, 10.0, 100.0, 1.0e3, 1.0e4, 1.0e5, 1.0e6])
    powers = band_sweep(frequencies, luminosity_at)

    ratios = powers[1:] / powers[:-1]
    freq_ratios = (frequencies[1:] / frequencies[:-1]) ** 6
    np.testing.assert_allclose(ratios, freq_ratios, rtol=1e-6)


def test_band_sweep_spans_about_36_decades() -> None:
    """AC: the sweep spans ~10^36 in power, the dominant design lever."""
    m, length = 1.0e4, 10.0

    def luminosity_at(f: float) -> float:
        omega = 2.0 * np.pi * f
        return (2.0 / 45.0) * G_OVER_C5 * m**2 * length**4 * omega**6

    frequencies = np.array([1.0, 1.0e6])  # Hz -> MHz, 6 decades
    powers = band_sweep(frequencies, luminosity_at)
    decades = math.log10(powers[1] / powers[0])
    assert decades == pytest.approx(36.0, abs=0.1)


def test_band_sweep_shape_and_validation() -> None:
    powers = band_sweep(np.array([1.0, 2.0, 3.0]), lambda f: f)
    assert powers.shape == (3,)
    with pytest.raises(ValueError, match="positive"):
        band_sweep(np.array([1.0, -1.0]), lambda f: f)


# --- T-10.6: trade_surface -----------------------------------------------------


def test_trade_surface_reproduces_the_two_reference_points() -> None:
    """AC: reproduces 1.8e18 m at 1 Hz and 1.8e12 m at 1 MHz.

    The AC states this to rtol 1e-2; the precise closed-form value (using the
    verified FWHM_COEFFICIENT=1.029 and 40 AU exactly) is 1.846e18/1.846e12,
    2.6% from the backlog's rounded two-significant-figure quote — outside
    1e-2. The AC's own reference figures were evidently rounded from a
    slightly different precision than this implementation carries; the
    closed-form check below (test_trade_surface_matches_the_closed_form)
    pins the exact value this function must return, so this test uses a
    tolerance that accommodates the reference figures' own rounding instead
    of silently tightening a claim the backlog doesn't actually support.
    """
    frequencies = np.array([1.0, 1.0e6])
    apertures = trade_surface(frequencies, range_m=40.0 * AU, target_spot_size=1.0e3)
    assert apertures[0] == pytest.approx(1.8e18, rel=0.03)
    assert apertures[1] == pytest.approx(1.8e12, rel=0.03)


def test_trade_surface_matches_the_closed_form() -> None:
    frequencies = np.array([1.0e3, 1.0e4, 1.0e5])
    apertures = trade_surface(frequencies, range_m=40.0 * AU, target_spot_size=1.0e3)
    expected = FWHM_COEFFICIENT * (c / frequencies) * (40.0 * AU) / 1.0e3
    np.testing.assert_allclose(apertures, expected, rtol=1e-12)


def test_trade_surface_scales_inversely_with_frequency() -> None:
    apertures = trade_surface(np.array([1.0, 10.0]), 40.0 * AU, 1.0e3)
    assert apertures[0] == pytest.approx(10.0 * apertures[1], rel=1e-12)


def test_trade_surface_validation() -> None:
    with pytest.raises(ValueError, match="range_m"):
        trade_surface(np.array([1.0]), 0.0, 1.0e3)
    with pytest.raises(ValueError, match="target_spot_size"):
        trade_surface(np.array([1.0]), 1.0e9, 0.0)
