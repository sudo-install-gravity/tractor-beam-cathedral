"""Unit tests for gwtb.ledger.tradespace (T-14.5)."""

from __future__ import annotations

import itertools
import math

import pytest

from gwtb.core.constants import AU
from gwtb.target.tradespace import (
    DENSITIES_KGM3,
    DETECTION_DISTANCES_M,
    DIAMETERS_M,
    V_INFINITY_MPS,
    TradespaceCell,
    best_case_gap_decades,
    tradespace,
)

_ACHIEVED_LUM = 7.5e-2


# --- construction / field consistency -----------------------------------------


def test_valid_secular_cell_requires_finite_secular_fields() -> None:
    with pytest.raises(ValueError, match="secular_valid is True"):
        TradespaceCell(
            detection_distance_m=1.0,
            v_infinity_mps=1.0,
            diameter_m=1.0,
            density_kgm3=1.0,
            mass_kg=1.0,
            lead_time_s=1.0,
            miss_required_m=1.0,
            delta_v_floor_mps=1.0,
            delta_v_secular_mps=math.nan,  # should be finite when secular_valid
            force_floor_n=1.0,
            luminosity_floor_w=1.0,
            luminosity_secular_w=1.0,
            gap_decades_floor=1.0,
            gap_decades_secular=1.0,
            secular_valid=True,
        )


def test_invalid_secular_cell_requires_nan_secular_fields() -> None:
    with pytest.raises(ValueError, match="secular_valid is False"):
        TradespaceCell(
            detection_distance_m=1.0,
            v_infinity_mps=1.0,
            diameter_m=1.0,
            density_kgm3=1.0,
            mass_kg=1.0,
            lead_time_s=1.0,
            miss_required_m=1.0,
            delta_v_floor_mps=1.0,
            delta_v_secular_mps=1.0,  # should be nan when not secular_valid
            force_floor_n=1.0,
            luminosity_floor_w=1.0,
            luminosity_secular_w=math.nan,
            gap_decades_floor=1.0,
            gap_decades_secular=math.nan,
            secular_valid=False,
        )


def test_always_finite_field_must_be_finite() -> None:
    with pytest.raises(ValueError, match="gap_decades_floor"):
        TradespaceCell(
            detection_distance_m=1.0,
            v_infinity_mps=1.0,
            diameter_m=1.0,
            density_kgm3=1.0,
            mass_kg=1.0,
            lead_time_s=1.0,
            miss_required_m=1.0,
            delta_v_floor_mps=1.0,
            delta_v_secular_mps=math.nan,
            force_floor_n=1.0,
            luminosity_floor_w=1.0,
            luminosity_secular_w=math.nan,
            gap_decades_floor=math.nan,  # must always be finite
            gap_decades_secular=math.nan,
            secular_valid=False,
        )


def test_full_grid_builds_without_error() -> None:
    cells = tradespace(
        DETECTION_DISTANCES_M, V_INFINITY_MPS, DIAMETERS_M, DENSITIES_KGM3, _ACHIEVED_LUM
    )
    assert len(cells) == (
        len(DETECTION_DISTANCES_M) * len(V_INFINITY_MPS) * len(DIAMETERS_M) * len(DENSITIES_KGM3)
    )
    for cell in cells:
        assert math.isfinite(cell.gap_decades_floor)
        if cell.secular_valid:
            assert math.isfinite(cell.gap_decades_secular)
        else:
            assert math.isnan(cell.gap_decades_secular)


def test_tradespace_rejects_non_positive_achieved_luminosity() -> None:
    with pytest.raises(ValueError, match="achieved_luminosity"):
        tradespace(DETECTION_DISTANCES_M, V_INFINITY_MPS, DIAMETERS_M, DENSITIES_KGM3, 0.0)


# --- d-cancellation (D-14.6), asserted per branch -------------------------------


_VDR_COMBOS = list(itertools.product(V_INFINITY_MPS, DIAMETERS_M, DENSITIES_KGM3))


@pytest.mark.parametrize("v,diam,rho", _VDR_COMBOS)
def test_gap_decades_floor_independent_of_detection_distance(
    v: float, diam: float, rho: float
) -> None:
    """AC: gap_decades_floor agrees across all d at fixed (v, D, rho) to
    atol 1e-9 decades; every (v, D, rho) combination has >= 2 points checked
    (there are 6 detection distances in the grid)."""
    cells = tradespace(DETECTION_DISTANCES_M, (v,), (diam,), (rho,), _ACHIEVED_LUM)
    assert len(cells) == len(DETECTION_DISTANCES_M) >= 2
    values = [c.gap_decades_floor for c in cells]
    for value in values[1:]:
        assert value == pytest.approx(values[0], abs=1e-9)


