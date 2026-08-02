"""Unit tests for gwtb.array.focus.focused_field / focused_phasor (T-9.6).

Every test here is written in a regime where it can actually fail. ADR-0006
measured four ways to write a passing but meaningless test for this function,
and each is guarded explicitly below:

1. the reference aperture is sub-wavelength at the nominal 1 kHz drive, where
   every weighting returns N and the AC passes with the logic deleted;
2. the sign convention is undetermined within a few beamwidths of broadside;
3. peak gain is N only at broadside;
4. the random-phase background mean is sqrt(N*pi)/2, not sqrt(N).
"""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.array.beamform import QuadrupoleElement, superpose_tt
from gwtb.array.focus import focal_phases, focused_field, focused_phasor
from gwtb.array.geometry import planar_array
from gwtb.core.constants import AU, c
from gwtb.kinematics.oscillators import PrimeOscillatorDrive

_R = 40.0 * AU

#: ADR-0006 trap 1: at the nominal 1 kHz the 12.4 km aperture spans 0.041
#: wavelengths and has no beam. 1 MHz gives D/lambda = 41.3.
_FREQ = 1.0e6

#: A linear quadrupole along x, per ADR-0003's analytic case.
_Q = np.array([[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 0.0]])


def _elements() -> list[QuadrupoleElement]:
    return [
        QuadrupoleElement(position=p, quadrupole=_Q) for p in planar_array(8, 8, 1250.0, 1250.0)
    ]


def _positions() -> np.ndarray:
    return planar_array(8, 8, 1250.0, 1250.0)


def _drive(frequency: float = _FREQ, amplitude: float = 1.0) -> PrimeOscillatorDrive:
    return PrimeOscillatorDrive(
        frequencies=np.array([frequency]),
        amplitudes=np.array([amplitude]),
        phases=np.array([0.0]),
        duration=1.0,
    )


def _aperture() -> float:
    p = _positions()
    return 2.0 * float(np.linalg.norm(p - p.mean(axis=0), axis=1).max())


def _beamwidth(frequency: float = _FREQ) -> float:
    return (c / frequency) / _aperture()


def _single_element_amplitude(field_point: np.ndarray, frequency: float = _FREQ) -> float:
    els = _elements()
    h = superpose_tt([els[0]], np.array([1.0 + 0j]), c / frequency, field_point)
    return float(np.abs(h).max())


# --- ADR-0006 trap 1: the test regime must have a beam at all -------------


def test_reference_aperture_has_a_beam_at_the_test_frequency() -> None:
    """Guard for trap 1 — without this, every assertion below is vacuous.

    At the project's nominal 1 kHz drive this array spans 0.041 wavelengths: a
    point source, where uniform weights already give N and the focusing logic
    could be deleted without any test noticing.
    """
    assert _aperture() / (c / _FREQ) > 1.0, "test frequency leaves the array sub-wavelength"
    assert _aperture() / (c / 1.0e3) < 1.0, "1 kHz was expected to be sub-wavelength"


# --- AC: peak amplitude at the focus is N*A, at broadside -----------------


def test_peak_at_broadside_focus_is_n_times_single_element() -> None:
    """The headline AC. Broadside only — ADR-0006 trap 3."""
    focal = np.array([0.0, 0.0, _R])
    els = _elements()
    phasor = focused_phasor(els, _drive(), focal[None, :], focal)
    peak = float(np.abs(phasor[0, 0]).max())
    np.testing.assert_allclose(peak, len(els) * _single_element_amplitude(focal), rtol=1e-6)


def test_peak_scales_linearly_with_drive_amplitude() -> None:
    focal = np.array([0.0, 0.0, _R])
    els = _elements()
    a = np.abs(focused_phasor(els, _drive(amplitude=1.0), focal[None, :], focal)).max()
    b = np.abs(focused_phasor(els, _drive(amplitude=3.0), focal[None, :], focal)).max()
    np.testing.assert_allclose(b, 3.0 * a, rtol=1e-12)


# --- ADR-0006 trap 2: pin the sign convention far off-axis ---------------


