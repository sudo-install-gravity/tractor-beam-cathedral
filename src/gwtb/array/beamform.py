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

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.signal.windows import chebwin, hamming, hann, taylor

from gwtb.core.validation import as_float64, as_tensor_3x3, as_unit_vector
from gwtb.propagate.tt_projection import apply_tt


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


# ---------------------------------------------------------------------------
# Spin-2 extension (T-6.5, T-6.6)
#
# Everything above this line is the scalar spin-1 baseline. Everything below is
# the gravitational-wave case, and the two must not be confused. The formulation
# is specified by docs/adr/0003-spin2-superposition.md, derived in SPIKE-4.4.
# ---------------------------------------------------------------------------


def _as_point(a: ArrayLike, name: str) -> NDArray[np.float64]:
    """Validate a position vector: shape ``(3,)``, float64, finite."""
    v = as_float64(a, name)
    if v.shape != (3,):
        raise ValueError(f"{name} must have shape (3,), got {v.shape}")
    return v


@dataclass(frozen=True)
class QuadrupoleElement:
    """One radiating element: where it sits, and how it is oriented.

    Orientation is what makes the spin-2 case differ from the scalar one. In an
    EM array an element contributes a complex scalar; here it contributes a
    *tensor*, and two elements whose tensors differ interfere only partially —
    or, at 90 degrees, cancel outright.

    Source: docs/adr/0003-spin2-superposition.md, eq. 1 (the per-element term
    of the superposition sum, which is what fixes this element model)

    Parameters
    ----------
    position
        Shape ``(3,)``, m.
    quadrupole
        Shape ``(3, 3)``, the element's second time derivative of the trace-free
        quadrupole moment, kg m^2 s^-2. Need not be TT-projected; that happens
        during superposition, along the common observation direction.
    """

    position: NDArray[np.float64]
    quadrupole: NDArray[np.float64]


def superpose_tt(
    elements: Sequence[QuadrupoleElement],
    weights: ArrayLike,
    wavelength: float,
    field_point: ArrayLike,
) -> NDArray[np.complex128]:
    """Superpose element radiation as TT tensors, not scalar amplitudes.

    .. code-block:: text

        h_ij(n) = sum_n  Lambda_ij,kl(n) Q^(n)_kl  w_n  exp(i k . r_n)

    The TT projection uses **one** observation direction, taken from the array
    centroid to ``field_point``. That is what makes the sum meaningful: tensors
    projected along different directions live in different two-dimensional
    polarization spaces and cannot be added. The far-field condition that
    justifies it is checked below.

    Contrast :func:`array_factor`, which sums complex scalars. For co-oriented
    elements this function factorizes into ``(TT tensor) x (scalar array
    factor)`` and the two agree exactly; for differently-oriented elements it
    does not, and the difference is the physics.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 2 (per-element
    waveform), superposed per docs/adr/0003-spin2-superposition.md

    Parameters
    ----------
    elements
        The radiating elements. Must be non-empty.
    weights
        Shape ``(N,)`` complex excitation, as for :func:`array_factor`.
    wavelength
        Radiation wavelength, m. Positive.
    field_point
        Shape ``(3,)``, m. Observation point, in the far field of the array.

    Returns
    -------
    ndarray
        Shape ``(3, 3)`` complex phasor of the TT strain, in the units of
        ``quadrupole``. Symmetric, traceless, and transverse to the observation
        direction.

    Raises
    ------
    ValueError
        If the field point is not in the array's far field, where the
        common-direction assumption underpinning this sum fails. Per ADR-0003
        that is a reversal condition for the whole formulation, so it raises
        rather than degrading quietly.
    """
    if len(elements) == 0:
        raise ValueError("elements must be non-empty")
    w = np.asarray(weights, dtype=np.complex128)
    if w.shape != (len(elements),):
        raise ValueError(f"weights must have shape ({len(elements)},), got {w.shape}")
    if not np.isfinite(wavelength) or wavelength <= 0.0:
        raise ValueError(f"wavelength must be positive and finite, got {wavelength!r}")

    positions = np.array([_as_point(e.position, "position") for e in elements])
    target = _as_point(field_point, "field_point")

    centroid = positions.mean(axis=0)
    offset = target - centroid
    distance = float(np.linalg.norm(offset))
    if distance == 0.0:
        raise ValueError("field_point coincides with the array centroid")
    n_hat = offset / distance

    # Fraunhofer condition: beyond 2 D^2 / lambda the wavefront across the
    # aperture is planar to better than lambda/16, so a single n_hat is valid.
    aperture = 2.0 * float(np.linalg.norm(positions - centroid, axis=1).max())
    far_field = 2.0 * aperture**2 / wavelength if aperture > 0.0 else 0.0
    if distance < far_field:
        raise ValueError(
            f"field_point is inside the array near field: distance {distance:.4g} m "
            f"< Fraunhofer limit {far_field:.4g} m (aperture {aperture:.4g} m, "
            f"wavelength {wavelength:.4g} m). Superposing TT tensors requires a "
            f"common observation direction — see ADR-0003's reversal condition."
        )

    k_vec = (2.0 * np.pi / wavelength) * n_hat
    total = np.zeros((3, 3), dtype=np.complex128)
    for element, weight, position in zip(elements, w, positions, strict=True):
        projected = apply_tt(as_tensor_3x3(element.quadrupole, "quadrupole"), n_hat)
        total += projected * weight * np.exp(1j * float(position @ k_vec))
    return total


def mismatch_loss(orientation_a: ArrayLike, orientation_b: ArrayLike, n_hat: ArrayLike) -> float:
    """Polarization coupling between two linear elements, seen along ``n_hat``.

    Returns the normalized double contraction of the two TT-projected
    quadrupoles, which for linear oscillators separated by ``dpsi`` about the
    line of sight evaluates to

    .. code-block:: text

        cos(2 * dpsi)

    ⚠️ **Not** ``cos(dpsi)``. The consequences are qualitative, not merely
    numerical:

    * ``dpsi = 45 deg`` gives **0** — the elements are polarization-orthogonal
      and their powers merely add. An EM array needs 90 degrees for this.
    * ``dpsi = 90 deg`` gives **-1** — the elements **cancel**. Spin-1 intuition
      predicts orthogonality and 2x power here, so an array laid out on antenna
      reasoning radiates nothing along its intended axis.

    Source: derived in docs/adr/0003-spin2-superposition.md (claim B-1),
    from Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 2

    Parameters
    ----------
    orientation_a, orientation_b
        Shape ``(3,)`` unit vectors giving each element's oscillation axis.
    n_hat
        Shape ``(3,)`` unit vector, the common observation direction.

    Returns
    -------
    float
        Coupling in ``[-1, 1]``: 1 fully coherent, 0 orthogonal, -1 cancelling.
        Period is ``pi`` in the orientation separation, not ``2 pi``.
    """
    n = as_unit_vector(n_hat)
    tensors = []
    for name, axis in (("orientation_a", orientation_a), ("orientation_b", orientation_b)):
        u = as_unit_vector(axis, name)
        tensors.append(apply_tt(np.outer(u, u), n))

    norms = [float(np.sqrt(np.einsum("ij,ij->", t, t))) for t in tensors]
    if min(norms) < 1e-15:
        raise ValueError(
            "an orientation is parallel to n_hat: a linear element radiates "
            "nothing along its own axis, so the coupling is undefined"
        )
    return float(np.einsum("ij,ij->", *tensors) / (norms[0] * norms[1]))
