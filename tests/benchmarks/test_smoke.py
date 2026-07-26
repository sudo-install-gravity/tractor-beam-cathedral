"""Smoke tests for the benchmark harness itself.

These validate the harness, not the physics. The physics benchmarks arrive in
Sprint 1 once there is source code to validate.
"""

from __future__ import annotations

import pytest

from tests.benchmarks.helpers import (
    ReferenceConstants,
    assert_order_of_magnitude,
    assert_relative,
)


def test_gravitational_constant_matches_codata(ref: ReferenceConstants) -> None:
    assert_relative(ref.G, 6.67430e-11, rtol=1e-12, what="G")


def test_speed_of_light_is_exact(ref: ReferenceConstants) -> None:
    # c is exact by SI definition, not measured.
    assert ref.c == 299792458.0


def test_astronomical_unit_matches_iau(ref: ReferenceConstants) -> None:
    assert_relative(ref.AU, 1.495978707e11, rtol=1e-12, what="AU")


def test_derived_coupling_constants(ref: ReferenceConstants) -> None:
    """G/c^5 sets the scale of every luminosity in this project.

    Its magnitude, ~2.8e-53 in SI, is the single number most responsible for
    the feasibility gap documented in docs/PHYSICS.md section 8.
    """
    assert_relative(ref.G_over_c5, 2.7561459334e-53, rtol=1e-9, what="G/c^5")
    assert_relative(ref.G_over_c4, 8.2627176397e-45, rtol=1e-9, what="G/c^4")


def test_target_range_is_forty_au(target_range: float, ref: ReferenceConstants) -> None:
    assert_relative(target_range, 5.9839148280e12, rtol=1e-9, what="40 AU")
    assert target_range / ref.AU == pytest.approx(40.0)


class TestAssertRelative:
    """The comparison helper has to be trustworthy before benchmarks rely on it."""

    def test_passes_within_tolerance(self) -> None:
        assert_relative(1.0000001, 1.0, rtol=1e-6)

    def test_fails_outside_tolerance(self) -> None:
        with pytest.raises(AssertionError, match="relative error"):
            assert_relative(1.1, 1.0, rtol=1e-6)

    def test_reports_ratio_on_failure(self) -> None:
        """A factor-of-2 miss usually means a convention mismatch, so show it."""
        with pytest.raises(AssertionError, match="ratio"):
            assert_relative(2.0, 1.0, rtol=1e-6)

    def test_handles_expected_zero(self) -> None:
        assert_relative(1e-15, 0.0, rtol=1e-12)
        with pytest.raises(AssertionError):
            assert_relative(1e-9, 0.0, rtol=1e-12)


class TestAssertOrderOfMagnitude:
    def test_passes_within_half_decade(self) -> None:
        assert_order_of_magnitude(2.0e-20, 1.0e-20)

    def test_fails_across_decades(self) -> None:
        with pytest.raises(AssertionError, match="decades"):
            assert_order_of_magnitude(1.0e-20, 1.0e-25)

    def test_rejects_zero(self) -> None:
        with pytest.raises(ValueError):
            assert_order_of_magnitude(0.0, 1.0)