def test_sign_convention_is_correct_far_off_axis() -> None:
    """Guard for trap 2.

    Within a few beamwidths both sign conventions give ~N and a test there
    passes with the phase inverted. At 50 beamwidths the correct convention
    gives ~45 and the inverted one ~5.7, so the sign is pinned.
    """
    els = _elements()
    offset = 50.0 * _beamwidth() * _R
    focal = np.array([offset, 0.0, _R])

    correct = float(np.abs(focused_phasor(els, _drive(), focal[None, :], focal)).max())

    phi = focal_phases(_positions(), np.array([_FREQ]), focal, 0.0)[:, 0]
    inverted = float(np.abs(superpose_tt(els, np.exp(-1j * phi), c / _FREQ, focal)).max())

    assert correct > 5.0 * inverted, (
        f"sign convention not pinned: correct={correct:.4g}, inverted={inverted:.4g}"
    )


def test_focusing_beats_uniform_weighting_off_axis() -> None:
    """Steering must actually do something — the unsteered control."""
    els = _elements()
    focal = np.array([5.0 * _beamwidth() * _R, 0.0, _R])
    focused = float(np.abs(focused_phasor(els, _drive(), focal[None, :], focal)).max())
    uniform = float(
        np.abs(superpose_tt(els, np.ones(len(els), dtype=complex), c / _FREQ, focal)).max()
    )
    assert focused > 100.0 * uniform


# --- AC: peak-to-background ratio scales as sqrt(N) -----------------------


def test_peak_to_background_ratio_scales_as_sqrt_n() -> None:
    """The mode-locking signature.

    ADR-0006 trap 4: the random-phase background *mean* is the Rayleigh value
    sqrt(N*pi)/2 ~ 0.886*sqrt(N), not sqrt(N). The peak-to-background ratio is
    the quantity that scales as sqrt(N), and it is what this asserts.
    """
    els = _elements()
    n = len(els)
    focal = np.array([0.0, 0.0, _R])
    peak = float(np.abs(focused_phasor(els, _drive(), focal[None, :], focal)).max())

    rng = np.random.default_rng(0)
    background = np.array(
        [
            float(
                np.abs(
                    superpose_tt(els, np.exp(1j * rng.uniform(0, 2 * np.pi, n)), c / _FREQ, focal)
                ).max()
            )
            for _ in range(400)
        ]
    ).mean()

    ratio = peak / background
    assert ratio == pytest.approx(np.sqrt(n), rel=0.2)


def test_ratio_actually_scales_with_n_not_merely_matches_at_one_n() -> None:
    """ "Scales as sqrt(N)" needs more than one N to mean anything.

    The single-N test above pins the value; this one pins the *trend*, which is
    the actual mode-locking claim. peak = N, background = sqrt(N*pi)/2, so the
    ratio is 2*sqrt(N)/sqrt(pi) = 1.128*sqrt(N) and ratio/sqrt(N) must be flat
    across N.
    """
    focal = np.array([0.0, 0.0, _R])
    single = _single_element_amplitude(focal)
    normalised = []

    for side in (4, 8, 10):
        positions = planar_array(side, side, 1250.0, 1250.0)
        els = [QuadrupoleElement(position=p, quadrupole=_Q) for p in positions]
        n = len(els)

        peak = float(np.abs(focused_phasor(els, _drive(), focal[None, :], focal)).max())
        rng = np.random.default_rng(side)
        background = np.array(
            [
                float(
                    np.abs(
                        superpose_tt(
                            els, np.exp(1j * rng.uniform(0, 2 * np.pi, n)), c / _FREQ, focal
                        )
                    ).max()
                )
                for _ in range(200)
            ]
        ).mean()

        assert peak == pytest.approx(n * single, rel=1e-6)
        normalised.append((peak / background) / np.sqrt(n))

    # Flat across a 6.25x range in N if the scaling is sqrt(N).
    assert max(normalised) / min(normalised) < 1.15, (
        f"ratio/sqrt(N) not flat across N: {normalised}"
    )


def test_background_mean_matches_the_rayleigh_prediction_not_sqrt_n() -> None:
    """Records trap 4 explicitly, so nobody chases the 12% discrepancy.

    For random phases the sum is Rayleigh-distributed with mean sqrt(N*pi)/2.
    At N=64 that is 7.09 against a naive sqrt(N) of 8.00.
    """
    els = _elements()
    n = len(els)
    focal = np.array([0.0, 0.0, _R])
    single = _single_element_amplitude(focal)

    rng = np.random.default_rng(1)
    background = np.array(
        [
            float(
                np.abs(
                    superpose_tt(els, np.exp(1j * rng.uniform(0, 2 * np.pi, n)), c / _FREQ, focal)
                ).max()
            )
            / single
            for _ in range(400)
        ]
    ).mean()

    assert background == pytest.approx(np.sqrt(n * np.pi) / 2.0, rel=0.05)