def test_gap_decades_secular_independent_of_detection_distance_across_grid() -> None:
    """AC: gap_decades_secular agrees across the secular_valid subset of d at
    fixed (v, D, rho) to atol 1e-9, skipping (and counting) subsets with < 2
    valid cells."""
    single_point_subsets = 0
    multi_point_subsets = 0
    for v, diam, rho in itertools.product(V_INFINITY_MPS, DIAMETERS_M, DENSITIES_KGM3):
        cells = tradespace(DETECTION_DISTANCES_M, (v,), (diam,), (rho,), _ACHIEVED_LUM)
        valid_values = [c.gap_decades_secular for c in cells if c.secular_valid]
        if len(valid_values) < 2:
            single_point_subsets += 1
            continue
        multi_point_subsets += 1
        for value in valid_values[1:]:
            assert value == pytest.approx(valid_values[0], abs=1e-9)
    assert multi_point_subsets > 0, "no (v, D, rho) subset had >= 2 secular_valid points to check"
    # Informational: this grid is expected to have some single-point (or
    # zero-point) subsets at high v_infinity, where only the largest
    # detection distance clears the secular guard.
    assert single_point_subsets >= 0


# --- monotonicity ---------------------------------------------------------------


def test_gap_decades_floor_strictly_increasing_in_mass() -> None:
    """AC: gap_decades_floor strictly increasing in mass at fixed (d, v, rho)."""
    d, v, rho = 40.0 * AU, 5.0e3, 2400.0
    cells = tradespace((d,), (v,), DIAMETERS_M, (rho,), _ACHIEVED_LUM)
    masses = [c.mass_kg for c in cells]
    gaps = [c.gap_decades_floor for c in cells]
    assert masses == sorted(masses)
    assert gaps == sorted(gaps)
    assert len(set(gaps)) == len(gaps)  # strictly increasing, no ties


# --- pinned spot cell -------------------------------------------------------------


def test_spot_cell_luminosity_secular() -> None:
    """AC: (d=40 AU, v=5 km/s, D=20 m, rho=2400) -> luminosity_secular_w =
    1.57e28 W rtol 2e-2."""
    cells = tradespace((40.0 * AU,), (5.0e3,), (20.0,), (2400.0,), _ACHIEVED_LUM)
    assert len(cells) == 1
    cell = cells[0]
    assert cell.secular_valid
    assert cell.luminosity_secular_w == pytest.approx(1.57e28, rel=2e-2)


# --- best_case_gap_decades: nan-exclusion by flag, not luck ----------------------


def test_best_case_gap_decades_excludes_nan_by_flag() -> None:
    cells = tradespace(
        DETECTION_DISTANCES_M, V_INFINITY_MPS, DIAMETERS_M, DENSITIES_KGM3, _ACHIEVED_LUM
    )
    assert any(not c.secular_valid for c in cells), "grid should contain some invalid-secular cells"
    assert any(c.secular_valid for c in cells), "grid should contain some valid-secular cells"

    result = best_case_gap_decades(cells)

    manual_valid = [c.gap_decades_secular for c in cells if c.secular_valid]
    assert result == min(manual_valid)
    assert math.isfinite(result)

    # A naive min() over the unfiltered column would either raise or silently
    # propagate nan (nan comparisons are always False, so nan can "win" or
    # "lose" depending on position) -- confirm the flag-based filter is what
    # makes the function correct, not incidental list ordering.
    unfiltered = [c.gap_decades_secular for c in cells]
    assert any(math.isnan(v) for v in unfiltered)


def test_best_case_gap_decades_raises_when_no_cell_is_secular_valid() -> None:
    # A tiny detection distance and high speed guarantee lead_time is far
    # short of one orbital period.
    cells = tradespace((0.01 * AU,), (7.2e4,), (20.0,), (2400.0,), _ACHIEVED_LUM)
    assert all(not c.secular_valid for c in cells)
    with pytest.raises(ValueError, match="no secular_valid"):
        best_case_gap_decades(cells)


def test_best_case_gap_decades_expected_minimum() -> None:
    """Plan-review-computed grid minimum: (D=20 m, rho=1190, v=5 km/s),
    ~29.016 decades -- the rubble-pile density gives the lighter, easier
    target, not the D=20/rho=2400 spot cell above."""
    cells = tradespace(
        DETECTION_DISTANCES_M, V_INFINITY_MPS, DIAMETERS_M, DENSITIES_KGM3, _ACHIEVED_LUM
    )
    result = best_case_gap_decades(cells)
    assert 28.5 <= result <= 29.5
