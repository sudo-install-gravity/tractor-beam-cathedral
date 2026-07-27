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
    return np.maximum(db, floor_db)


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


__all__ = ["plot_pattern_3d", "plot_pattern_polar"]
