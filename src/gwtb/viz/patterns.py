"""Beam-pattern visualization: polar and 3D radiation-pattern plots.

Rendering is forced headless (``Agg`` backend) so these functions work in CI
and other environments without a display. Not a physics module (``viz/`` is
exempt from the citation-CI check); the underlying array-factor mathematics
matches :func:`gwtb.array.beamform.array_factor` (reimplemented vectorized
here for full-grid rendering speed rather than looping through it per point).
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from numpy.typing import ArrayLike  # noqa: E402


def _array_factor_magnitude(
    geometry: ArrayLike, weights: ArrayLike, wavelength: float, directions: np.ndarray
) -> np.ndarray:
    """Vectorized ``|AF|`` over an arbitrary batch of unit-vector directions,
    shape ``(..., 3)``, without looping through :func:`array_factor` per
    point (needed for full-sphere or fine-resolution sweeps)."""
    pos = np.asarray(geometry, dtype=np.float64)
    w = np.asarray(weights, dtype=np.complex128)
    d = np.asarray(directions, dtype=np.float64)
    k = (2.0 * np.pi / wavelength) * d
    phase = np.tensordot(k, pos, axes=([-1], [1]))  # shape (..., N)
    af = np.sum(w * np.exp(1j * phase), axis=-1)
    result: np.ndarray = np.abs(af)
    return result


def _pattern_db(
    geometry: ArrayLike,
    weights: ArrayLike,
    wavelength: float,
    theta: np.ndarray,
    floor_db: float,
) -> np.ndarray:
    """|AF(theta)| in dB relative to peak, scanning in the xz-plane, clamped
    to ``floor_db``."""
    directions = np.stack([np.sin(theta), np.zeros_like(theta), np.cos(theta)], axis=1)
    mags = _array_factor_magnitude(geometry, weights, wavelength, directions)
    peak = np.max(mags)
    with np.errstate(divide="ignore"):
        db = 20.0 * np.log10(np.where(mags > 0.0, mags / peak, 0.0))
    # np.asarray keeps the return concretely typed: some numpy stub
    # generations type np.maximum with a scalar operand as Any.
    return np.asarray(np.maximum(db, floor_db), dtype=np.float64)


def plot_pattern_polar(
    geometry: ArrayLike,
    weights: ArrayLike,
    wavelength: float,
    floor_db: float = -40.0,
    n_points: int = 721,
) -> Figure:
    """Polar plot of the array's radiation pattern, in dB relative to peak.

    Parameters
    ----------
    geometry
        Shape ``(N, 3)``, m.
    weights
        Shape ``(N,)``, complex excitation.
    wavelength
        Radiation wavelength, m.
    floor_db
        Lower dB floor for the radial axis (negative number). Must be
        negative.
    n_points
        Angular resolution over the full ``[-pi, pi]`` sweep.

    Returns
    -------
    matplotlib.figure.Figure
        Polar plot with the main lobe visible at its steered direction and
        sidelobe structure visible down to ``floor_db``.
    """
    if floor_db >= 0.0:
        raise ValueError(f"floor_db must be negative, got {floor_db!r}")

    theta = np.linspace(-np.pi, np.pi, n_points)
    db = _pattern_db(geometry, weights, wavelength, theta, floor_db)

    fig = plt.figure()
    ax = fig.add_subplot(projection="polar")
    ax.plot(theta, db)
    ax.set_ylim(floor_db, 0.0)
    ax.set_title("Array radiation pattern (dB, relative to peak)")
    return fig


def plot_pattern_3d(
    geometry: ArrayLike,
    weights: ArrayLike,
    wavelength: float,
    floor_db: float = -40.0,
    n_theta: int = 181,
    n_phi: int = 361,
) -> Figure:
    """3D surface plot of the array's radiation pattern over the full
    sphere, in dB relative to peak.

    Parameters
    ----------
    geometry
        Shape ``(N, 3)``, m.
    weights
        Shape ``(N,)``, complex excitation.
    wavelength
        Radiation wavelength, m.
    floor_db
        Lower dB floor (negative number); values are clamped at this floor
        and remapped to a non-negative radius so the floor renders as a
        point at the origin rather than a negative radius.
    n_theta, n_phi
        Angular resolution in polar and azimuthal angle.

    Returns
    -------
    matplotlib.figure.Figure
        3D surface plot, with radius ``(db - floor_db)`` so the pattern's
        peak direction is the point farthest from the origin.
    """
    if floor_db >= 0.0:
        raise ValueError(f"floor_db must be negative, got {floor_db!r}")

    theta = np.linspace(0.0, np.pi, n_theta)
    phi = np.linspace(-np.pi, np.pi, n_phi)
    theta_grid, phi_grid = np.meshgrid(theta, phi, indexing="ij")

    directions = np.stack(
        [
            np.sin(theta_grid) * np.cos(phi_grid),
            np.sin(theta_grid) * np.sin(phi_grid),
            np.cos(theta_grid),
        ],
        axis=-1,
    )
    mags = _array_factor_magnitude(geometry, weights, wavelength, directions)
    peak = np.max(mags)
    with np.errstate(divide="ignore"):
        db = 20.0 * np.log10(np.where(mags > 0.0, mags / peak, 0.0))
    db = np.maximum(db, floor_db)
    radius = db - floor_db  # >= 0, zero at the floor

    x = radius * np.sin(theta_grid) * np.cos(phi_grid)
    y = radius * np.sin(theta_grid) * np.sin(phi_grid)
    z = radius * np.cos(theta_grid)

    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")
    ax.plot_surface(x, y, z, cmap="viridis", linewidth=0, antialiased=True)
    ax.set_title("Array radiation pattern (3D, dB relative to peak)")
    return fig


def plot_polarization_ellipse(h_plus: float, h_cross: float, n_points: int = 200) -> Figure:
    """Deformation of a ring of free-falling test particles under a passing
    GW — the visual spin-2 signature.

    .. code-block:: text

        x'(theta) = (1 + h_plus/2) R cos(theta) + (h_cross/2) R sin(theta)
        y'(theta) = (h_cross/2) R cos(theta) + (1 - h_plus/2) R sin(theta)

    the standard geodesic-deviation displacement of a ring of test masses
    (see :func:`gwtb.target.geodesic.deviation_acceleration`), with
    ``h_ij = [[h_plus, h_cross], [h_cross, -h_plus]]`` in the
    ``h_xx = -h_yy = h_plus``, ``h_xy = h_yx = h_cross`` convention.

    **AC, visually**: pure ``h_plus`` stretches the ring along one axis and
    squeezes the perpendicular one (an ellipse aligned with x/y); pure
    ``h_cross`` produces the identical ellipse shape but rotated 45 degrees —
    not 90, the spin-2 signature CLAUDE.md rule 4 names.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 2.22 (the
    ``h_plus``/``h_cross`` component convention this displacement uses)

    Parameters
    ----------
    h_plus, h_cross
        Dimensionless strain amplitudes.
    n_points
        Number of points to trace the ring with. Must be at least 8.

    Returns
    -------
    matplotlib.figure.Figure
    """
    if n_points < 8:
        raise ValueError(f"n_points must be at least 8, got {n_points!r}")

    theta = np.linspace(0.0, 2.0 * np.pi, n_points)
    radius = 1.0
    x_undeformed = radius * np.cos(theta)
    y_undeformed = radius * np.sin(theta)
    x_deformed = (1.0 + h_plus / 2.0) * x_undeformed + (h_cross / 2.0) * y_undeformed
    y_deformed = (h_cross / 2.0) * x_undeformed + (1.0 - h_plus / 2.0) * y_undeformed

    fig, ax = plt.subplots()
    ax.plot(x_undeformed, y_undeformed, "k--", alpha=0.3, label="undeformed")
    ax.plot(x_deformed, y_deformed, "b-", label="deformed")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect("equal")
    ax.legend()
    return fig


def plot_trade_surface(
    frequencies: ArrayLike, apertures: ArrayLike, invariant_wavelengths: float = 6.16e9
) -> Figure:
    """Required-aperture-vs-frequency trade-surface plot.

    Log-log axes, since the trade surface (:func:`gwtb.array.focus.
    trade_surface`) spans many decades in both frequency and aperture; the
    invariant ``D/lambda`` product is annotated as a horizontal reference
    line, since :func:`gwtb.array.focus.trade_surface`'s whole point is that
    this ratio does not depend on frequency.

    Parameters
    ----------
    frequencies
        Shape ``(F,)``, Hz.
    apertures
        Shape ``(F,)``, m. From :func:`gwtb.array.focus.trade_surface`.
    invariant_wavelengths
        The frequency-independent ``D/lambda`` requirement to annotate, e.g.
        ~6.16e9 for a 1 km spot at 40 AU.

    Returns
    -------
    matplotlib.figure.Figure
    """
    freqs = np.asarray(frequencies, dtype=np.float64)
    aps = np.asarray(apertures, dtype=np.float64)
    if freqs.shape != aps.shape:
        raise ValueError(
            f"frequencies and apertures must have the same shape, got {freqs.shape} and {aps.shape}"
        )

    fig, ax = plt.subplots()
    ax.loglog(freqs, aps, "b-o")
    ax.set_xlabel("Drive frequency (Hz)")
    ax.set_ylabel("Required aperture D (m)")
    ax.set_title(f"D/λ invariant ≈ {invariant_wavelengths:.2e}")
    ax.grid(True, which="both", alpha=0.3)
    return fig


__all__ = [
    "plot_pattern_3d",
    "plot_pattern_polar",
    "plot_polarization_ellipse",
    "plot_trade_surface",
]
