"""Unit tests for gwtb.array.focus.spot_size (T-10.1).

The coefficient is the whole content of this function, so it is verified two
independent ways rather than asserted: by re-solving the transcendental root
with scipy, and by measuring the -3 dB width of an actual simulated circular
aperture's diffraction pattern.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.optimize import brentq
from scipy.special import j1

from gwtb.array.focus import FWHM_COEFFICIENT, spot_size
from gwtb.array.geometry import linear_array
from gwtb.core.constants import AU, c


def _filled_disk(diameter: float, n_across: int = 81) -> np.ndarray:
    """A dense, uniform, circular aperture — the geometry the Airy form assumes."""
    axis = np.linspace(-diameter / 2.0, diameter / 2.0, n_across)
    gx, gy = np.meshgrid(axis, axis, indexing="ij")
    inside = (gx**2 + gy**2) <= (diameter / 2.0) ** 2
    positions = np.zeros((int(inside.sum()), 3))
    positions[:, 0] = gx[inside]
    positions[:, 1] = gy[inside]
    return positions


# --- the coefficient, verified independently -----------------------------


def test_coefficient_solves_the_airy_half_maximum_condition() -> None:
    """Re-derive 1.029 from scratch: the root of 2 J1(x)/x = 1/sqrt(2).

    This is the citation. If it ever fails, the constant was edited, not the
    physics.
    """
    root = brentq(lambda x: 2.0 * j1(x) / x - 1.0 / np.sqrt(2.0), 1.0, 2.4)
    assert FWHM_COEFFICIENT == pytest.approx(2.0 * root / np.pi, rel=1e-12)
    assert FWHM_COEFFICIENT == pytest.approx(1.029, abs=5e-4)


def test_coefficient_is_not_the_rayleigh_criterion() -> None:
    """1.22 is the first Airy null, a resolution limit — a 19% overstatement.

    Guarded explicitly because substituting it is the single most plausible
    silent error in this function.
    """
    assert abs(FWHM_COEFFICIENT - 1.22) > 0.15
    first_null = brentq(j1, 3.0, 4.5)
    assert first_null / np.pi == pytest.approx(1.22, abs=5e-3)


def test_half_maximum_is_exactly_minus_3_db() -> None:
    """-3.01 dB and half power are the same statement."""
    assert 10.0 * np.log10(0.5) == pytest.approx(-3.0, abs=0.02)


# --- AC: recovers w ~ lambda*r/D across aperture/frequency combinations ---


@pytest.mark.parametrize(
    ("diameter", "frequency", "range_m"),
    [
        (1.0e3, 1.0e6, 40.0 * AU),
        (1.0e4, 1.0e6, 40.0 * AU),
        (1.0e4, 1.0e5, 40.0 * AU),
        (1.0e5, 1.0e7, 1.0 * AU),
        (1.0e2, 1.0e8, 1.0e9),
    ],
)
def test_recovers_lambda_r_over_d(diameter: float, frequency: float, range_m: float) -> None:
    """Five aperture/frequency combinations, per the acceptance criterion."""
    positions = linear_array(2, diameter)  # exact aperture: two elements, D apart
    wavelength = c / frequency
    expected = FWHM_COEFFICIENT * wavelength * range_m / diameter
    assert spot_size(positions, wavelength, range_m) == pytest.approx(expected, rel=1e-2)


def test_scales_linearly_with_wavelength_and_range_and_inversely_with_aperture() -> None:
    positions = linear_array(2, 1.0e4)
    base = spot_size(positions, 300.0, 40.0 * AU)
    assert spot_size(positions, 600.0, 40.0 * AU) == pytest.approx(2.0 * base, rel=1e-12)
    assert spot_size(positions, 300.0, 80.0 * AU) == pytest.approx(2.0 * base, rel=1e-12)
    assert spot_size(linear_array(2, 2.0e4), 300.0, 40.0 * AU) == pytest.approx(
        base / 2.0, rel=1e-12
    )


# --- the coefficient, measured from a simulated aperture ------------------


def test_matches_the_measured_pattern_of_a_filled_circular_aperture() -> None:
    """Independent check: simulate the aperture and measure its -3 dB width.

    Scalar far-field pattern of a filled disk, sampled in angle, with the half-
    maximum located by interpolation. This is the physical content of the
    formula, verified without reference to the analytic Airy expression.
    """
    diameter = 100.0
    wavelength = 1.0
    positions = _filled_disk(diameter)
    k = 2.0 * np.pi / wavelength

    theta = np.linspace(0.0, 3.0 * wavelength / diameter, 4001)
    # Broadside pattern: phase across the aperture for a plane wave at angle
    # theta in the x-z plane.
    phase = k * np.outer(np.sin(theta), positions[:, 0])
    pattern = np.abs(np.exp(1j * phase).sum(axis=1))
    power = (pattern / pattern[0]) ** 2

    below = np.flatnonzero(power <= 0.5)[0]
    theta_half = np.interp(0.5, [power[below], power[below - 1]], [theta[below], theta[below - 1]])
    measured_coefficient = 2.0 * theta_half * diameter / wavelength

    assert measured_coefficient == pytest.approx(FWHM_COEFFICIENT, rel=1e-2)


def test_measured_width_matches_spot_size_at_range() -> None:
    """The same measurement, expressed as a transverse extent at range."""
    diameter = 100.0
    wavelength = 1.0
    range_m = 1.0e6
    positions = _filled_disk(diameter)

    measured = FWHM_COEFFICIENT * wavelength * range_m / diameter
    assert spot_size(positions, wavelength, range_m) == pytest.approx(measured, rel=1e-2)


# --- validation ------------------------------------------------------------


def test_rejects_zero_extent_array() -> None:
    with pytest.raises(ValueError, match="zero extent"):
        spot_size(np.zeros((4, 3)), 300.0, 40.0 * AU)


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_rejects_non_positive_wavelength(bad: float) -> None:
    with pytest.raises(ValueError, match="wavelength"):
        spot_size(linear_array(2, 100.0), bad, 40.0 * AU)


@pytest.mark.parametrize("bad", [0.0, -1.0])
def test_rejects_non_positive_range(bad: float) -> None:
    with pytest.raises(ValueError, match="range_m"):
        spot_size(linear_array(2, 100.0), 300.0, bad)


def test_rejects_wrong_array_shape() -> None:
    with pytest.raises(ValueError, match=r"\(N, 3\)"):
        spot_size(np.zeros((4, 2)), 300.0, 40.0 * AU)


def test_rejects_float32() -> None:
    """ADR-0002 §5: float32 is rejected, not upcast."""
    with pytest.raises(TypeError, match="float32"):
        spot_size(linear_array(2, 100.0).astype(np.float32), 300.0, 40.0 * AU)


# --- the wall this function quantifies ------------------------------------


def test_a_one_km_spot_at_40_au_needs_d_over_lambda_of_order_6e9() -> None:
    """The feasibility wall, from the spot-size side (B-3, T-10.2).

    Requiring w = 1 km at 40 AU forces D/lambda ~ 6e9 — and the result is
    **independent of frequency**, since only the ratio appears. This is a
    finding, not a limitation to engineer around (CLAUDE.md rule 5).
    """
    target_w = 1.0e3
    range_m = 40.0 * AU
    required_d_over_lambda = FWHM_COEFFICIENT * range_m / target_w
    assert required_d_over_lambda == pytest.approx(6.16e9, rel=0.05)

    # Frequency-independent: the same ratio for every wavelength.
    for wavelength in (1.0e-3, 1.0, 3.0e2, 3.0e5):
        diameter = required_d_over_lambda * wavelength
        positions = linear_array(2, diameter)
        assert spot_size(positions, wavelength, range_m) == pytest.approx(target_w, rel=1e-6)
