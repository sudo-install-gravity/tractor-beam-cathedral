"""Unit tests for gwtb.target.deflection (T-8.7, T-8.8)."""

from __future__ import annotations

import pytest

from gwtb.core.constants import AU
from gwtb.target.deflection import delta_v, miss_distance

_1AU_ORBIT = 1.0 * AU


# --- T-8.7: delta_v ----------------------------------------------------------


def test_dart_cross_check() -> None:
    """AC: 4.3e9 kg, ~1.16e7 N s -> 2.7 mm/s to rtol 1e-2."""
    mass = 4.3e9
    impulse = 1.16e7
    duration = 1.0
    v = delta_v(force=impulse / duration, duration=duration, asteroid_mass=mass)
    assert v == pytest.approx(2.7e-3, rel=1e-2)


def test_delta_v_scales_linearly_with_force_and_duration() -> None:
    base = delta_v(force=10.0, duration=2.0, asteroid_mass=1e9)
    assert delta_v(force=20.0, duration=2.0, asteroid_mass=1e9) == pytest.approx(
        2.0 * base, rel=1e-14
    )
    assert delta_v(force=10.0, duration=4.0, asteroid_mass=1e9) == pytest.approx(
        2.0 * base, rel=1e-14
    )


def test_delta_v_scales_inversely_with_mass() -> None:
    a = delta_v(force=10.0, duration=1.0, asteroid_mass=1e9)
    b = delta_v(force=10.0, duration=1.0, asteroid_mass=2e9)
    assert a == pytest.approx(2.0 * b, rel=1e-14)


def test_delta_v_rejects_non_positive_duration() -> None:
    with pytest.raises(ValueError, match="duration"):
        delta_v(force=1.0, duration=0.0, asteroid_mass=1e9)


def test_delta_v_rejects_non_positive_mass() -> None:
    with pytest.raises(ValueError, match="asteroid_mass"):
        delta_v(force=1.0, duration=1.0, asteroid_mass=-1.0)


def test_delta_v_accepts_negative_force() -> None:
    """A signed deflection direction is physically meaningful."""
    assert delta_v(force=-10.0, duration=1.0, asteroid_mass=1e9) < 0.0


# --- T-8.8: miss_distance ------------------------------------------------------


def test_miss_distance_scales_linearly_with_delta_v() -> None:
    """AC: rtol 1e-6."""
    base = miss_distance(delta_v=0.001, lead_time=1.0e6, orbit=_1AU_ORBIT)
    scaled = miss_distance(delta_v=0.005, lead_time=1.0e6, orbit=_1AU_ORBIT)
    assert scaled == pytest.approx(5.0 * base, rel=1e-6)


def test_miss_distance_scales_linearly_with_lead_time() -> None:
    base = miss_distance(delta_v=0.001, lead_time=1.0e6, orbit=_1AU_ORBIT)
    scaled = miss_distance(delta_v=0.001, lead_time=3.0e6, orbit=_1AU_ORBIT)
    assert scaled == pytest.approx(3.0 * base, rel=1e-6)


def test_miss_distance_matches_the_closed_form() -> None:
    result = miss_distance(delta_v=0.0027, lead_time=3.15e7, orbit=_1AU_ORBIT)
    assert result == pytest.approx(0.0027 * 3.15e7, rel=1e-12)


def test_miss_distance_rejects_lead_time_exceeding_the_orbital_period() -> None:
    """The impulsive-limit formula is not valid outside lead_time << period."""
    with pytest.raises(ValueError, match="orbital period"):
        miss_distance(delta_v=1.0, lead_time=1.0e10, orbit=1.0e6)  # tiny orbit, huge lead_time


def test_miss_distance_accepts_negative_delta_v() -> None:
    assert miss_distance(delta_v=-0.001, lead_time=1.0e6, orbit=_1AU_ORBIT) < 0.0


def test_miss_distance_rejects_non_positive_orbit() -> None:
    with pytest.raises(ValueError, match="orbit"):
        miss_distance(delta_v=0.001, lead_time=1.0e6, orbit=0.0)
