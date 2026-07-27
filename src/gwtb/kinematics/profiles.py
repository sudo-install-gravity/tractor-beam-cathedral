"""Finite-maneuver acceleration profiles and their spectral analysis.

A "finite maneuver" is a non-impulsive, finite-duration acceleration burst
along a single axis — the kinematic building block that
:func:`gwtb.source.quadrupole.waveform_from_profile` (T-3.8) turns into a
strain waveform. ``docs/PHYSICS.md`` §4 makes the key physical point: the
acceleration profile *is* the transmit pulse shape, and its spectral content
follows the same mathematics as radar/DSP pulse shaping — a rectangular
(bang-bang) profile behaves like a rectangular window (-13 dB first
sidelobe); a raised-cosine profile behaves like a Hann window (-31 dB).

Every profile here represents a single burst taking a body from rest
(``v(0) = 0``) to a final velocity ``v(duration)`` that is, in general,
nonzero — this is deliberate: a maneuver that returns to rest leaves no net
velocity change and therefore no gravitational-wave memory (see
``docs/PHYSICS.md`` §4 and T-3.8's acceptance criterion).

**Analytic derivatives and integrals only.** Every subclass supplies closed
forms for acceleration, jerk, velocity, and position; none are obtained by
numerical differentiation or integration (CLAUDE.md: "Analytic derivatives
only — never finite-difference inside ``src/``"). This module is not in the
citation-enforced package list (``source``, ``propagate``, ``bodies``,
``array``) since these are kinematic/DSP constructions rather than physics
results with an equation number to check, but sources are noted where one
exists.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.validation import as_float64


def _prepare_time(t: ArrayLike) -> tuple[NDArray[np.float64], bool]:
    """Coerce a time argument to a 1-D float64 array; remember if it was a
    scalar so results can be handed back in the same shape."""
    raw = np.asarray(t)
    scalar = raw.ndim == 0
    validated = as_float64(np.atleast_1d(raw), "t")
    return validated, scalar


def _finish(result: NDArray[np.float64], scalar: bool) -> float | NDArray[np.float64]:
    """Undo :func:`_prepare_time`'s ``atleast_1d`` for scalar callers."""
    if scalar:
        return float(result[0])
    return result


def _require_positive_finite(value: float, name: str) -> float:
    if not np.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be positive and finite, got {value!r}")
    return float(value)


def _require_finite(value: float, name: str) -> float:
    if not np.isfinite(value):
        raise ValueError(f"{name} must be finite, got {value!r}")
    return float(value)


class AccelerationProfile(ABC):
    """Abstract base for a finite-duration, single-axis acceleration maneuver.

    A profile describes scalar kinematics (acceleration, its time integrals
    velocity/position, and its time derivative jerk) along one caller-chosen
    axis, defined for ``t`` in ``[0, duration]``. Concrete subclasses supply
    closed-form expressions for all four; the base class enforces that
    subclasses implement all of them (Python's ``ABC``/``abstractmethod``
    machinery raises ``TypeError`` on an attempt to instantiate an incomplete
    subclass) and provides shared time-domain validation.

    Every method accepts a scalar or array-like ``t`` and returns a value of
    the same shape (float in, float out; array in, array out).
    """

    @property
    @abstractmethod
    def duration(self) -> float:
        """Total maneuver duration, s."""

    @abstractmethod
    def acceleration(self, t: ArrayLike) -> float | NDArray[np.float64]:
        """Scalar acceleration ``a(t)``, m/s^2."""

    @abstractmethod
    def velocity(self, t: ArrayLike) -> float | NDArray[np.float64]:
        """Scalar velocity ``v(t)``, m/s. ``v(0) = 0`` for every profile here."""

    @abstractmethod
    def position(self, t: ArrayLike) -> float | NDArray[np.float64]:
        """Scalar position ``x(t)``, m. ``x(0) = 0`` for every profile here."""

    @abstractmethod
    def jerk(self, t: ArrayLike) -> float | NDArray[np.float64]:
        """Scalar jerk ``da/dt``, m/s^3."""

    def _validate_domain(self, t: NDArray[np.float64]) -> None:
        """Public methods are defined only on ``[0, duration]``; ADR-0002 §8
        validates at the public boundary rather than silently extrapolating.
        Callers needing post-maneuver "coasting" behavior (e.g.
        :func:`gwtb.source.quadrupole.waveform_from_profile`) must implement
        it explicitly against the clamped endpoints."""
        if np.any(t < 0.0) or np.any(t > self.duration):
            raise ValueError(
                f"t must lie within [0, {self.duration!r}] (this profile's duration); "
                f"got range [{float(np.min(t))!r}, {float(np.max(t))!r}]"
            )


