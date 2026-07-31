"""Spatiotemporal focusing: driving array elements so their radiation coincides
at one point in space *and* time.

Focusing is a statement about **propagation delay**, not about polarization. An
element's contribution arrives at the focal point delayed by ``R/c``, and the
phase law below simply inverts that delay. Nothing here depends on the radiation
being spin-2, which is why the geometry may legitimately be borrowed from the
antenna-array literature — unlike the *superposition* of what arrives, which is
tensorial and must go through :func:`gwtb.array.beamform.superpose_tt`
(``CLAUDE.md`` rule 4, ADR-0003).

**Precision is the hard part here, not the geometry.** Over 40 AU the absolute
propagation phase is ~1e10 wavelengths, so forming ``R_a / c`` and differencing
the results loses roughly eight decimal digits exactly where the answer lives:
the *differences* between elements are of order the aperture, ~1e4 m against a
range of ~1e12 m. Computing ``R_a - R_ref`` naively in float64 leaves ~1e-3 m of
error, i.e. ~1e-8 rad at 1 kHz — an order of magnitude worse than this module's
1e-9 rad requirement. :func:`focal_phases` therefore never forms that difference
directly; see :func:`_differential_range`.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.constants import c
from gwtb.core.validation import as_body_array, as_float64


def _as_point(a: ArrayLike, name: str) -> NDArray[np.float64]:
    """Validate a position vector: shape ``(3,)``, float64, finite."""
    v = as_float64(a, name)
    if v.shape != (3,):
        raise ValueError(f"{name} must have shape (3,), got {v.shape}")
    return v


def _differential_range(
    offsets: NDArray[np.float64],
    to_focus: NDArray[np.float64],
    range_ref: float,
) -> NDArray[np.float64]:
    """``|to_focus - offsets_a| - |to_focus|``, without catastrophic cancellation.

    Both ranges are ~1e12 m and differ by ~1e4 m, so subtracting them directly
    discards the eight most significant digits of the answer. The identity

    .. code-block:: text

        R_a - R_ref = (R_a^2 - R_ref^2) / (R_a + R_ref)
                    = (|q_a|^2 - 2 s.q_a) / (R_a + R_ref)

    with ``q_a`` the element offset from the reference and ``s`` the vector from
    the reference to the focus, is algebraically identical but numerically
    benign: the huge ``|s|^2`` term cancels *symbolically* and never enters the
    arithmetic. What remains is formed from quantities of order ``|s||q|``,
    carrying full float64 relative precision, and the division by ``R_a + R_ref``
    restores the scale.

    Parameters
    ----------
    offsets
        Shape ``(N, 3)``, m. Element positions relative to the reference point.
    to_focus
        Shape ``(3,)``, m. Vector from the reference point to the focal point.
    range_ref
        ``|to_focus|``, m, passed in to avoid recomputing it.

    Returns
    -------
    ndarray
        Shape ``(N,)``, m. Signed range differences, accurate to ~1e-15 m at
        astronomical range rather than the ~1e-3 m of the naive difference.
    """
    numerator = np.einsum("ai,ai->a", offsets, offsets) - 2.0 * (offsets @ to_focus)
    range_a = np.linalg.norm(to_focus - offsets, axis=1)
    # einsum's numpy stub returns Any; annotate so mypy narrows the result back
    # to NDArray[np.float64] rather than silently widening the return type.
    result: NDArray[np.float64] = numerator / (range_a + range_ref)
    return result


def focal_phases(
    geometry: ArrayLike,
    frequencies: ArrayLike,
    focal_point: ArrayLike,
    focal_time: float,
) -> NDArray[np.float64]:
    """Per-element, per-frequency drive phases that focus at one space-time point.

    An element at ``p_a`` driven as ``sin(2 pi f t + phi_a)`` contributes, at the
    focal point, the phase ``2 pi f (t - R_a/c) + phi_a`` with ``R_a =
    |r_focus - p_a|``. Requiring every element and every frequency to arrive at
    the same phase at ``t = focal_time`` inverts to

    .. code-block:: text

        phi_a(f) = 2 pi f (R_a / c - focal_time)

    which is this function, evaluated in the numerically stable form described
    in :func:`_differential_range` and wrapped to ``[-pi, pi)``.

    **Each element gets its own exact delay.** The array centroid appears only
    as an arithmetic reference point for the differencing identity — never as a
    single delay standing in for the whole array, which is the quiet, high-damage
    error ADR-0002 §7 exists to forbid. The two are distinguishable by test, and
    ``tests/unit/test_focus.py`` distinguishes them: element phases are checked
    against exact ``decimal``-arithmetic ranges, which a centroid approximation
    fails by many orders of magnitude.

    Absolute versus differential phase: the term common to all elements,
    ``2 pi f (R_ref/c - focal_time)``, is ~1e8 rad at 1 kHz and 40 AU and so
    carries only ~1e-8 rad of float64 absolute accuracy. That limit is real but
    does not affect focusing, which depends only on element-to-element phase
    *differences* — these are exact to ~1e-15 rad. Recovering absolute phase at
    this range is what T-11.3's split-phase scheme is for.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 2 (the retarded-time
    relation ``t_ret = t - R/c`` whose per-element inversion this is; the
    inversion itself is this project's own construction, as no external
    gravitational-wave reference gives an array focusing phase law)

    Parameters
    ----------
    geometry
        Shape ``(N, 3)``, m. Element positions, per ADR-0002 §1.
    frequencies
        Shape ``(F,)``, Hz. Strictly positive.
    focal_point
        Shape ``(3,)``, m. Where the radiation is to coincide.
    focal_time
        Coordinate time at the focal point, s, at which coincidence occurs.

    Returns
    -------
    ndarray
        Shape ``(N, F)``, rad, wrapped to ``[-pi, pi)``. Element index leads,
        per ADR-0002 §1.

    Raises
    ------
    ValueError
        If shapes are wrong, frequencies are not positive, or the focal point
        coincides with an element (where the delay is undefined).
    """
    positions = as_body_array(geometry, "geometry")
    freqs = as_float64(frequencies, "frequencies")
    target = _as_point(focal_point, "focal_point")

    if freqs.ndim != 1 or freqs.size == 0:
        raise ValueError(f"frequencies must have shape (F,), got {freqs.shape}")
    if np.any(freqs <= 0.0):
        raise ValueError("frequencies must be strictly positive")
    if not math.isfinite(focal_time):
        raise ValueError(f"focal_time must be finite, got {focal_time!r}")

    reference = positions.mean(axis=0)
    offsets = positions - reference
    to_focus = target - reference
    range_ref = float(np.linalg.norm(to_focus))

    ranges = np.linalg.norm(target - positions, axis=1)
    if np.any(ranges == 0.0):
        raise ValueError(
            "focal_point coincides with an array element; the propagation delay "
            "to that element is undefined"
        )

    delta_range = _differential_range(offsets, to_focus, range_ref)

    # Split deliberately: the differential term carries full precision, while
    # the common term is wrapped once, at its own (lower) absolute accuracy.
    # Adding them before wrapping would spread the common term's ~1e-8 rad error
    # across every element and destroy the differential accuracy.
    differential = 2.0 * np.pi * np.outer(delta_range / c, freqs)
    common = 2.0 * np.pi * freqs * (range_ref / c - focal_time)
    common_wrapped = np.remainder(common + np.pi, 2.0 * np.pi) - np.pi

    phases = differential + common_wrapped
    wrapped: NDArray[np.float64] = np.remainder(phases + np.pi, 2.0 * np.pi) - np.pi
    return wrapped


__all__ = ["focal_phases"]
