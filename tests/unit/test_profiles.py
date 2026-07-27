"""Unit tests for gwtb.kinematics.profiles (T-3.1 through T-3.6)."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import integrate

from gwtb.kinematics.profiles import (
    AccelerationProfile,
    BangBangProfile,
    QuinticProfile,
    RaisedCosineProfile,
    SCurveProfile,
    spectrum,
)


def _first_sidelobe_db(magnitude_one_sided: np.ndarray) -> float:
    """Ratio (dB) of the first sidelobe peak to the main lobe peak, for a
    one-sided (non-negative frequency) magnitude spectrum."""
    peak_idx = int(np.argmax(magnitude_one_sided))
    i = peak_idx
    while i < len(magnitude_one_sided) - 1 and magnitude_one_sided[i + 1] <= magnitude_one_sided[i]:
        i += 1
    j = i
    while j < len(magnitude_one_sided) - 1 and magnitude_one_sided[j + 1] >= magnitude_one_sided[j]:
        j += 1
    return float(20.0 * np.log10(magnitude_one_sided[j] / magnitude_one_sided[peak_idx]))


# --- T-3.1: AccelerationProfile ABC ------------------------------------------


def test_acceleration_profile_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        AccelerationProfile()  # type: ignore[abstract]


def test_incomplete_subclass_cannot_be_instantiated() -> None:
    class _Incomplete(AccelerationProfile):
        @property
        def duration(self) -> float:
            return 1.0

        # Missing acceleration/velocity/position/jerk.

    with pytest.raises(TypeError):
        _Incomplete()  # type: ignore[abstract]


@pytest.mark.parametrize(
    "profile",
    [
        BangBangProfile(a_max=2.0, duration=4.0),
        SCurveProfile(a_max=2.0, j_max=5.0, duration=4.0),
        QuinticProfile(delta_v=3.0, duration=4.0),
        RaisedCosineProfile(delta_v=3.0, duration=4.0),
    ],
)
def test_velocity_matches_integral_of_acceleration(profile: AccelerationProfile) -> None:
    """AC: velocity/position match analytic integrals to rtol 1e-9."""
    for t in (0.5, 1.3, 2.0, 3.1, profile.duration):
        expected, _ = integrate.quad(
            lambda tau: float(profile.acceleration(tau)), 0.0, t, limit=200
        )
        actual = float(profile.velocity(t))
        if abs(expected) < 1e-12:
            assert abs(actual - expected) < 1e-9
        else:
            assert abs(actual - expected) / abs(expected) < 1e-9


@pytest.mark.parametrize(
    "profile",
    [
        BangBangProfile(a_max=2.0, duration=4.0),
        SCurveProfile(a_max=2.0, j_max=5.0, duration=4.0),
        QuinticProfile(delta_v=3.0, duration=4.0),
        RaisedCosineProfile(delta_v=3.0, duration=4.0),
    ],
)
def test_position_matches_integral_of_velocity(profile: AccelerationProfile) -> None:
    """AC: velocity/position match analytic integrals to rtol 1e-9."""
    for t in (0.5, 1.3, 2.0, 3.1, profile.duration):
        # Integrate panel-by-panel. These profiles are only *piecewise* smooth —
        # the S-curve has constant-jerk phases, so its velocity has kinks — and
        # adaptive quadrature loses precision straddling a breakpoint. A single
        # quad() call over [0, t] gives 2.3e-9 relative error against the exact
        # analytic position; subdividing confines any kink to one panel.
        # Verified: supplying the S-curve's true breakpoints gives exactly 0.0
        # relative error, so the profile is right and the measurement was wrong.
        #
        # This fixes how the comparison is *measured*. The rtol 1e-9 below is
        # the spec's acceptance criterion and is deliberately unchanged.
        n_panels = 64
        edges = [t * k / n_panels for k in range(n_panels + 1)]
        expected = sum(
            integrate.quad(lambda tau: float(profile.velocity(tau)), lo, hi, limit=200)[0]
            for lo, hi in zip(edges[:-1], edges[1:], strict=True)
        )
        actual = float(profile.position(t))
        if abs(expected) < 1e-12:
            assert abs(actual - expected) < 1e-9
        else:
            assert abs(actual - expected) / abs(expected) < 1e-9


def test_profile_methods_reject_t_outside_domain() -> None:
    profile = BangBangProfile(a_max=1.0, duration=2.0)
    with pytest.raises(ValueError):
        profile.acceleration(-0.1)
    with pytest.raises(ValueError):
        profile.acceleration(2.1)
    with pytest.raises(ValueError):
        profile.velocity(2.1)
    with pytest.raises(ValueError):
        profile.position(-0.1)


def test_profile_methods_accept_array_and_scalar_consistently() -> None:
    profile = QuinticProfile(delta_v=2.0, duration=3.0)
    times = np.array([0.0, 1.0, 2.0, 3.0])
    array_result = profile.velocity(times)
    scalar_results = np.array([profile.velocity(float(t)) for t in times])
    np.testing.assert_allclose(array_result, scalar_results, rtol=1e-15)
    assert isinstance(profile.velocity(1.5), float)
    assert isinstance(array_result, np.ndarray)
    assert array_result.dtype == np.float64


# --- T-3.2: BangBangProfile ----------------------------------------------------


def test_bang_bang_delta_v_is_a_max_times_half_duration() -> None:
    a_max, duration = 3.0, 10.0
    profile = BangBangProfile(a_max=a_max, duration=duration)
    delta_v = profile.velocity(duration)
    assert delta_v == pytest.approx(a_max * duration / 2.0, rel=1e-12)


def test_bang_bang_coasts_at_peak_velocity_in_second_half() -> None:
    a_max, duration = 3.0, 10.0
    profile = BangBangProfile(a_max=a_max, duration=duration)
    v_peak = a_max * duration / 2.0
    for t in (duration / 2.0, duration * 0.75, duration):
        assert profile.velocity(t) == pytest.approx(v_peak, rel=1e-12)
        assert profile.acceleration(t) == 0.0


def test_bang_bang_spectrum_shows_rect_window_sidelobe() -> None:
    """AC: spectrum shows -13 dB first sidelobe."""
    profile = BangBangProfile(a_max=2.0, duration=1.0)
    freqs, magnitude = spectrum(profile, n_fft=4096)
    one_sided = magnitude[: len(magnitude) // 2 + 1]
    db = _first_sidelobe_db(one_sided)
    assert db == pytest.approx(-13.3, abs=1.0)


def test_bang_bang_rejects_nonpositive_parameters() -> None:
    with pytest.raises(ValueError):
        BangBangProfile(a_max=0.0, duration=1.0)
    with pytest.raises(ValueError):
        BangBangProfile(a_max=1.0, duration=-1.0)


# --- T-3.3: SCurveProfile ------------------------------------------------------


def test_s_curve_respects_jerk_and_acceleration_bounds() -> None:
    a_max, j_max, duration = 2.0, 1.0, 10.0
    profile = SCurveProfile(a_max=a_max, j_max=j_max, duration=duration)
    t = np.linspace(0.0, duration, 5000)
    accel = profile.acceleration(t)
    jerk = profile.jerk(t)
    assert np.max(np.abs(accel)) <= a_max * (1.0 + 1e-12)
    assert np.max(np.abs(jerk)) <= j_max * (1.0 + 1e-12)


def test_s_curve_acceleration_is_continuous() -> None:
    """AC: C1 continuous (acceleration has no jumps across the ramp/cruise
    boundaries, even though jerk does)."""
    a_max, j_max, duration = 2.0, 1.0, 10.0
    profile = SCurveProfile(a_max=a_max, j_max=j_max, duration=duration)
    tau = a_max / j_max
    t2 = duration - tau
    eps = 1e-7
    for boundary in (tau, t2):
        left = float(profile.acceleration(boundary - eps))
        right = float(profile.acceleration(boundary + eps))
        assert abs(left - right) < 1e-4


def test_s_curve_requires_sufficient_duration() -> None:
    # a_max/j_max = 2.0, so duration must be >= 4.0.
    with pytest.raises(ValueError):
        SCurveProfile(a_max=2.0, j_max=1.0, duration=3.9)
    # Exactly at the boundary should succeed (pure triangular profile).
    SCurveProfile(a_max=2.0, j_max=1.0, duration=4.0)


# --- T-3.4: QuinticProfile -----------------------------------------------------


def test_quintic_endpoint_derivatives_are_zero() -> None:
    profile = QuinticProfile(delta_v=5.0, duration=7.0)
    for t in (0.0, profile.duration):
        assert abs(profile.acceleration(t)) < 1e-12
        assert abs(profile.jerk(t)) < 1e-12


def test_quintic_delta_v_is_exact() -> None:
    delta_v, duration = 5.0, 7.0
    profile = QuinticProfile(delta_v=delta_v, duration=duration)
    assert profile.velocity(0.0) == pytest.approx(0.0, abs=1e-12)
    assert profile.velocity(duration) == pytest.approx(delta_v, rel=1e-12)


# --- T-3.5: RaisedCosineProfile ------------------------------------------------


def test_raised_cosine_matches_hann_window_spectral_rolloff() -> None:
    """AC: matches a Hann window in spectral rolloff to rtol 1e-6.

    The acceleration a(t) = (delta_v/T)(1 - cos(2 pi t/T)) is exactly
    proportional to a periodic Hann window sampled the same way, so their
    (normalized) magnitude spectra should agree far tighter than rtol 1e-6;
    compared here at every bin with appreciable magnitude.
    """
    duration = 1.0
    profile = RaisedCosineProfile(delta_v=4.0, duration=duration)
    n_fft = 4096
    freqs, magnitude = spectrum(profile, n_fft=n_fft)

    # Reproduce spectrum()'s own sampling/padding convention independently
    # (rather than importing its private constant) for the reference window.
    n_samples = n_fft // 16
    hann_periodic = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(n_samples) / n_samples))
    padded = np.zeros(n_fft)
    padded[:n_samples] = hann_periodic
    hann_magnitude = np.abs(np.fft.fft(padded))

    our_norm = magnitude / magnitude[0]
    hann_norm = hann_magnitude / hann_magnitude[0]

    significant = hann_norm > 1e-6
    np.testing.assert_allclose(our_norm[significant], hann_norm[significant], rtol=1e-6, atol=1e-9)


def test_raised_cosine_acceleration_and_jerk_vanish_at_endpoints() -> None:
    profile = RaisedCosineProfile(delta_v=4.0, duration=2.5)
    for t in (0.0, profile.duration):
        assert abs(profile.acceleration(t)) < 1e-12
        assert abs(profile.jerk(t)) < 1e-12


# --- T-3.6: spectrum() ---------------------------------------------------------


def test_spectrum_parseval_holds() -> None:
    """AC: Parseval holds to rtol 1e-9."""
    profile = BangBangProfile(a_max=2.0, duration=1.0)
    n_fft = 4096
    _, magnitude = spectrum(profile, n_fft=n_fft)

    n_samples = n_fft // 16
    dt = profile.duration / n_samples
    t = np.arange(n_samples) * dt
    samples = np.asarray(profile.acceleration(t), dtype=np.float64)

    lhs = np.sum(samples**2)
    rhs = np.sum(magnitude**2) / n_fft
    assert lhs == pytest.approx(rhs, rel=1e-9)


def test_spectrum_sidelobe_levels_match_window_analogues() -> None:
    """AC: first-sidelobe levels match the window-function analogues
    (rect -13 dB, Hann -31 dB) to +/-1 dB."""
    rect_profile = BangBangProfile(a_max=1.0, duration=1.0)
    hann_profile = RaisedCosineProfile(delta_v=1.0, duration=1.0)

    _, mag_rect = spectrum(rect_profile, n_fft=8192)
    _, mag_hann = spectrum(hann_profile, n_fft=8192)

    db_rect = _first_sidelobe_db(mag_rect[: len(mag_rect) // 2 + 1])
    db_hann = _first_sidelobe_db(mag_hann[: len(mag_hann) // 2 + 1])

    assert db_rect == pytest.approx(-13.0, abs=1.0)
    assert db_hann == pytest.approx(-31.0, abs=1.0)


def test_spectrum_returns_float64_arrays_of_matching_shape() -> None:
    profile = QuinticProfile(delta_v=1.0, duration=1.0)
    freqs, magnitude = spectrum(profile, n_fft=1024)
    assert freqs.shape == (1024,)
    assert magnitude.shape == (1024,)
    assert freqs.dtype == np.float64
    assert magnitude.dtype == np.float64


def test_spectrum_rejects_nonpositive_or_too_small_n_fft() -> None:
    profile = QuinticProfile(delta_v=1.0, duration=1.0)
    with pytest.raises(ValueError):
        spectrum(profile, n_fft=0)
    with pytest.raises(ValueError):
        spectrum(profile, n_fft=-8)
    with pytest.raises(ValueError):
        spectrum(profile, n_fft=4)
