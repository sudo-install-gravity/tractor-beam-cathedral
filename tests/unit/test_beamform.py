"""Unit tests for gwtb.array.beamform (T-6.1, T-6.2, T-6.3, T-6.4)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.array.beamform import (
    array_factor,
    beamwidth_3db,
    peak_sidelobe_level,
    steering_phases,
    taper,
)
from gwtb.array.geometry import linear_array


def test_array_factor_matches_uniform_broadside_analytic() -> None:
    n, d, wavelength = 8, 0.5, 1.0
    geom = linear_array(n, d)
    weights = np.ones(n, dtype=complex)
    theta = 0.3
    direction = np.array([np.sin(theta), 0.0, np.cos(theta)])

    af = array_factor(geom, weights, wavelength, direction)
    psi = 2.0 * np.pi / wavelength * d * np.sin(theta)
    analytic = np.sin(n * psi / 2.0) / np.sin(psi / 2.0)
    assert af.real == pytest.approx(analytic, rel=1e-9)
    assert af.imag == pytest.approx(0.0, abs=1e-9)


def test_array_factor_rejects_non_unit_direction() -> None:
    geom = linear_array(4, 0.5)
    with pytest.raises(ValueError):
        array_factor(geom, np.ones(4, dtype=complex), 1.0, np.array([1.0, 1.0, 0.0]))


def test_steering_phases_puts_peak_at_target() -> None:
    n, d, wavelength = 16, 0.5, 1.0
    geom = linear_array(n, d)
    theta_target = 0.4
    direction = np.array([np.sin(theta_target), 0.0, np.cos(theta_target)])
    phases = steering_phases(geom, wavelength, direction)
    weights = np.exp(1j * phases)

    # k . r_n is linear in sin(theta), so the array factor is exactly
    # periodic in psi = k d sin(theta); sweep sin(theta) directly for an
    # exact peak location rather than paying for a huge angular grid.
    k_vec_per_sin = (2.0 * np.pi / wavelength) * np.array([1.0, 0.0, 0.0])
    phase_per_sin = geom @ k_vec_per_sin  # phase contribution per unit sin(theta)
    sins = np.linspace(-1.0, 1.0, 2_000_001)
    af = np.sum(weights[None, :] * np.exp(1j * np.outer(sins, phase_per_sin)), axis=1)
    peak_theta = np.arcsin(sins[np.argmax(np.abs(af))])
    assert abs(peak_theta - theta_target) < 1e-6


def test_beamwidth_matches_uniform_array_formula_for_large_n() -> None:
    n, d, wavelength = 128, 0.5, 1.0
    geom = linear_array(n, d)
    weights = np.ones(n, dtype=complex)
    bw = beamwidth_3db(geom, weights, wavelength, axis=np.array([1.0, 0.0, 0.0]))
    expected = 0.886 * wavelength / (n * d)
    assert bw == pytest.approx(expected, rel=1e-3)


def test_peak_sidelobe_level_matches_uniform_array_minus_13_2_db() -> None:
    n, d, wavelength = 128, 0.5, 1.0
    geom = linear_array(n, d)
    weights = np.ones(n, dtype=complex)
    psl = peak_sidelobe_level(geom, weights, wavelength, axis=np.array([1.0, 0.0, 0.0]))
    assert psl == pytest.approx(-13.2, abs=0.2)


def test_taper_uniform_is_ones() -> None:
    np.testing.assert_array_equal(taper(10, "uniform"), np.ones(10))


def test_chebyshev_taper_hits_requested_sidelobe_level() -> None:
    n, d, wavelength = 32, 0.5, 1.0
    geom = linear_array(n, d)
    for sll in (30.0, 40.0, 50.0):
        weights = taper(n, "chebyshev", sll=sll).astype(complex)
        psl = peak_sidelobe_level(geom, weights, wavelength, axis=np.array([1.0, 0.0, 0.0]))
        assert psl == pytest.approx(-sll, abs=0.5)


def test_taper_beamwidth_broadens_monotonically_with_depth() -> None:
    n, d, wavelength = 32, 0.5, 1.0
    geom = linear_array(n, d)
    axis = np.array([1.0, 0.0, 0.0])
    bws = []
    for sll in (20.0, 30.0, 40.0, 50.0):
        weights = taper(n, "chebyshev", sll=sll).astype(complex)
        bws.append(beamwidth_3db(geom, weights, wavelength, axis))
    assert all(b2 > b1 for b1, b2 in zip(bws[:-1], bws[1:], strict=True))


def test_taylor_taper_requires_sll_and_nbar() -> None:
    with pytest.raises(ValueError):
        taper(16, "taylor")


def test_unknown_taper_kind_raises() -> None:
    with pytest.raises(ValueError):
        taper(8, "bogus")