class BangBangProfile(AccelerationProfile):
    """Rectangular ("bang-bang") acceleration profile.

    Accelerates at the constant rate ``a_max`` for the first half of
    ``duration``, then coasts (zero acceleration) for the second half:

    .. code-block:: text

        a(t) = a_max,   0 <= t <  duration/2
        a(t) = 0,       duration/2 <= t <= duration

    This is "rectangular" in the same sense as a DSP rectangular window:
    constant amplitude over its support (here, the first half of the
    observation window), zero elsewhere. Its acceleration spectrum therefore
    shows the classic rectangular-window first sidelobe at -13 dB (verified
    numerically in ``tests/unit/test_profiles.py``; the sidelobe ratio of a
    top-hat pulse is scale/position-invariant, so this holds regardless of
    where within the window the "on" phase sits).

    Net velocity change over the full profile: ``delta_v = a_max *
    duration / 2`` (the body coasts at this velocity for the second half).
    """

    def __init__(self, a_max: float, duration: float) -> None:
        self._a_max = _require_positive_finite(a_max, "a_max")
        self._duration = _require_positive_finite(duration, "duration")

    @property
    def duration(self) -> float:
        return self._duration

    def acceleration(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        half = self._duration / 2.0
        result: NDArray[np.float64] = np.where(arr < half, self._a_max, 0.0)
        return _finish(result, scalar)

    def velocity(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        half = self._duration / 2.0
        v_peak = self._a_max * half
        result: NDArray[np.float64] = np.where(arr < half, self._a_max * arr, v_peak)
        return _finish(result, scalar)

    def position(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        half = self._duration / 2.0
        v_peak = self._a_max * half
        x_half = 0.5 * self._a_max * half**2
        result: NDArray[np.float64] = np.where(
            arr < half,
            0.5 * self._a_max * arr**2,
            x_half + v_peak * (arr - half),
        )
        return _finish(result, scalar)

    def jerk(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        # Jerk is a distributional spike at t=0, duration/2, duration and
        # zero elsewhere; we report the (correct, everywhere-else) zero value.
        result: NDArray[np.float64] = np.zeros_like(arr)
        return _finish(result, scalar)


class SCurveProfile(AccelerationProfile):
    """Jerk-limited trapezoidal ("S-curve") acceleration profile, standard in
    spacecraft maneuver planning.

    Acceleration ramps from 0 to ``a_max`` at constant jerk ``j_max``, holds
    at ``a_max`` ("cruise"), then ramps back down to 0 at ``-j_max``:

    .. code-block:: text

        tau = a_max / j_max                                  (ramp duration)
        a(t) = j_max * t,                                     0 <= t < tau
        a(t) = a_max,                                  tau <= t < duration - tau
        a(t) = a_max - j_max * (t - (duration - tau)),  duration - tau <= t <= duration

    Requires ``duration >= 2 * a_max / j_max``: otherwise ``a_max`` cannot be
    reached within the specified duration and jerk limit, and the profile as
    given (with zero further free parameters, per the Definition of Ready)
    would be under-determined. At exactly ``duration == 2*a_max/j_max`` the
    cruise phase has zero length and the profile degenerates continuously
    into a pure triangular ramp-up/ramp-down.
    """

    def __init__(self, a_max: float, j_max: float, duration: float) -> None:
        self._a_max = _require_positive_finite(a_max, "a_max")
        self._j_max = _require_positive_finite(j_max, "j_max")
        self._duration = _require_positive_finite(duration, "duration")

        tau = self._a_max / self._j_max
        if self._duration < 2.0 * tau:
            raise ValueError(
                f"duration ({self._duration!r}) must be at least 2*a_max/j_max "
                f"({2.0 * tau!r}) for the acceleration to reach a_max and return to zero"
            )
        self._tau = tau
        self._t2 = self._duration - tau

        # Kinematics at the two ramp/cruise boundaries, precomputed once so
        # the piecewise formulas below are simple polynomial evaluations.
        self._v_tau = 0.5 * self._j_max * tau**2
        self._x_tau = (1.0 / 6.0) * self._j_max * tau**3
        self._v_t2 = self._v_tau + self._a_max * (self._t2 - tau)
        self._x_t2 = (
            self._x_tau + self._v_tau * (self._t2 - tau) + 0.5 * self._a_max * (self._t2 - tau) ** 2
        )

    @property
    def duration(self) -> float:
        return self._duration

    def acceleration(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        tau, t2 = self._tau, self._t2
        ramp_up = self._j_max * arr
        cruise = np.full_like(arr, self._a_max)
        ramp_down = self._a_max - self._j_max * (arr - t2)
        result: NDArray[np.float64] = np.where(
            arr < tau, ramp_up, np.where(arr < t2, cruise, ramp_down)
        )
        return _finish(result, scalar)

    def jerk(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        tau, t2 = self._tau, self._t2
        result: NDArray[np.float64] = np.where(
            arr < tau, self._j_max, np.where(arr < t2, 0.0, -self._j_max)
        )
        return _finish(result, scalar)

    def velocity(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        tau, t2 = self._tau, self._t2
        ramp_up_v = 0.5 * self._j_max * arr**2
        cruise_v = self._v_tau + self._a_max * (arr - tau)
        ramp_down_v = self._v_t2 + self._a_max * (arr - t2) - 0.5 * self._j_max * (arr - t2) ** 2
        result: NDArray[np.float64] = np.where(
            arr < tau, ramp_up_v, np.where(arr < t2, cruise_v, ramp_down_v)
        )
        return _finish(result, scalar)

    def position(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        tau, t2 = self._tau, self._t2
        ramp_up_x = (1.0 / 6.0) * self._j_max * arr**3
        cruise_x = self._x_tau + self._v_tau * (arr - tau) + 0.5 * self._a_max * (arr - tau) ** 2
        ramp_down_x = (
            self._x_t2
            + self._v_t2 * (arr - t2)
            + 0.5 * self._a_max * (arr - t2) ** 2
            - (1.0 / 6.0) * self._j_max * (arr - t2) ** 3
        )
        result: NDArray[np.float64] = np.where(
            arr < tau, ramp_up_x, np.where(arr < t2, cruise_x, ramp_down_x)
        )
        return _finish(result, scalar)


class QuinticProfile(AccelerationProfile):
    """Quintic (minimum-jerk) velocity profile.

    The standard quintic "smootherstep" polynomial, scaled so velocity rises
    from 0 to ``delta_v`` over ``[0, duration]`` with zero acceleration
    *and* zero jerk at both endpoints:

    .. code-block:: text

        s = t / duration
        v(t) = delta_v * (10 s^3 - 15 s^4 + 6 s^5)
        a(t) = (delta_v / duration)   * (30 s^2 - 60 s^3 + 30 s^4)
        j(t) = (delta_v / duration^2) * (60 s - 180 s^2 + 120 s^3)
        x(t) = delta_v * duration * (2.5 s^4 - 3 s^5 + s^6)

    This is the unique quintic polynomial in ``s`` satisfying ``v(0)=0``,
    ``v(1)=delta_v``, and ``v', v''`` both zero at ``s=0`` and ``s=1``
    (6 coefficients, 6 boundary conditions).
    """

    def __init__(self, delta_v: float, duration: float) -> None:
        self._delta_v = _require_finite(delta_v, "delta_v")
        self._duration = _require_positive_finite(duration, "duration")

    @property
    def duration(self) -> float:
        return self._duration

    def _s(self, arr: NDArray[np.float64]) -> NDArray[np.float64]:
        result: NDArray[np.float64] = arr / self._duration
        return result

    def acceleration(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        s = self._s(arr)
        result: NDArray[np.float64] = (self._delta_v / self._duration) * (
            30.0 * s**2 - 60.0 * s**3 + 30.0 * s**4
        )
        return _finish(result, scalar)

    def velocity(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        s = self._s(arr)
        result: NDArray[np.float64] = self._delta_v * (10.0 * s**3 - 15.0 * s**4 + 6.0 * s**5)
        return _finish(result, scalar)

    def position(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        s = self._s(arr)
        result: NDArray[np.float64] = (
            self._delta_v * self._duration * (2.5 * s**4 - 3.0 * s**5 + s**6)
        )
        return _finish(result, scalar)

    def jerk(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        s = self._s(arr)
        result: NDArray[np.float64] = (self._delta_v / self._duration**2) * (
            60.0 * s - 180.0 * s**2 + 120.0 * s**3
        )
        return _finish(result, scalar)


class RaisedCosineProfile(AccelerationProfile):
    """Raised-cosine acceleration profile.

    Acceleration follows one full raised-cosine (Hann-shaped) hump over
    ``[0, duration]``:

    .. code-block:: text

        a(t) = (delta_v / duration) * (1 - cos(2 pi t / duration))
        v(t) = (delta_v / duration) * (t - (duration / 2 pi) sin(2 pi t / duration))
        x(t) = (delta_v / duration) * (t^2/2
                 + (duration/2pi)^2 * (cos(2 pi t / duration) - 1))
        j(t) = (2 pi delta_v / duration^2) * sin(2 pi t / duration)

    ``a(t)`` is exactly proportional to a periodic Hann/raised-cosine window
    ``(1 - cos(2 pi t/T))``, which is why its acceleration spectrum matches a
    Hann window's spectral rolloff (verified in
    ``tests/unit/test_profiles.py``, T-3.5's acceptance criterion). Both
    acceleration and jerk vanish at ``t=0`` and ``t=duration``.
    """

    def __init__(self, delta_v: float, duration: float) -> None:
        self._delta_v = _require_finite(delta_v, "delta_v")
        self._duration = _require_positive_finite(duration, "duration")

    @property
    def duration(self) -> float:
        return self._duration

    def acceleration(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        omega = 2.0 * np.pi / self._duration
        result: NDArray[np.float64] = (self._delta_v / self._duration) * (1.0 - np.cos(omega * arr))
        return _finish(result, scalar)

    def velocity(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        omega = 2.0 * np.pi / self._duration
        result: NDArray[np.float64] = (self._delta_v / self._duration) * (
            arr - np.sin(omega * arr) / omega
        )
        return _finish(result, scalar)

    def position(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        omega = 2.0 * np.pi / self._duration
        result: NDArray[np.float64] = (self._delta_v / self._duration) * (
            0.5 * arr**2 + (np.cos(omega * arr) - 1.0) / omega**2
        )
        return _finish(result, scalar)

    def jerk(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        omega = 2.0 * np.pi / self._duration
        result: NDArray[np.float64] = (self._delta_v / self._duration) * omega * np.sin(omega * arr)
        return _finish(result, scalar)


#: Zero-padding factor between the number of real time-domain samples taken
#: across a profile's own duration and the total (zero-padded) FFT length.
#:
#: This is necessary, not cosmetic: a plain N-point DFT taken over exactly
#: one profile period places every frequency bin exactly on a harmonic of
#: 1/duration, which is precisely where a finite pulse confined to that same
#: window has all of its *own* energy concentrated (an integer number of
#: cycles fits exactly in the observation window) — every bin in between
#: comes out at the floating-point noise floor, and the sidelobe structure
#: this function exists to reveal is invisible. Zero-padding the real samples
#: out to a longer FFT interpolates the *continuous* spectrum between those
#: harmonics, exactly the standard oversampling technique used to inspect a
#: finite pulse's or window's sidelobe structure in radar/DSP pulse analysis.
#: Verified numerically (see tests/unit/test_profiles.py) to reproduce the
#: expected -13 dB / -31 dB sidelobe levels stably across n_fft in [1024,
#: 65536] at this factor.
_SPECTRUM_OVERSAMPLE = 16


def spectrum(
    profile: AccelerationProfile, n_fft: int
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Discrete Fourier spectrum of a profile's acceleration signal.

    Samples ``profile.acceleration(t)`` at ``n_fft // 16`` evenly spaced
    points over ``[0, duration)`` (the acceleration profile is the "transmit
    pulse shape", ``docs/PHYSICS.md`` §4), zero-pads to length ``n_fft`` (see
    ``_SPECTRUM_OVERSAMPLE``), and returns the full two-sided DFT frequency
    axis and magnitude spectrum. Uses NumPy's unnormalized forward transform
    convention (``numpy.fft.fft``), under which the discrete Parseval
    relation ``sum(x^2) == sum(|X|^2) / n_fft`` holds exactly (zero-padding
    adds no energy, so this holds for the padded signal exactly as for the
    real samples alone).

    Parameters
    ----------
    profile
        Any concrete :class:`AccelerationProfile`.
    n_fft
        Total (zero-padded) FFT length. Must be a positive integer, at least
        ``_SPECTRUM_OVERSAMPLE``.

    Returns
    -------
    tuple of ndarray
        ``(freqs, magnitude)``, each shape ``(n_fft,)``, float64. ``freqs``
        is in Hz (``numpy.fft.fftfreq(n_fft, d=dt)`` with
        ``dt = duration / (n_fft // _SPECTRUM_OVERSAMPLE)``); ``magnitude``
        is ``abs(fft(zero-padded acceleration samples))``.
    """
    if not isinstance(n_fft, (int, np.integer)) or isinstance(n_fft, bool) or n_fft <= 0:
        raise ValueError(f"n_fft must be a positive integer, got {n_fft!r}")
    if n_fft < _SPECTRUM_OVERSAMPLE:
        raise ValueError(f"n_fft must be at least {_SPECTRUM_OVERSAMPLE}, got {n_fft!r}")

    n_samples = n_fft // _SPECTRUM_OVERSAMPLE
    duration = profile.duration
    dt = duration / n_samples
    t = np.arange(n_samples, dtype=np.float64) * dt
    samples = np.asarray(profile.acceleration(t), dtype=np.float64)

    padded = np.zeros(n_fft, dtype=np.float64)
    padded[:n_samples] = samples

    spectrum_complex = np.fft.fft(padded)
    freqs: NDArray[np.float64] = np.fft.fftfreq(n_fft, d=dt).astype(np.float64)
    magnitude: NDArray[np.float64] = np.abs(spectrum_complex).astype(np.float64)
    return freqs, magnitude


__all__ = [
    "AccelerationProfile",
    "BangBangProfile",
    "QuinticProfile",
    "RaisedCosineProfile",
    "SCurveProfile",
    "spectrum",
]
