"""Unit tests for gwtb.target.threat (T-14.1)."""

from __future__ import annotations

import pytest

from gwtb.target.threat import (
    ANCHORS,
    RHO_RUBBLE_PILE,
    RHO_STONY,
    ThreatAnchor,
    mass_from_diameter,
)


def _anchor(name: str) -> ThreatAnchor:
    for a in ANCHORS:
        if a.name == name:
            return a
    raise KeyError(name)


def test_dimorphos_mass_self_consistent_with_diameter_and_density() -> None:
    """AC: mass_from_diameter(151.0, RHO_STONY) matches the Dimorphos anchor
    to rtol 2e-2 -- the anchor table is self-consistent with its own source."""
    dimorphos = _anchor("Dimorphos")
    computed = mass_from_diameter(dimorphos.diameter_m, RHO_STONY)
    assert computed == pytest.approx(dimorphos.mass_kg, rel=2e-2)


def test_bennu_mass_self_consistent_with_diameter_and_density() -> None:
    """AC: mass_from_diameter(490.0, RHO_RUBBLE_PILE) matches Bennu to rtol 2e-2."""
    bennu = _anchor("Bennu")
    computed = mass_from_diameter(bennu.diameter_m, RHO_RUBBLE_PILE)
    assert computed == pytest.approx(bennu.mass_kg, rel=2e-2)


def test_every_anchor_has_a_non_empty_source() -> None:
    """AC: absence-loud -- every anchor's source is non-empty."""
    for a in ANCHORS:
        assert a.source


def test_anchor_names_are_unique() -> None:
    names = [a.name for a in ANCHORS]
    assert len(names) == len(set(names))


def test_mass_from_diameter_rejects_non_positive_diameter() -> None:
    with pytest.raises(ValueError, match="diameter"):
        mass_from_diameter(0.0, RHO_STONY)


def test_mass_from_diameter_rejects_non_positive_density() -> None:
    with pytest.raises(ValueError, match="density"):
        mass_from_diameter(100.0, -1.0)


def test_mass_from_diameter_rejects_non_finite_inputs() -> None:
    with pytest.raises(ValueError, match="diameter"):
        mass_from_diameter(float("inf"), RHO_STONY)
    with pytest.raises(ValueError, match="density"):
        mass_from_diameter(100.0, float("nan"))


def test_threat_anchor_rejects_non_positive_mass() -> None:
    with pytest.raises(ValueError, match="mass_kg"):
        ThreatAnchor(name="x", diameter_m=1.0, mass_kg=0.0, speed_mps=None, source="[x]")


def test_threat_anchor_rejects_empty_source() -> None:
    with pytest.raises(ValueError, match="source"):
        ThreatAnchor(name="x", diameter_m=1.0, mass_kg=1.0, speed_mps=None, source="")


def test_threat_anchor_rejects_non_positive_speed_when_given() -> None:
    with pytest.raises(ValueError, match="speed_mps"):
        ThreatAnchor(name="x", diameter_m=1.0, mass_kg=1.0, speed_mps=-1.0, source="[x]")


def test_threat_anchor_allows_none_speed() -> None:
    a = ThreatAnchor(name="x", diameter_m=1.0, mass_kg=1.0, speed_mps=None, source="[x]")
    assert a.speed_mps is None
