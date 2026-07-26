"""Unit tests for gwtb.core.constants (T-1.1).

Acceptance criteria per docs/BACKLOG.md Sprint 1, T-1.1: ``G`` and ``c`` are
exact (they are definitional, not measured-and-rounded, for ``c``; CODATA 2018
for ``G``), and the derived coupling factors match to rtol 1e-9.
"""

from __future__ import annotations

import pytest

from gwtb.core import constants


def test_G_matches_codata_exactly() -> None:
    assert constants.G == 6.67430e-11


def test_c_is_exact_by_definition() -> None:
    assert constants.c == 299792458.0


def test_G_over_c4_matches_expected_value() -> None:
    assert constants.G_OVER_C4 == pytest.approx(8.2627176397e-45, rel=1e-9)


def test_G_over_c5_matches_expected_value() -> None:
    assert constants.G_OVER_C5 == pytest.approx(2.7561459334e-53, rel=1e-9)


def test_G_over_c4_is_internally_consistent() -> None:
    """The derived constant must actually be G/c^4, not a hand-typed literal."""
    assert constants.G_OVER_C4 == constants.G / constants.c**4


def test_G_over_c5_is_internally_consistent() -> None:
    assert constants.G_OVER_C5 == constants.G / constants.c**5


def test_astronomical_unit_matches_iau_2012() -> None:
    assert constants.AU == 1.495978707e11


def test_target_range_is_forty_au() -> None:
    assert constants.TARGET_RANGE == pytest.approx(40.0 * constants.AU, rel=1e-15)
