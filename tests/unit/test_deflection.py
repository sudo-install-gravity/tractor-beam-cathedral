"""Unit tests for gwtb.target.deflection (T-8.7, T-8.8, T-14.2, T-14.3)."""

from __future__ import annotations

import math

import pytest

from gwtb.core.constants import AU, GM_EARTH, R_EARTH_EQ
from gwtb.target.deflection import (
    delta_v,
    miss_distance,
    required_delta_v,
    required_miss_distance,
)

_1AU_ORBIT = 1.0 * AU
_YEAR_S = 3.15576e7


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


# --- T-14.2: required_miss_distance ------------------------------------------


def test_required_miss_distance_at_escape_speed() -> None:
    """AC: required_miss_distance(v_esc) = sqrt(2) * R_EARTH_EQ, rtol 1e-12."""
    v_esc = math.sqrt(2.0 * GM_EARTH / R_EARTH_EQ)
    result = required_miss_distance(v_esc)
    assert result == pytest.approx(math.sqrt(2.0) * R_EARTH_EQ, rel=1e-12)


def test_required_miss_distance_at_high_speed_approaches_r_earth() -> None:
    """AC: required_miss_distance(1e8) -> R_EARTH_EQ, rtol 1e-3."""
    result = required_miss_distance(1.0e8)
    assert result == pytest.approx(R_EARTH_EQ, rel=1e-3)


def test_required_miss_distance_strictly_decreasing_in_v_infinity() -> None:
    slow = required_miss_distance(5.0e3)
    fast = required_miss_distance(7.2e4)
    assert slow > fast


def test_required_miss_distance_rejects_non_positive_v_infinity() -> None:
    with pytest.raises(ValueError, match="v_infinity"):
        required_miss_distance(0.0)


def test_required_miss_distance_rejects_non_finite_v_infinity() -> None:
    with pytest.raises(ValueError, match="v_infinity"):
        required_miss_distance(float("nan"))


# --- T-14.3: required_delta_v --------------------------------------------------


def test_secular_is_a_third_of_impulsive_floor() -> None:
    """AC: secular == impulsive/3 to rtol 1e-12 wherever both are defined."""
    miss = R_EARTH_EQ
    lead_time = 40.0 * _YEAR_S
    impulsive = required_delta_v(miss, lead_time, _1AU_ORBIT, "impulsive-floor")
    secular = required_delta_v(miss, lead_time, _1AU_ORBIT, "secular")
    assert secular == pytest.approx(impulsive / 3.0, rel=1e-12)


@pytest.mark.parametrize(
    "years,published_cm_s",
    [(10, 1.4), (20, 0.76), (30, 0.55), (40, 0.46), (50, 0.38)],
)
def test_greenstreet_2020_medians_bracketed(years: int, published_cm_s: float) -> None:
    """AC: bracketing test against [G20] -- secular <= published <= impulsive,
    for a 1 R_earth miss target, zero-tolerance consistency check."""
    lead_time = years * _YEAR_S
    published_mps = published_cm_s * 1.0e-2
    impulsive = required_delta_v(R_EARTH_EQ, lead_time, _1AU_ORBIT, "impulsive-floor")
    secular = required_delta_v(R_EARTH_EQ, lead_time, _1AU_ORBIT, "secular")
    assert secular <= published_mps <= impulsive


def test_required_delta_v_secular_rejects_lead_time_shorter_than_period() -> None:
    with pytest.raises(ValueError, match="orbital"):
        required_delta_v(R_EARTH_EQ, 1.0e3, _1AU_ORBIT, "secular")


def test_required_delta_v_impulsive_floor_allows_short_lead_time() -> None:
    """The impulsive-floor regime has no period guard -- it is valid (as an
    upper bound) at every lead time, including sub-orbital ones."""
    result = required_delta_v(R_EARTH_EQ, 1.0e3, _1AU_ORBIT, "impulsive-floor")
    assert result > 0.0


def test_required_delta_v_rejects_unknown_regime() -> None:
    with pytest.raises(ValueError, match="regime"):
        required_delta_v(R_EARTH_EQ, 1.0e9, _1AU_ORBIT, "optimistic")


def test_required_delta_v_rejects_non_positive_miss() -> None:
    with pytest.raises(ValueError, match="miss"):
        required_delta_v(0.0, 1.0e9, _1AU_ORBIT, "impulsive-floor")
