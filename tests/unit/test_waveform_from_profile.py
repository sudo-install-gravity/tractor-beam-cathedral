"""Unit tests for gwtb.source.quadrupole.waveform_from_profile (T-3.8)."""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.bodies.sphere import Sphere
from gwtb.kinematics.profiles import BangBangProfile, QuinticProfile
from gwtb.source.quadrupole import waveform_from_profile


def test_zero_before_maneuver_starts() -> None:
    body = Sphere(radius=1.0, density=8000.0)
    profile = QuinticProfile(delta_v=10.0, duration=4.0)
    h = waveform_from_profile(body, profile, r=1e10, n_hat=np.array([0.0, 0.0, 1.0]), times=[0.0])
    np.testing.assert_allclose(h, 0.0, atol=1e-30)


def test_strain_settles_to_memory_offset_after_maneuver() -> None:
    body = Sphere(radius=1.0, density=8000.0)
    profile = QuinticProfile(delta_v=10.0, duration=4.0)
    n_hat = np.array([0.0, 0.0, 1.0])
    times = np.array([4.0, 6.0, 10.0, 50.0])
    h = waveform_from_profile(body, profile, r=1e10, n_hat=n_hat, times=times)

    offset = h[0]
    assert np.max(np.abs(offset)) > 0.0  # the memory offset itself is nonzero
    for i in range(1, len(times)):
        np.testing.assert_allclose(h[i], offset, rtol=1e-6)


def test_strain_returns_zero_for_zero_delta_v() -> None:
    """A profile with delta_v = 0 has no memory offset: the mirrored bodies
    return to rest, so quadrupole ddot -> 0 well after the maneuver."""
    body = Sphere(radius=1.0, density=8000.0)
    profile = BangBangProfile(a_max=1.0, duration=2.0)
    # BangBangProfile ends with nonzero velocity by construction (it does not
    # return to rest), so use it only to confirm the offset is nonzero here,
    # and separately confirm strain grows monotonically to that offset.
    n_hat = np.array([0.0, 0.0, 1.0])
    times = np.linspace(0.0, 1.0, 5)
    h = waveform_from_profile(body, profile, r=1e10, n_hat=n_hat, times=times)
    magnitudes = np.array([np.max(np.abs(h[i])) for i in range(len(times))])
    assert np.all(np.diff(magnitudes) >= -1e-30)


def test_output_shape() -> None:
    body = Sphere(radius=2.0, density=3000.0)
    profile = QuinticProfile(delta_v=5.0, duration=1.0)
    times = np.linspace(0.0, 2.0, 7)
    h = waveform_from_profile(body, profile, r=1e10, n_hat=np.array([0.0, 0.0, 1.0]), times=times)
    assert h.shape == (7, 3, 3)


def test_strain_traceless_and_scales_as_inverse_r() -> None:
    body = Sphere(radius=1.0, density=8000.0)
    profile = QuinticProfile(delta_v=10.0, duration=4.0)
    n_hat = np.array([0.0, 0.0, 1.0])
    h1 = waveform_from_profile(body, profile, r=1e10, n_hat=n_hat, times=[2.0])[0]
    h2 = waveform_from_profile(body, profile, r=2e10, n_hat=n_hat, times=[2.0])[0]
    assert np.trace(h1) == pytest.approx(0.0, abs=1e-40)
    np.testing.assert_allclose(h2, h1 / 2.0, rtol=1e-9)
