"""Unit tests for gwtb.kinematics.oscillators (T-9.1, T-9.2, T-9.3, T-9.4)."""

from __future__ import annotations

import time

import numpy as np
import pytest

from gwtb.kinematics.oscillators import (
    PrimeOscillatorDrive,
    first_n_primes,
    prime_frequencies,
    recurrence_period,
)


def test_first_10_primes() -> None:
    assert first_n_primes(10) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]


def test_first_n_primes_1000_is_fast() -> None:
    t0 = time.perf_counter()
    primes = first_n_primes(1000)
    elapsed = time.perf_counter() - t0
    assert len(primes) == 1000
    assert elapsed < 1.0


def test_first_n_primes_rejects_non_positive() -> None:
    with pytest.raises(ValueError):
        first_n_primes(0)


def test_prime_frequencies_band_scaling() -> None:
    freqs = prime_frequencies(5, unit_hz=1e6)
    np.testing.assert_allclose(freqs, np.array([2, 3, 5, 7, 11]) * 1e6, rtol=1e-12)


def test_prime_frequencies_recurrence_period_scales_with_unit() -> None:
    n = 10
    product_of_primes = float(np.prod(first_n_primes(n)))
    freqs_hz = prime_frequencies(n, unit_hz=1.0)
    freqs_mhz = prime_frequencies(n, unit_hz=1e6)
    assert recurrence_period(freqs_hz) == pytest.approx(product_of_primes, rel=1e-12)
    assert recurrence_period(freqs_mhz) * 1e6 == pytest.approx(product_of_primes, rel=1e-12)


def test_recurrence_period_first_10_primes_exact() -> None:
    freqs = prime_frequencies(10, unit_hz=1.0)
    assert recurrence_period(freqs) == pytest.approx(6.469693230e9, rel=1e-12)


def test_oscillator_drive_superposition_and_phase() -> None:
    freqs = [1.0, 3.0]
    amps = [2.0, 1.0]
    phases = [0.0, 0.5]
    drive = PrimeOscillatorDrive(freqs, amps, phases, duration=5.0)
    t = 0.37
    expected = 2.0 * np.sin(2 * np.pi * 1.0 * t + 0.0) + 1.0 * np.sin(2 * np.pi * 3.0 * t + 0.5)
    assert drive.acceleration(t) == pytest.approx(expected, rel=1e-12)
    assert drive.velocity(0.0) == pytest.approx(0.0, abs=1e-12)
    assert drive.position(0.0) == pytest.approx(0.0, abs=1e-12)


def test_oscillator_drive_velocity_matches_numerical_integral() -> None:
    drive = PrimeOscillatorDrive([1.0, 5.0], [3.0, 1.5], [0.1, -0.4], duration=2.0)
    ts = np.linspace(0.0, 2.0, 200001)
    a = np.array(drive.acceleration(ts))
    v_numeric = np.concatenate([[0.0], np.cumsum((a[1:] + a[:-1]) / 2.0 * np.diff(ts))])
    v_analytic = np.array(drive.velocity(ts))
    assert np.max(np.abs(v_numeric - v_analytic)) < 1e-4


def test_oscillator_drive_amplitude_bound() -> None:
    freqs = [1.0, 2.0, 3.0]
    amps = [1.0, 2.0, 0.5]
    drive = PrimeOscillatorDrive(freqs, amps, [0.0, 0.0, 0.0], duration=3.0)
    ts = np.linspace(0.0, 3.0, 5000)
    a = np.array(drive.acceleration(ts))
    assert np.max(np.abs(a)) <= drive.a_max + 1e-12
    assert drive.a_max == pytest.approx(3.5, rel=1e-12)
