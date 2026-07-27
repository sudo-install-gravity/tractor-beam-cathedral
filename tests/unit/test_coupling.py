"""Unit tests for gwtb.target.coupling (T-8.5)."""

from __future__ import annotations

import pytest

from gwtb.target.coupling import channel_gravity_tractor


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
