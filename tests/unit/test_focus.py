"""Unit tests for gwtb.array.focus (T-9.5).

The acceptance criterion — residual phase error at the focus < 1e-9 rad — is
not checkable against the implementation's own arithmetic, because the naive
float64 route is itself ~1e-8 rad wrong at 40 AU. These tests therefore compute
the reference ranges in exact decimal arithmetic at 60 significant digits and
compare against that, which is an genuinely independent check rather than a
restatement of the code.
"""

from __future__ import annotations

import math
from decimal import Decimal, getcontext

import numpy as np
import pytest

from gwtb.array.focus import focal_phases
from gwtb.array.geometry import linear_array, planar_array
from gwtb.core.constants import AU, c

getcontext().prec = 60

#: pi to 50 significant digits, for the exact-arithmetic reference.
_PI = Decimal("3.14159265358979323846264338327950288419716939937510")

_FOCAL_POINT = np.array([0.0, 0.0, 40.0 * AU])
_FOCAL_TIME = 1234.5
_FREQUENCIES = np.array([100.0, 1000.0, 10000.0])


def _exact_ranges(positions: np.ndarray, focal_point: np.ndarray) -> list[Decimal]:
    """Element-to-focus ranges in 60-digit decimal arithmetic.

    ``Decimal(float)`` is exact for a binary float, so this consumes precisely
    the same inputs the implementation sees; only the arithmetic differs.
    """
    ranges = []
    for p in positions:
        total = Decimal(0)
        for i in range(3):
            d = Decimal(float(focal_point[i])) - Decimal(float(p[i]))
            total += d * d
        ranges.append(total.sqrt())
    return ranges


def _exact_differential_phases(
    positions: np.ndarray, focal_point: np.ndarray, frequency: float
) -> np.ndarray:
    """Exact ``2 pi f (R_a - R_0) / c``, relative to element 0."""
    ranges = _exact_ranges(positions, focal_point)
    c_dec = Decimal(float(c))
    f_dec = Decimal(float(frequency))
    out = []
    for r in ranges:
        out.append(float(2 * _PI * f_dec * (r - ranges[0]) / c_dec))
    return np.array(out)


def _wrap(x: np.ndarray) -> np.ndarray:
    """Wrap to [-pi, pi)."""
    return np.remainder(x + np.pi, 2.0 * np.pi) - np.pi


# --- AC: residual phase error at the focus < 1e-9 rad ---------------------


def test_residual_phase_error_below_1e_9_at_40_au() -> None:
    """The headline acceptance criterion, against exact decimal ranges."""
    positions = planar_array(8, 8, 1250.0, 1250.0)
    phases = focal_phases(positions, _FREQUENCIES, _FOCAL_POINT, _FOCAL_TIME)

    for j, freq in enumerate(_FREQUENCIES):
        exact = _exact_differential_phases(positions, _FOCAL_POINT, freq)
        ours = phases[:, j] - phases[0, j]
        residual = _wrap(ours - exact)
        assert np.max(np.abs(residual)) < 1e-9, f"frequency {freq} Hz"


def test_residual_holds_for_a_sparse_wide_aperture() -> None:
    """A 10 km aperture is where the cancellation is worst."""
    rng = np.random.default_rng(7)
    positions = np.zeros((32, 3))
    positions[:, 0] = rng.uniform(-5000.0, 5000.0, 32)
    positions[:, 1] = rng.uniform(-5000.0, 5000.0, 32)

    phases = focal_phases(positions, _FREQUENCIES, _FOCAL_POINT, _FOCAL_TIME)
    for j, freq in enumerate(_FREQUENCIES):
        exact = _exact_differential_phases(positions, _FOCAL_POINT, freq)
        residual = _wrap((phases[:, j] - phases[0, j]) - exact)
        assert np.max(np.abs(residual)) < 1e-9, f"frequency {freq} Hz"


