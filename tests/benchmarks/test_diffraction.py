"""Benchmark: diffraction limit (T-10.2).

Two AC clauses:

1. Numerically recovered spot size matches lambda*r/D to rtol 1e-2.
2. A 1 km spot at 40 AU requires D/lambda >~ 6e9, **independent of
   frequency**, asserted across 4 decades of frequency.

The "numerically recovered" half is a genuinely independent check: a filled
circular aperture's far-field diffraction pattern is simulated directly
(summing per-element phasors, not calling spot_size), and its measured -3 dB
half-width is compared against gwtb.array.focus.spot_size's closed form.
"""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.array.focus import FWHM_COEFFICIENT, spot_size
from gwtb.core.constants import AU, c


def _filled_disk(diameter: float, n_across: int = 121) -> np.ndarray:
    """A dense, uniform, circular aperture."""
    axis = np.linspace(-diameter / 2.0, diameter / 2.0, n_across)
    gx, gy = np.meshgrid(axis, axis, indexing="ij")
    inside = (gx**2 + gy**2) <= (diameter / 2.0) ** 2
    positions = np.zeros((int(inside.sum()), 3))
    positions[:, 0] = gx[inside]
    positions[:, 1] = gy[inside]
    return positions


def _measured_spot_size(diameter: float, wavelength: float, range_m: float) -> float:
    """Simulate the filled-aperture diffraction pattern and measure its -3 dB
    transverse extent at range_m, entirely independent of spot_size()."""
    positions = _filled_disk(diameter)
    k = 2.0 * np.pi / wavelength

    theta = np.linspace(0.0, 3.0 * wavelength / diameter, 4001)
    phase = k * np.outer(np.sin(theta), positions[:, 0])
    pattern = np.abs(np.exp(1j * phase).sum(axis=1))
    power = (pattern / pattern[0]) ** 2

    below = np.flatnonzero(power <= 0.5)[0]
    theta_half = np.interp(0.5, [power[below], power[below - 1]], [theta[below], theta[below - 1]])
    return 2.0 * theta_half * range_m  # full width, transverse extent at range


@pytest.mark.parametrize(
    ("diameter", "frequency"),
    # D/lambda well above 1 in each case (ADR-0006 trap 1: a sub-wavelength
    # "aperture" has no main lobe at all, and the diffraction sweep below
    # breaks down).
    [(1.0e4, 1.0e6), (3.0e4, 5.0e5), (5.0e3, 2.0e6)],
)
def test_numerically_recovered_spot_size_matches_lambda_r_over_d(
    diameter: float, frequency: float
) -> None:
    """AC clause 1: rtol 1e-2."""
    wavelength = c / frequency
    range_m = 1.0e6

    measured = _measured_spot_size(diameter, wavelength, range_m)
    closed_form = spot_size(_filled_disk(diameter), wavelength, range_m)

    assert measured == pytest.approx(closed_form, rel=1e-2)
    # Also matches the bare w ~ lambda*r/D scaling the AC names directly.
    naive = wavelength * range_m / diameter
    assert measured == pytest.approx(naive, rel=0.05)


def test_required_aperture_is_independent_of_frequency_across_four_decades() -> None:
    """AC clause 2: D/lambda >~ 6e9 for a 1 km spot at 40 AU, independent of
    frequency, across 4 decades."""
    target_spot = 1.0e3
    range_m = 40.0 * AU

    required_d_over_lambda = FWHM_COEFFICIENT * range_m / target_spot
    assert required_d_over_lambda == pytest.approx(6.16e9, rel=0.05)

    ratios = []
    for frequency in (1.0e3, 1.0e4, 1.0e5, 1.0e6, 1.0e7):  # 4 decades
        wavelength = c / frequency
        diameter = required_d_over_lambda * wavelength
        w = spot_size(np.array([[-diameter / 2, 0, 0], [diameter / 2, 0, 0]]), wavelength, range_m)
        assert w == pytest.approx(target_spot, rel=1e-6)
        ratios.append(diameter / wavelength)

    assert max(ratios) / min(ratios) == pytest.approx(1.0, abs=1e-9)


def test_diffraction_limit_holds_at_a_second_target_spot_size() -> None:
    """Guards against the frequency-independence being an artifact of the
    specific 1 km / 40 AU numbers."""
    target_spot = 10.0
    range_m = 1.0 * AU
    required_d_over_lambda = FWHM_COEFFICIENT * range_m / target_spot

    for frequency in (1.0e2, 1.0e5, 1.0e8):
        wavelength = c / frequency
        diameter = required_d_over_lambda * wavelength
        w = spot_size(np.array([[-diameter / 2, 0, 0], [diameter / 2, 0, 0]]), wavelength, range_m)
        assert w == pytest.approx(target_spot, rel=1e-6)
