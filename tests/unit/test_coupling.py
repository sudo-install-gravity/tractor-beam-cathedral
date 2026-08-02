"""Unit tests for gwtb.target.coupling (T-8.2, T-8.3, T-8.4, T-8.5, T-8.6)."""

from __future__ import annotations

import math

import pytest

from gwtb.core.constants import AU
from gwtb.target.coupling import (
    CouplingResult,
    channel_absorption,
    channel_gravity_tractor,
    channel_gravity_tractor_result,
    channel_tidal,
    compare_channels,
    tidal_strain,
)


def test_reproduces_apophis_worked_example() -> None:
    """Schweickart, Chapman, Durda & Hut, arXiv:physics/0608157 (2006), Fig. 2:
    Apophis, M=4.6e10 kg, m=1e3 kg, d=240 m -> T=0.053 N."""
    f = channel_gravity_tractor(tractor_mass=1.0e3, separation=240.0, asteroid_mass=4.6e10)
    assert f == pytest.approx(0.053, rel=1e-2)


def test_reproduces_2004vd17_worked_example() -> None:
    """Same source, second example: 2004VD17, M=2.6e11 kg, m=1e3 kg,
    d=435 m -> T=0.092 N."""
    f = channel_gravity_tractor(tractor_mass=1.0e3, separation=435.0, asteroid_mass=2.6e11)
    assert f == pytest.approx(0.092, rel=1e-2)


@pytest.mark.parametrize(
    "tractor_mass,separation,asteroid_mass",
    [(-1.0, 1.0, 1.0), (1.0, 0.0, 1.0), (1.0, 1.0, -1.0)],
)
def test_rejects_non_positive_arguments(
    tractor_mass: float, separation: float, asteroid_mass: float
) -> None:
    with pytest.raises(ValueError):
        channel_gravity_tractor(tractor_mass, separation, asteroid_mass)


def test_scales_inversely_with_separation_squared() -> None:
    f1 = channel_gravity_tractor(tractor_mass=1e3, separation=100.0, asteroid_mass=1e10)
    f2 = channel_gravity_tractor(tractor_mass=1e3, separation=200.0, asteroid_mass=1e10)
    assert f1 == pytest.approx(4.0 * f2, rel=1e-12)


# --- T-8.2: tidal_strain -----------------------------------------------------


def test_tidal_strain_scales_linearly_with_h_amplitude() -> None:
    a = tidal_strain(1e-21, 500.0)
    b = tidal_strain(3e-21, 500.0)
    assert b == pytest.approx(3.0 * a, rel=1e-14)


def test_tidal_strain_scales_linearly_with_body_radius() -> None:
    a = tidal_strain(1e-21, 500.0)
    b = tidal_strain(1e-21, 1500.0)
    assert b == pytest.approx(3.0 * a, rel=1e-14)


def test_tidal_strain_matches_the_half_h_r_closed_form() -> None:
    assert tidal_strain(2e-21, 1000.0) == pytest.approx(1e-18, rel=1e-14)


def test_tidal_strain_rejects_non_positive_radius() -> None:
    with pytest.raises(ValueError, match="body_radius"):
        tidal_strain(1e-21, 0.0)


# --- T-8.3: channel_tidal -----------------------------------------------------


def test_channel_tidal_returns_strain_not_force() -> None:
    """AC: returns strain, not force; result carries no net-force field."""
    result = channel_tidal(1e-21, 500.0)
    assert result.channel == "tidal"
    assert result.strain is not None
    assert result.force is None


def test_coupling_result_requires_exactly_one_field() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        CouplingResult(channel="x")
    with pytest.raises(ValueError, match="exactly one"):
        CouplingResult(channel="x", strain=1.0, force=1.0)


# --- T-8.4: channel_absorption ------------------------------------------------


def test_channel_absorption_returns_force_not_strain() -> None:
    result = channel_absorption(luminosity=1e-19, cross_section=1.0, distance=40.0 * AU)
    assert result.force is not None
    assert result.strain is None


def test_channel_absorption_below_1e_30_n_for_1km_asteroid_at_40au() -> None:
    """AC: the smallness is the finding, asserted rather than hidden."""
    # A 1 km asteroid: cross-section ~ pi r^2 for r ~ 500 m.
    cross_section = math.pi * 500.0**2
    result = channel_absorption(luminosity=1e-19, cross_section=cross_section, distance=40.0 * AU)
    assert result.force < 1e-30


def test_channel_absorption_scales_linearly_with_luminosity_and_cross_section() -> None:
    a = channel_absorption(1.0, 1.0, 1.0e9).force
    assert a is not None
    b = channel_absorption(2.0, 1.0, 1.0e9).force
    c = channel_absorption(1.0, 3.0, 1.0e9).force
    assert b == pytest.approx(2.0 * a, rel=1e-12)
    assert c == pytest.approx(3.0 * a, rel=1e-12)


def test_channel_absorption_scales_inversely_with_distance_squared() -> None:
    near = channel_absorption(1.0, 1.0, 1.0e9).force
    far = channel_absorption(1.0, 1.0, 2.0e9).force
    assert near == pytest.approx(4.0 * far, rel=1e-12)


def test_channel_absorption_rejects_non_positive_cross_section() -> None:
    with pytest.raises(ValueError, match="cross_section"):
        channel_absorption(1.0, 0.0, 1.0e9)


# --- T-8.6: compare_channels --------------------------------------------------


def test_compare_channels_reports_all_three() -> None:
    tidal = channel_tidal(1e-21, 500.0)
    absorption = channel_absorption(1e-19, 1.0, 40.0 * AU)
    tractor = channel_gravity_tractor_result(1e3, 240.0, 4.6e10)

    report = compare_channels(tidal, absorption, tractor, required_strain=1e-15, required_force=1.0)
    names = {m.name for m in report}
    assert names == {"tidal", "absorption", "gravity_tractor"}


def test_compare_channels_orders_by_descending_magnitude() -> None:
    tidal = channel_tidal(1e-21, 500.0)  # ~5e-19 m
    absorption = channel_absorption(1e-19, 1.0, 40.0 * AU)  # extremely small
    tractor = channel_gravity_tractor_result(1e3, 240.0, 4.6e10)  # ~0.05 N

    report = compare_channels(tidal, absorption, tractor, required_strain=1.0, required_force=1.0)
    magnitudes = [m.achieved for m in report]
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_compare_channels_never_sums_the_rows() -> None:
    """The three rows' achieved values must be exactly the individual channel
    magnitudes — not a combination of them. Also guards against a fourth
    "total" row ever being added: summing tidal (m), absorption (N) and
    gravity_tractor (N) would mix incompatible units, which is precisely
    the mechanism-additivity error this AC forbids."""
    tidal = channel_tidal(1e-21, 500.0)
    absorption = channel_absorption(1e-19, 1.0, 40.0 * AU)
    tractor = channel_gravity_tractor_result(1e3, 240.0, 4.6e10)

    report = compare_channels(tidal, absorption, tractor, required_strain=1.0, required_force=1.0)
    assert len(report) == 3
    achieved_by_name = {m.name: m.achieved for m in report}
    assert achieved_by_name["tidal"] == pytest.approx(abs(tidal.strain), rel=1e-12)
    assert achieved_by_name["absorption"] == pytest.approx(abs(absorption.force), rel=1e-12)
    assert achieved_by_name["gravity_tractor"] == pytest.approx(abs(tractor.force), rel=1e-12)