def test_naive_float64_differencing_loses_the_signal_entirely() -> None:
    """Documents *why* the stabilized identity exists.

    This is the implementation the task would otherwise have got: form each
    range in float64 and subtract. At 40 AU it does not merely lose precision —
    every element's range rounds to the *same* float64, so the differences are
    identically zero and 100% of the focusing information is gone. The
    stabilized form recovers a real spread of ~3.1e-6 m from the same inputs.

    If this test ever starts failing, float64 got wider or the geometry changed;
    it should not be deleted to quieten the suite (CLAUDE.md rule 5).
    """
    positions = planar_array(8, 8, 1250.0, 1250.0)

    ranges = np.linalg.norm(_FOCAL_POINT - positions, axis=1)
    naive_delta = ranges - ranges[0]
    assert np.ptp(naive_delta) == 0.0, "expected total cancellation in naive float64"

    ranges_exact = _exact_ranges(positions, _FOCAL_POINT)
    exact = np.array([float(r - ranges_exact[0]) for r in ranges_exact])
    assert np.ptp(exact) > 1e-6, "the true range spread is nonzero"

    # Ours recovers it: differential phase tracks the exact range difference.
    #
    # rtol is 1e-4, and the reason is worth recording rather than tuning away.
    # The differential phase at 40 AU is ~1e-11 rad, carried on a wrapped
    # common-mode phase of order 1 rad, so wrapping costs ~2e-16 rad of
    # rounding — five orders of magnitude below the signal, but 1e-5 of it in
    # relative terms, and that lands directly on the recovered range. The
    # acceptance criterion is stated in absolute phase (< 1e-9 rad), which this
    # clears by two orders of magnitude; the relative floor here is float64's,
    # not the algorithm's.
    phases = focal_phases(positions, np.array([1000.0]), _FOCAL_POINT, _FOCAL_TIME)
    recovered = (phases[:, 0] - phases[0, 0]) * c / (2.0 * np.pi * 1000.0)
    np.testing.assert_allclose(recovered, exact, rtol=1e-4, atol=1e-18)


def test_focusing_is_degenerate_with_steering_at_40_au() -> None:
    """**Finding, not a bug** (CLAUDE.md rule 5): at 40 AU you cannot focus.

    The wavefront sag across a 12.4 km aperture at 40 AU is ~3.2e-6 m, so the
    entire focusing phase correction is ~1e-11 rad at 1 kHz — ten orders of
    magnitude inside the far field (R / R_Fraunhofer ~ 5.9e9). A "focal point"
    at 40 AU is indistinguishable from a steering direction at infinity.

    This is the same diffraction wall T-10.2 states from the other side, and it
    is why T-9.6's focused field must not be read as concentrating energy at
    range. If a future change makes this spread large at 40 AU, the change is
    defective, not the wall.
    """
    positions = planar_array(8, 8, 1250.0, 1250.0)
    phases = focal_phases(positions, np.array([1000.0]), _FOCAL_POINT, _FOCAL_TIME)
    spread = float(np.ptp(phases[:, 0]))
    assert spread < 1e-9, f"focusing phase at 40 AU should be negligible, got {spread}"


def test_near_field_focus_gives_distinct_element_phases() -> None:
    """ADR-0002 §7: per-element delay, never one delay for the whole array.

    At 40 AU the phases are legitimately near-constant (above), so that geometry
    cannot distinguish a correct implementation from a centroid approximation.
    This one can: at 100 km with a 1 MHz drive the array is well inside the
    Fraunhofer distance and element phases span radians.
    """
    positions = planar_array(8, 8, 1250.0, 1250.0)
    focal_point = np.array([0.0, 0.0, 1.0e5])
    frequency = 1.0e6

    phases = focal_phases(positions, np.array([frequency]), focal_point, 0.0)
    assert float(np.ptp(phases[:, 0])) > 1.0, "near-field phases should span radians"

    exact = _exact_differential_phases(positions, focal_point, frequency)
    residual = _wrap((phases[:, 0] - phases[0, 0]) - exact)
    assert np.max(np.abs(residual)) < 1e-9


def test_residual_below_1e_9_where_the_criterion_actually_bites() -> None:
    """The AC restated in the regime that can fail it.

    At 40 AU the true differential phase is ~1e-11 rad, so "residual < 1e-9 rad"
    is satisfied by returning zeros. In the near field the phases are O(1) rad
    and the criterion is a real statement about precision.
    """
    rng = np.random.default_rng(11)
    positions = np.zeros((24, 3))
    positions[:, 0] = rng.uniform(-5000.0, 5000.0, 24)
    positions[:, 1] = rng.uniform(-5000.0, 5000.0, 24)
    focal_point = np.array([1.0e4, -2.0e4, 3.0e5])

    for frequency in (1.0e5, 1.0e6, 1.0e7):
        phases = focal_phases(positions, np.array([frequency]), focal_point, 0.0)
        exact = _exact_differential_phases(positions, focal_point, frequency)
        residual = _wrap((phases[:, 0] - phases[0, 0]) - exact)
        assert np.max(np.abs(residual)) < 1e-9, f"frequency {frequency} Hz"


# --- shape, dtype and wrapping contracts ----------------------------------


