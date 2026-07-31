"""Unit tests for gwtb.core.backend.split_phase (T-11.3).

The acceptance criterion is two-sided, and the second half is the important
one: the split must work, *and* the naive FP32 path must be shown to fail the
same check. A test that only demonstrated success would leave the reader with
no evidence that the decomposition earns its complexity.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal, getcontext

import numpy as np
import pytest

from gwtb.core.backend import SplitPhase, split_phase
from gwtb.core.constants import AU, c

getcontext().prec = 60

_PI = Decimal("3.14159265358979323846264338327950288419716939937510")

#: The acceptance geometry: a 10 km aperture viewed from 40 AU.
_APERTURE = 1.0e4
_RANGE = 40.0 * AU
_WAVELENGTH = c / 1.0e3  # 1 kHz drive


def _geometry(n: int = 64, seed: int = 3) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    offsets = np.zeros((n, 3))
    offsets[:, 0] = rng.uniform(-_APERTURE / 2, _APERTURE / 2, n)
    offsets[:, 1] = rng.uniform(-_APERTURE / 2, _APERTURE / 2, n)
    return np.array([0.0, 0.0, _RANGE]), offsets


def _exact_phases(s: np.ndarray, q: np.ndarray, wavelength: float) -> np.ndarray:
    """Per-element phase in 60-digit decimal arithmetic."""
    k = 2 * _PI / Decimal(float(wavelength))
    out = []
    for offset in q:
        total = Decimal(0)
        for i in range(3):
            d = Decimal(float(s[i])) - Decimal(float(offset[i]))
            total += d * d
        out.append(k * total.sqrt())
    return np.array([float(p) for p in out])


def _exact_differentials(s: np.ndarray, q: np.ndarray, wavelength: float) -> np.ndarray:
    """Exact phases relative to the reference range, avoiding float overflow."""
    k = 2 * _PI / Decimal(float(wavelength))
    ref = Decimal(0)
    for i in range(3):
        ref += Decimal(float(s[i])) * Decimal(float(s[i]))
    ref = ref.sqrt()

    out = []
    for offset in q:
        total = Decimal(0)
        for i in range(3):
            d = Decimal(float(s[i])) - Decimal(float(offset[i]))
            total += d * d
        out.append(float(k * (total.sqrt() - ref)))
    return np.array(out)


# --- AC: recombined phase matches full FP64 to < 1e-5 rad -----------------


def test_recombined_matches_exact_to_better_than_1e_5_rad() -> None:
    """The headline criterion, for D = 10 km at 40 AU.

    Stated as written: the recombined phase must agree with the full-float64
    absolute phase to better than 1e-5 rad. Both are degenerate at this range
    (see ``test_absolute_phase_defeats_float64_too_not_only_float32``), so this
    passes — but it passes for a reason the criterion does not capture, and the
    test below on ``phasor()`` is the one with physical content.
    """
    s, q = _geometry()
    split = split_phase(s, q, _WAVELENGTH)

    wavenumber = 2.0 * np.pi / _WAVELENGTH
    full_fp64 = wavenumber * np.linalg.norm(s - q, axis=1)
    assert np.max(np.abs(split.recombine() - full_fp64)) < 1e-5


def test_phasor_matches_exact_differential_to_better_than_1e_5_rad() -> None:
    """The criterion with physical content: element-to-element phase."""
    s, q = _geometry()
    split = split_phase(s, q, _WAVELENGTH)

    relative = split.phasor() / split.phasor()[0]
    exact = _exact_differentials(s, q, _WAVELENGTH)
    expected = exact - exact[0]
    assert np.max(np.abs(np.angle(relative) - expected)) < 1e-5


def test_holds_across_four_decades_of_frequency() -> None:
    s, q = _geometry()
    for frequency in (1.0e1, 1.0e2, 1.0e3, 1.0e4):
        wavelength = c / frequency
        split = split_phase(s, q, wavelength)
        relative = split.phasor() / split.phasor()[0]
        exact = _exact_differentials(s, q, wavelength)
        expected = exact - exact[0]
        assert np.max(np.abs(np.angle(relative) - expected)) < 1e-5, f"{frequency} Hz"


# --- AC: naive FP32 fails the same check ---------------------------------


def test_naive_fp32_fails_the_same_check() -> None:
    """Why the decomposition exists (CLAUDE.md rule 3, ADR-0002 §5).

    At 40 AU and 1 kHz the absolute propagation phase is ~1.25e8 rad, where the
    float32 spacing is **8 rad** — wider than a full 2 pi cycle. Storing the
    absolute phase in float32 does not degrade the interference pattern, it
    erases it: every representable value is more than one cycle from its
    neighbour.
    """
    s, q = _geometry()
    exact_absolute = _exact_phases(s, q, _WAVELENGTH)

    naive = exact_absolute.astype(np.float32).astype(np.float64)
    naive_error = np.max(np.abs(naive - exact_absolute))
    assert naive_error > 1e-5, "naive float32 was expected to fail the criterion"
    assert float(np.spacing(np.float32(exact_absolute[0]))) > 2.0 * np.pi

    split = split_phase(s, q, _WAVELENGTH)
    ours = split.recombine() - split.reference
    assert np.max(np.abs(ours - _exact_differentials(s, q, _WAVELENGTH))) < 1e-5


def test_absolute_phase_defeats_float64_too_not_only_float32() -> None:
    """**Finding:** the split is required even for an all-FP64 pipeline.

    T-11.3 is framed as enabling an FP32 path, and it does. But the sharper
    result is that forming *absolute* phases and subtracting them loses the
    signal in float64 as well. At 40 AU / 1 kHz:

    * absolute phase ~1.25e8 rad, float64 spacing there ~1.49e-8 rad;
    * the entire differential across a 10 km aperture is ~4.4e-11 rad.

    The float64 resolution of the absolute phase is therefore ~340x *larger*
    than the whole quantity being measured. Any pipeline that computes
    ``k*R_a`` per element and differences the results gets zero, in float64,
    for the same reason the naive range differencing in
    ``tests/unit/test_focus.py`` does. The reference/differential split is not
    an FP32 optimisation — it is the only way to obtain the number at all.

    This is a wall, not a defect (CLAUDE.md rule 5): it does not go away with a
    wider float, only with a formulation that never forms the large term.
    """
    s, q = _geometry()
    exact_differential = _exact_differentials(s, q, _WAVELENGTH)
    differential_spread = float(np.ptp(exact_differential))
    assert differential_spread > 0.0

    split = split_phase(s, q, _WAVELENGTH)
    float64_resolution = float(np.spacing(split.reference))
    assert float64_resolution > 100.0 * differential_spread

    # The naive all-float64 route: form absolute phases, then difference.
    wavenumber = 2.0 * np.pi / _WAVELENGTH
    naive_absolute = wavenumber * np.linalg.norm(s - q, axis=1)
    naive_differential = naive_absolute - naive_absolute[0]
    assert np.ptp(naive_differential) == 0.0, "expected float64 to lose it entirely"

    # recombine() cannot rescue it either — adding the differential to the
    # reference absorbs it. This is asserted, not worked around, because it is
    # the reason phasor() exists.
    assert np.ptp(split.recombine()) == 0.0

    # phasor() does, because phasors multiply rather than adding phases.
    relative = split.phasor() / split.phasor()[0]
    recovered = np.angle(relative)
    expected = exact_differential - exact_differential[0]
    assert np.max(np.abs(recovered - expected)) < 1e-5
    assert np.ptp(recovered) > 0.0, "phasor() must preserve the element structure"


def test_differential_fits_comfortably_in_float32() -> None:
    """The premise of the split: the residual has small dynamic range."""
    s, q = _geometry()
    split = split_phase(s, q, _WAVELENGTH)
    assert split.differential.dtype == np.float32
    # float32 resolution at this magnitude must be far below the 1e-5 budget.
    largest = float(np.max(np.abs(split.differential)))
    assert np.spacing(np.float32(largest)) < 1e-6


# --- structure and contracts ----------------------------------------------


def test_reference_is_float64_and_differential_is_float32() -> None:
    s, q = _geometry()
    split = split_phase(s, q, _WAVELENGTH)
    assert isinstance(split.reference, float)
    assert split.differential.dtype == np.float32
    assert split.recombine().dtype == np.float64


def test_shapes_follow_the_element_axis() -> None:
    s, q = _geometry(n=17)
    split = split_phase(s, q, _WAVELENGTH)
    assert split.differential.shape == (17,)
    assert split.recombine().shape == (17,)


def test_wavelength_is_retained() -> None:
    s, q = _geometry()
    assert split_phase(s, q, _WAVELENGTH).wavelength == _WAVELENGTH


def test_element_at_the_reference_has_zero_differential() -> None:
    s = np.array([0.0, 0.0, _RANGE])
    q = np.zeros((1, 3))
    split = split_phase(s, q, _WAVELENGTH)
    assert abs(float(split.differential[0])) < 1e-9


def test_phase_scales_inversely_with_wavelength() -> None:
    s, q = _geometry()
    a = split_phase(s, q, _WAVELENGTH)
    b = split_phase(s, q, _WAVELENGTH / 2.0)
    assert b.reference == pytest.approx(2.0 * a.reference, rel=1e-12)


def test_split_phase_is_frozen() -> None:
    s, q = _geometry()
    with pytest.raises(FrozenInstanceError):
        split_phase(s, q, _WAVELENGTH).reference = 0.0  # type: ignore[misc]


# --- validation ------------------------------------------------------------


def test_rejects_wrong_reference_shape() -> None:
    with pytest.raises(ValueError, match=r"\(3,\)"):
        split_phase(np.zeros(2), np.zeros((4, 3)), _WAVELENGTH)


def test_rejects_wrong_offsets_shape() -> None:
    with pytest.raises(ValueError, match=r"\(N, 3\)"):
        split_phase(np.array([0.0, 0.0, 1.0]), np.zeros((4, 2)), _WAVELENGTH)


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_rejects_non_positive_wavelength(bad: float) -> None:
    with pytest.raises(ValueError, match="wavelength"):
        split_phase(np.array([0.0, 0.0, 1.0]), np.zeros((4, 3)), bad)


def test_rejects_zero_reference_geometry() -> None:
    with pytest.raises(ValueError, match="coincides"):
        split_phase(np.zeros(3), np.zeros((4, 3)), _WAVELENGTH)


def test_rejects_float32_input() -> None:
    """ADR-0002 §5: float32 *input* is still rejected.

    The split produces an FP32 differential as an output representation; it
    does not license FP32 geometry on the way in, where precision would already
    have been lost before the decomposition could help.
    """
    s, q = _geometry()
    with pytest.raises(TypeError, match="float32"):
        split_phase(s.astype(np.float32), q, _WAVELENGTH)


def test_recombine_matches_manual_addition() -> None:
    s, q = _geometry()
    split = split_phase(s, q, _WAVELENGTH)
    manual = split.reference + split.differential.astype(np.float64)
    np.testing.assert_array_equal(split.recombine(), manual)


def test_is_a_split_phase_instance() -> None:
    s, q = _geometry()
    assert isinstance(split_phase(s, q, _WAVELENGTH), SplitPhase)
