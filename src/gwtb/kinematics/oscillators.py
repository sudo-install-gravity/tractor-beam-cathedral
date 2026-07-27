"""Prime-frequency multiplexed drive: a synthetic multi-tone acceleration
profile used to probe the array's frequency-domain behavior (Sprint 9).

The choice to space drive tones at prime-numbered frequencies is a project
design decision, not a physics result (BACKLOG.md T-9.2, "the band scale is a
free parameter"): using pairwise-coprime tones pushes the multi-tone
recurrence period out to the product of the tones rather than their (trivial)
pairwise GCD, which is the whole point of the construction. This module is
kinematic/DSP, like ``profiles.py``, and is exempt from the ``source``/
``propagate``/``bodies``/``array`` citation requirement.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.validation import as_float64
from gwtb.kinematics.profiles import AccelerationProfile, _finish, _prepare_time


def first_n_primes(n: int) -> list[int]:
    """The first ``n`` prime numbers, via a sieve.

    Parameters
    ----------
    n
        How many primes to generate. Must be a positive integer.

    Returns
    -------
    list[int]
        The first ``n`` primes in increasing order.
    """
    if not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError(f"n must be a positive integer, got {n!r}")

    # Upper bound on the n-th prime (Rosser's theorem, valid for n >= 6); pad
    # generously and fall back to widening if it still comes up short.
    if n < 6:
        limit = 15
    else:
        limit = int(n * (math.log(n) + math.log(math.log(n)))) + 10

    while True:
        sieve = np.ones(limit + 1, dtype=bool)
        sieve[:2] = False
        for p in range(2, int(math.isqrt(limit)) + 1):
            if sieve[p]:
                sieve[p * p :: p] = False
        primes = np.flatnonzero(sieve)
        if primes.size >= n:
            return [int(p) for p in primes[:n]]
        limit *= 2


def prime_frequencies(n: int, unit_hz: float = 1.0) -> NDArray[np.float64]:
    """The first ``n`` primes scaled to a frequency band.

    ``unit_hz`` is a free parameter (BACKLOG.md T-9.2, decision 2): it sets
    where in the spectrum the prime-multiplexed comb sits, independent of the
    combinatorial structure (prime spacing) that gives the comb its
    recurrence-period behavior.

    Parameters
    ----------
    n
        Number of tones.
    unit_hz
        Frequency scale, Hz. Must be strictly positive.

    Returns
    -------
    ndarray
        Shape ``(n,)``, Hz: ``primes * unit_hz``.
    """
    if not math.isfinite(unit_hz) or unit_hz <= 0.0:
        raise ValueError(f"unit_hz must be positive and finite, got {unit_hz!r}")
    primes = np.array(first_n_primes(n), dtype=np.float64)
    return primes * unit_hz


def _float_gcd(a: float, b: float, tol: float = 1e-9) -> float:
    """Euclidean-algorithm GCD for floats, terminating within ``tol``."""
    a, b = abs(a), abs(b)
    while b > tol:
        a, b = b, math.fmod(a, b)
    return a


def recurrence_period(frequencies: ArrayLike) -> float:
    """Time for a set of commensurate tones to return simultaneously to
    zero phase.

    Each frequency is expressed as an integer multiple of a common unit
    ``g`` (recovered via the Euclidean algorithm on floats): ``f_i = k_i *
    g``. All tones return to zero phase together after ``LCM(k_i) / g``
    seconds; for pairwise-coprime integer ratios ``k_i`` (as produced by
    :func:`prime_frequencies`), ``LCM(k_i) = product(k_i)``, so the
    recurrence period grows as the *product* of the tone count's primes
    rather than their (trivial, always-1) pairwise GCD — the reason this
    construction uses primes at all.

    Parameters
    ----------
    frequencies
        Shape ``(N,)``, Hz. Must be strictly positive and pairwise
        commensurate (integer multiples of a common unit, to within the
        Euclidean-algorithm tolerance).

    Returns
    -------
    float
        Recurrence period, s.
    """
    freqs = as_float64(frequencies, "frequencies")
    if freqs.ndim != 1 or freqs.size == 0:
        raise ValueError(f"frequencies must have shape (N,), got {freqs.shape}")
    if np.any(freqs <= 0.0):
        raise ValueError("frequencies must be strictly positive")

    g = float(freqs[0])
    for f in freqs[1:]:
        g = _float_gcd(g, float(f))
    if g <= 0.0:
        raise ValueError("frequencies share no common unit (GCD reduced to zero)")

    ratios = np.rint(freqs / g).astype(np.int64)
    product = 1
    for k in ratios:
        product *= int(k)
    return float(product) / g


class PrimeOscillatorDrive(AccelerationProfile):
    """Multi-frequency acceleration drive: a sum of sinusoidal tones.

    .. code-block:: text

        a(t) = sum_i amplitudes[i] * sin(2*pi*frequencies[i]*t + phases[i])

    Velocity and position are the exact analytic time integrals (each tone
    integrates to a cosine/sine term), so ``v(0) = x(0) = 0`` by
    construction — consistent with every other :class:`AccelerationProfile`
    in this module.

    Parameters
    ----------
    frequencies
        Shape ``(N,)``, Hz. Strictly positive.
    amplitudes
        Shape ``(N,)``, m/s^2. Per-tone acceleration amplitude.
    phases
        Shape ``(N,)``, rad. Per-tone phase offset.
    duration
        Total drive duration, s.
    """

    def __init__(
        self,
        frequencies: ArrayLike,
        amplitudes: ArrayLike,
        phases: ArrayLike,
        duration: float,
    ) -> None:
        f = as_float64(frequencies, "frequencies")
        a = as_float64(amplitudes, "amplitudes")
        p = as_float64(phases, "phases")
        if f.ndim != 1 or f.size == 0:
            raise ValueError(f"frequencies must have shape (N,), got {f.shape}")
        if a.shape != f.shape or p.shape != f.shape:
            raise ValueError("frequencies, amplitudes, and phases must have the same shape")
        if np.any(f <= 0.0):
            raise ValueError("frequencies must be strictly positive")
        if not math.isfinite(duration) or duration <= 0.0:
            raise ValueError(f"duration must be positive and finite, got {duration!r}")

        self._omega = 2.0 * np.pi * f
        self._amplitudes = a
        self._phases = p
        self._duration = float(duration)
        #: Worst-case bound on |acceleration|, saturated when every tone
        #: peaks in phase.
        self.a_max = float(np.sum(np.abs(a)))

    @property
    def duration(self) -> float:
        return self._duration

    def acceleration(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        phase = np.outer(arr, self._omega) + self._phases
        result = np.sum(self._amplitudes * np.sin(phase), axis=-1)
        return _finish(result, scalar)

    def velocity(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        phase = np.outer(arr, self._omega) + self._phases
        term = -(self._amplitudes / self._omega) * (np.cos(phase) - np.cos(self._phases))
        result = np.sum(term, axis=-1)
        return _finish(result, scalar)

    def position(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        phase = np.outer(arr, self._omega) + self._phases
        sin_term = -(self._amplitudes / self._omega**2) * (np.sin(phase) - np.sin(self._phases))
        cos_term = (self._amplitudes / self._omega) * np.cos(self._phases) * arr[:, None]
        result = np.sum(sin_term + cos_term, axis=-1)
        return _finish(result, scalar)

    def jerk(self, t: ArrayLike) -> float | NDArray[np.float64]:
        arr, scalar = _prepare_time(t)
        self._validate_domain(arr)
        phase = np.outer(arr, self._omega) + self._phases
        result = np.sum(self._amplitudes * self._omega * np.cos(phase), axis=-1)
        return _finish(result, scalar)


__all__ = ["PrimeOscillatorDrive", "first_n_primes", "prime_frequencies", "recurrence_period"]