def test_shape_is_elements_by_frequencies() -> None:
    positions = planar_array(4, 5, 100.0, 100.0)
    phases = focal_phases(positions, _FREQUENCIES, _FOCAL_POINT, _FOCAL_TIME)
    assert phases.shape == (20, 3)
    assert phases.dtype == np.float64


def test_phases_are_wrapped_to_pi() -> None:
    positions = planar_array(8, 8, 1250.0, 1250.0)
    phases = focal_phases(positions, _FREQUENCIES, _FOCAL_POINT, _FOCAL_TIME)
    assert np.all(phases >= -np.pi)
    assert np.all(phases < np.pi)


def test_single_element_and_single_frequency() -> None:
    phases = focal_phases(np.zeros((1, 3)), np.array([1.0]), _FOCAL_POINT, 0.0)
    assert phases.shape == (1, 1)


# --- physical behaviour ----------------------------------------------------


def test_symmetric_geometry_gives_symmetric_phases() -> None:
    """A linear array focused on its perpendicular bisector is symmetric."""
    positions = linear_array(9, 500.0)
    phases = focal_phases(positions, np.array([1000.0]), _FOCAL_POINT, _FOCAL_TIME)
    np.testing.assert_allclose(phases[:, 0], phases[::-1, 0], rtol=0, atol=1e-9)


def test_phase_differences_scale_linearly_with_frequency() -> None:
    """phi_a - phi_0 is proportional to f, since it is 2 pi f dR / c."""
    positions = linear_array(5, 500.0)
    freqs = np.array([100.0, 200.0])
    phases = focal_phases(positions, freqs, _FOCAL_POINT, _FOCAL_TIME)
    low = phases[:, 0] - phases[0, 0]
    high = phases[:, 1] - phases[0, 1]
    np.testing.assert_allclose(_wrap(high), _wrap(2.0 * low), rtol=1e-9, atol=1e-12)


def test_moving_the_focus_changes_the_phases() -> None:
    positions = planar_array(4, 4, 1000.0, 1000.0)
    a = focal_phases(positions, _FREQUENCIES, _FOCAL_POINT, _FOCAL_TIME)
    b = focal_phases(positions, _FREQUENCIES, _FOCAL_POINT * 0.5, _FOCAL_TIME)
    assert not np.allclose(a, b)


def test_focal_time_shifts_all_phases_in_common() -> None:
    """focal_time is a common-mode term: differential phases are unchanged."""
    positions = planar_array(4, 4, 1000.0, 1000.0)
    a = focal_phases(positions, _FREQUENCIES, _FOCAL_POINT, 0.0)
    b = focal_phases(positions, _FREQUENCIES, _FOCAL_POINT, 10.0)
    for j in range(_FREQUENCIES.size):
        da = _wrap(a[:, j] - a[0, j])
        db = _wrap(b[:, j] - b[0, j])
        np.testing.assert_allclose(da, db, rtol=0, atol=1e-12)


# --- validation ------------------------------------------------------------


def test_rejects_wrong_geometry_shape() -> None:
    with pytest.raises(ValueError, match=r"\(N, 3\)"):
        focal_phases(np.zeros((4, 2)), _FREQUENCIES, _FOCAL_POINT, 0.0)


def test_rejects_wrong_frequency_shape() -> None:
    with pytest.raises(ValueError, match=r"\(F,\)"):
        focal_phases(np.zeros((4, 3)), np.ones((2, 2)), _FOCAL_POINT, 0.0)


def test_rejects_non_positive_frequencies() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        focal_phases(np.zeros((4, 3)), np.array([1.0, 0.0]), _FOCAL_POINT, 0.0)


def test_rejects_wrong_focal_point_shape() -> None:
    with pytest.raises(ValueError, match=r"\(3,\)"):
        focal_phases(np.zeros((4, 3)), _FREQUENCIES, np.zeros(2), 0.0)


def test_rejects_non_finite_focal_time() -> None:
    with pytest.raises(ValueError, match="focal_time"):
        focal_phases(np.zeros((4, 3)), _FREQUENCIES, _FOCAL_POINT, math.inf)


def test_rejects_focus_coinciding_with_an_element() -> None:
    positions = linear_array(3, 100.0)
    with pytest.raises(ValueError, match="coincides"):
        focal_phases(positions, _FREQUENCIES, positions[1], 0.0)


def test_rejects_float32_geometry() -> None:
    """ADR-0002 §5: float32 is rejected, not upcast."""
    with pytest.raises(TypeError, match="float32"):
        focal_phases(np.zeros((4, 3), dtype=np.float32), _FREQUENCIES, _FOCAL_POINT, 0.0)
