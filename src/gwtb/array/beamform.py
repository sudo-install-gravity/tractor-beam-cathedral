"""Scalar phased-array beamforming: array factor, steering, beamwidth/
sidelobes, and amplitude tapering.

**This module is deliberately the scalar (spin-1-style) baseline**
(BACKLOG.md T-6.1 note; see also ``docs/HANDOVER.md`` §5). It treats each
element as an isotropic point radiator combining complex scalar weights —
exactly the formalism used for ordinary EM phased arrays. It is the
known-good reference against which the spin-2 tensor superposition
(:mod:`gwtb.array.beamform.superpose_tt`, T-6.5, not yet implemented) must
reduce for co-oriented elements. Do not read gravitational-radiation physics
into this module: it is pure classical array theory.

Source: S. J. Orfanidis, *Electromagnetic Waves and Antennas* (open-access,
www.ece.rutgers.edu/~orfanidi/ewa), ch. 19 "Antenna Arrays".
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.signal.windows import chebwin, hamming, hann, taylor


def array_factor(
    geometry: ArrayLike,
    weights: ArrayLike,
    wavelength: float,
    direction: ArrayLike,
) -> complex:
    """Scalar array factor evaluated toward one observation direction.

    .. code-block:: text

        AF = sum_n w_n * exp(i * k . r_n),   k = (2 pi / lambda) * direction

    Source: Orfanidis, EM Waves and Antennas, ch. 19, eq. 19.4.1

    Parameters
    ----------
    geometry
        Shape ``(N, 3)``, m. Element positions.
    weights
        Shape ``(N,)``, complex. Per-element excitation (amplitude and phase).
    wavelength
        Radiation wavelength, m. Must be positive.
    direction
        Shape ``(3,)`` unit vector, the observation direction.

    Returns
    -------
    complex
        The (unnormalized) array factor.
    """
    pos = np.asarray(geometry, dtype=np.float64)
    w = np.asarray(weights, dtype=np.complex128)
    d = np.asarray(direction, dtype=np.float64)
    if pos.ndim != 2 or pos.shape[1] != 3:
        raise ValueError(f"geometry must have shape (N, 3), got {pos.shape}")
    if w.shape != (pos.shape[0],):
        raise ValueError(f"weights must have shape ({pos.shape[0]},), got {w.shape}")
    if d.shape != (3,):
        raise ValueError(f"direction must have shape (3,), got {d.shape}")
    if not np.isfinite(wavelength) or wavelength <= 0.0:
        raise ValueError(f"wavelength must be positive and finite, got {wavelength!r}")
    norm = np.linalg.norm(d)
    if abs(norm - 1.0) > 1e-9:
        raise ValueError(f"direction must be a unit vector, got |direction| = {norm!r}")

    k_vec = (2.0 * np.pi / wavelength) * d
    phase = pos @ k_vec
    return complex(np.sum(w * np.exp(1j * phase)))


def _wavevector_component(wavelength: float, theta: NDArray[np.float64]) -> NDArray[np.float64]:
    """``k * sin(theta)`` for a sweep of scan angles from broadside."""
    return (2.0 * np.pi / wavelength) * np.sin(theta)


def steering_phases(
    geometry: ArrayLike, wavelength: float, target_direction: ArrayLike
) -> NDArray[np.float64]:
    """Per-element phase that steers a uniform-amplitude array's peak to
    ``target_direction``.

    .. code-block:: text

        phi_n = -k . r_n,   k = (2 pi / lambda) * target_direction

    Applying ``weights_n = amplitude_n * exp(i phi_n)`` cancels the
    propagation phase toward ``target_direction``, so all elements combine
    constructively there.

    Source: Orfanidis, EM Waves and Antennas, ch. 19, eq. 19.4.1 (phase
    conjugation for beam steering)

    Parameters
    ----------
    geometry
        Shape ``(N, 3)``, m.
    wavelength
        Radiation wavelength, m.
    target_direction
        Shape ``(3,)`` unit vector to steer the main lobe toward.

    Returns
    -------
    ndarray
        Shape ``(N,)``, rad.
    """
    pos = np.asarray(geometry, dtype=np.float64)
    d = np.asarray(target_direction, dtype=np.float64)
    if pos.ndim != 2 or pos.shape[1] != 3:
        raise ValueError(f"geometry must have shape (N, 3), got {pos.shape}")
    if d.shape != (3,):
        raise ValueError(f"target_direction must have shape (3,), got {d.shape}")
    norm = np.linalg.norm(d)
    if abs(norm - 1.0) > 1e-9:
        raise ValueError(f"target_direction must be a unit vector, got |direction| = {norm!r}")
    if not np.isfinite(wavelength) or wavelength <= 0.0:
        raise ValueError(f"wavelength must be positive and finite, got {wavelength!r}")

    k_vec = (2.0 * np.pi / wavelength) * d
    result: NDArray[np.float64] = -(pos @ k_vec)
    return result


def _pattern_along_broadside_sweep(
    geometry: NDArray[np.float64],
    weights: NDArray[np.complex128],
    wavelength: float,
    axis: NDArray[np.float64],
    theta: NDArray[np.float64],
) -> NDArray[np.float64]:
    """|AF(theta)| for a 1-D sweep of angles from broadside, scanning in the
    plane containing ``axis`` (the array's long axis) and an orthogonal
    direction. Used by beamwidth/sidelobe and taper evaluation."""
    orth = np.array([0.0, 0.0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    orth = orth - axis * np.dot(orth, axis)
    orth = orth / np.linalg.norm(orth)
    directions = np.outer(np.sin(theta), axis) + np.outer(np.cos(theta), orth)
    k = (2.0 * np.pi / wavelength) * directions
    phase = geometry @ k.T
    af = np.sum(weights[:, None] * np.exp(1j * phase), axis=0)
    result: NDArray[np.float64] = np.abs(af)
    return result


def beamwidth_3db(
    geometry: ArrayLike, weights: ArrayLike, wavelength: float, axis: ArrayLike
) -> float:
    """Full 3 dB beamwidth of the main lobe, rad, scanning broadside along
    ``axis``.

    For a uniform array this reproduces ``theta_3dB ~= 0.886 * lambda / (N *
    d)``, ``d`` the element spacing (Orfanidis eq. 19.7.6, broadside form).

    Source: Orfanidis, EM Waves and Antennas, ch. 19, eq. 19.7.6

    Parameters
    ----------
    geometry
        Shape ``(N, 3)``, m.
    weights
        Shape ``(N,)``, complex.
    wavelength
        Radiation wavelength, m.
    axis
        Shape ``(3,)`` unit vector along the array's scan axis.

    Returns
    -------
    float
        Full width (rad) where ``|AF|`` falls to ``1/sqrt(2)`` of its peak,
        found by a fine angular sweep.
    """
    pos = np.asarray(geometry, dtype=np.float64)
    w = np.asarray(weights, dtype=np.complex128)
    ax = np.asarray(axis, dtype=np.float64)
    ax = ax / np.linalg.norm(ax)

    theta = np.linspace(-np.pi / 2.0, np.pi / 2.0, 200001)
    pattern = _pattern_along_broadside_sweep(pos, w, wavelength, ax, theta)
    peak = np.max(pattern)
    half_power = peak / np.sqrt(2.0)
    peak_idx = int(np.argmax(pattern))

    above = pattern >= half_power
    # Walk outward from the peak to the first index that drops below
    # half-power on each side, then interpolate linearly for sub-sample
    # resolution.
    left = peak_idx
    while left > 0 and above[left - 1]:
        left -= 1
    right = peak_idx
    while right < len(theta) - 1 and above[right + 1]:
        right += 1

    def _interp_crossing(i_in: int, i_out: int) -> float:
        p_in, p_out = pattern[i_in], pattern[i_out]
        if p_in == p_out:
            return float(theta[i_in])
        frac = (half_power - p_in) / (p_out - p_in)
        return float(theta[i_in] + frac * (theta[i_out] - theta[i_in]))

    theta_left = _interp_crossing(left, left - 1) if left > 0 else float(theta[0])
    theta_right = _interp_crossing(right, right + 1) if right < len(theta) - 1 else float(theta[-1])
    return theta_right - theta_left


def peak_sidelobe_level(
    geometry: ArrayLike, weights: ArrayLike, wavelength: float, axis: ArrayLike
) -> float:
    """Peak sidelobe level relative to the main lobe, dB (negative).

    For a uniform array this reproduces the classical ``-13.2`` dB first
    sidelobe (Orfanidis, derived between eq. 19.7.6 and eq. 19.8.1).

    Source: Orfanidis, EM Waves and Antennas, ch. 19, eq. 19.7.6

    Parameters
    ----------
    geometry
        Shape ``(N, 3)``, m.
    weights
        Shape ``(N,)``, complex.
    wavelength
        Radiation wavelength, m.
    axis
        Shape ``(3,)`` unit vector along the array's scan axis.

    Returns
    -------
    float
        ``20 * log10(sidelobe_peak / main_peak)``, dB.
    """
    pos = np.asarray(geometry, dtype=np.float64)
    w = np.asarray(weights, dtype=np.complex128)
    ax = np.asarray(axis, dtype=np.float64)
    ax = ax / np.linalg.norm(ax)

    theta = np.linspace(-np.pi / 2.0, np.pi / 2.0, 400001)
    pattern = _pattern_along_broadside_sweep(pos, w, wavelength, ax, theta)
    peak = np.max(pattern)
    peak_idx = int(np.argmax(pattern))

    # Find the main-lobe null on each side (first local minimum), then take
    # the maximum of the pattern outside that region as the sidelobe peak.
    left = peak_idx
    while left > 1 and pattern[left - 1] <= pattern[left]:
        left -= 1
    right = peak_idx
    while right < len(theta) - 2 and pattern[right + 1] <= pattern[right]:
        right += 1

    outside = np.concatenate([pattern[: max(left, 1)], pattern[min(right + 1, len(theta)) :]])
    if outside.size == 0:
        return float("-inf")
    sidelobe_peak = np.max(outside)
    return float(20.0 * np.log10(sidelobe_peak / peak))


def taper(
    n: int, kind: str, sll: float | None = None, nbar: int | None = None
) -> NDArray[np.float64]:
    """Amplitude taper (window function) for an ``n``-element linear array.

    ``kind`` selects the window:

    - ``"uniform"``: all-ones.
    - ``"hann"``: Hann window.
    - ``"hamming"``: Hamming window.
    - ``"chebyshev"``: Dolph-Chebyshev window for a requested sidelobe level
      ``sll`` (positive dB below the main lobe).
    - ``"taylor"``: Taylor window for sidelobe level ``sll`` and near-in
      sidelobe count ``nbar``.

    Source: Dolph (1946) and Taylor (1955), eq. n/a (in-paper eq. numbers unconfirmed; see below)

    Full references: C. L. Dolph, Proc. IRE 34(6), 335 (1946); T. T. Taylor,
    IRE Trans. Antennas Propag. 3(1), 16 (1955). Implemented via
    ``scipy.signal.windows``, which follows each paper's construction — see
    the SciPy docs for ``chebwin``/``taylor``.

    Parameters
    ----------
    n
        Number of elements. Must be a positive integer.
    kind
        One of ``"uniform"``, ``"hann"``, ``"hamming"``, ``"chebyshev"``,
        ``"taylor"``.
    sll
        Sidelobe level, dB (positive number below the main lobe). Required
        for ``"chebyshev"`` and ``"taylor"``.
    nbar
        Number of near-in sidelobes at the design level. Required for
        ``"taylor"``.

    Returns
    -------
    ndarray
        Shape ``(n,)``, real, non-negative amplitude weights.
    """
    if not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError(f"n must be a positive integer, got {n!r}")

    if kind == "uniform":
        return np.ones(n, dtype=np.float64)
    if kind == "hann":
        result: NDArray[np.float64] = hann(n, sym=True)
        return result
    if kind == "hamming":
        result = hamming(n, sym=True)
        return result
    if kind == "chebyshev":
        if sll is None:
            raise ValueError("chebyshev taper requires sll (dB)")
        result = chebwin(n, at=sll, sym=True)
        return result
    if kind == "taylor":
        if sll is None or nbar is None:
            raise ValueError("taylor taper requires both sll (dB) and nbar")
        result = taylor(n, nbar=nbar, sll=sll, norm=False, sym=True)
        return result
    raise ValueError(f"unknown taper kind {kind!r}")


__all__ = [
    "array_factor",
    "beamwidth_3db",
    "peak_sidelobe_level",
    "steering_phases",
    "taper",
]