# --- near-field requests must fail loudly (ADR-0006) ---------------------


def test_near_field_request_raises_rather_than_degrading() -> None:
    """ADR-0006: near-field focusing is out of scope and must not degrade.

    superpose_tt's Fraunhofer guard raises; focused_field propagates it rather
    than catching it, because the alternative formulation is one ADR-0003
    forbids.
    """
    els = _elements()
    inside = np.array([0.0, 0.0, 1.0e3])  # well inside 2 D^2 / lambda ~ 1.0e6 m
    with pytest.raises(ValueError, match="near field"):
        focused_phasor(els, _drive(), inside[None, :], inside)


# --- time-domain behaviour -------------------------------------------------


def test_field_shape_follows_the_propagate_convention() -> None:
    els = _elements()
    focal = np.array([0.0, 0.0, _R])
    points = np.array([focal, focal * 1.0001])
    times = np.linspace(0.0, 1.0e-6, 7)
    h = focused_field(els, _drive(), points, times, focal)
    assert h.shape == (2, 7, 3, 3)
    assert h.dtype == np.float64


def test_time_series_envelope_matches_the_phasor_magnitude() -> None:
    """The time series must be the phasor's oscillation, not an independent path."""
    els = _elements()
    focal = np.array([0.0, 0.0, _R])
    times = np.linspace(0.0, 1.0 / _FREQ, 20001)
    h = focused_field(els, _drive(), focal[None, :], times, focal)
    envelope = float(np.abs(h[0, :, 0, 0]).max())
    expected = float(np.abs(focused_phasor(els, _drive(), focal[None, :], focal)[0, 0, 0, 0]))
    np.testing.assert_allclose(envelope, expected, rtol=1e-6)


def test_field_is_symmetric_and_traceless_at_every_time() -> None:
    els = _elements()
    focal = np.array([0.0, 0.0, _R])
    h = focused_field(els, _drive(), focal[None, :], np.linspace(0.0, 1e-6, 5), focal)
    for slice_ in h[0]:
        np.testing.assert_allclose(slice_, slice_.T, rtol=1e-12, atol=0.0)
        assert abs(np.trace(slice_)) < 1e-9 * np.abs(slice_).max()


def test_multi_tone_drive_superposes_its_tones() -> None:
    """A prime-frequency comb is the point of Sprint 9's drive."""
    els = _elements()
    focal = np.array([0.0, 0.0, _R])
    freqs = np.array([2.0, 3.0, 5.0]) * _FREQ
    drive = PrimeOscillatorDrive(
        frequencies=freqs,
        amplitudes=np.ones(3),
        phases=np.zeros(3),
        duration=1.0,
    )
    phasor = focused_phasor(els, drive, focal[None, :], focal)
    assert phasor.shape == (1, 3, 3, 3)
    # Every tone focuses coherently at the same point.
    for j in range(3):
        peak = float(np.abs(phasor[0, j]).max())
        expected = len(els) * _single_element_amplitude(focal, float(freqs[j]))
        np.testing.assert_allclose(peak, expected, rtol=1e-6)


# --- validation ------------------------------------------------------------


def test_rejects_empty_array() -> None:
    focal = np.array([0.0, 0.0, _R])
    with pytest.raises(ValueError, match="non-empty"):
        focused_phasor([], _drive(), focal[None, :], focal)


def test_rejects_wrong_field_point_shape() -> None:
    focal = np.array([0.0, 0.0, _R])
    with pytest.raises(ValueError, match=r"\(N, 3\)"):
        focused_phasor(_elements(), _drive(), np.zeros((4, 2)), focal)


def test_rejects_wrong_times_shape() -> None:
    focal = np.array([0.0, 0.0, _R])
    with pytest.raises(ValueError, match=r"\(T,\)"):
        focused_field(_elements(), _drive(), focal[None, :], np.zeros((2, 2)), focal)
