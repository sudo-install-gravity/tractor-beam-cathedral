"""Phased-array element geometries.

Every geometry returns element positions as an ``(N, 3)`` array per
ADR-0002 §1, in whatever local frame the array occupies (the caller
translates/rotates it into the engagement geometry downstream). These are
definitional constructions, not physics results with an external equation to
check, but the layouts themselves come from the standard antenna-array
literature.

Source: S. J. Orfanidis, *Electromagnetic Waves and Antennas* (open-access,
www.ece.rutgers.edu/~orfanidi/ewa), ch. 19 "Antenna Arrays", eq. 19.4.1
(element-position convention underlying the array factor definition used
throughout ``gwtb.array``).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def linear_array(n_elements: int, spacing: float) -> NDArray[np.float64]:
    """Uniformly spaced elements along the x-axis, centered on the origin.

    Source: Orfanidis, *EM Waves and Antennas*, ch. 19, eq. 19.4.1

    Parameters
    ----------
    n_elements
        Number of elements. Must be a positive integer.
    spacing
        Inter-element spacing, m. Must be positive.

    Returns
    -------
    ndarray
        Shape ``(n_elements, 3)``, m.
    """
    if not isinstance(n_elements, (int, np.integer)) or n_elements < 1:
        raise ValueError(f"n_elements must be a positive integer, got {n_elements!r}")
    if not np.isfinite(spacing) or spacing <= 0.0:
        raise ValueError(f"spacing must be positive and finite, got {spacing!r}")

    indices = np.arange(n_elements, dtype=np.float64)
    x = (indices - (n_elements - 1) / 2.0) * spacing
    positions = np.zeros((n_elements, 3), dtype=np.float64)
    positions[:, 0] = x
    return positions


def planar_array(nx: int, ny: int, dx: float, dy: float) -> NDArray[np.float64]:
    """A rectangular grid of elements in the z=0 plane, centered on the origin.

    Source: Orfanidis, *EM Waves and Antennas*, ch. 19, eq. 19.4.1
    (generalized to two dimensions)

    Parameters
    ----------
    nx, ny
        Element counts along x and y. Each must be a positive integer.
    dx, dy
        Spacing along x and y, m. Each must be positive.

    Returns
    -------
    ndarray
        Shape ``(nx * ny, 3)``, m. All elements have ``z == 0``.
    """
    for name, val in (("nx", nx), ("ny", ny)):
        if not isinstance(val, (int, np.integer)) or val < 1:
            raise ValueError(f"{name} must be a positive integer, got {val!r}")
    for name, fval in (("dx", dx), ("dy", dy)):
        if not np.isfinite(fval) or fval <= 0.0:
            raise ValueError(f"{name} must be positive and finite, got {fval!r}")

    ix = np.arange(nx, dtype=np.float64) - (nx - 1) / 2.0
    iy = np.arange(ny, dtype=np.float64) - (ny - 1) / 2.0
    grid_x, grid_y = np.meshgrid(ix * dx, iy * dy, indexing="ij")
    positions = np.zeros((nx * ny, 3), dtype=np.float64)
    positions[:, 0] = grid_x.ravel()
    positions[:, 1] = grid_y.ravel()
    return positions


def sparse_array(n_elements: int, aperture: float, seed: int) -> NDArray[np.float64]:
    """A reproducible, uniformly-random element layout within a circular
    aperture in the z=0 plane.

    Source: this project's own construction, eq. n/a (no external equation to
    cite): uniform-disk random sampling used to instantiate a sparse/thinned
    array geometry per BACKLOG.md T-5.7's open question OQ-4. Orfanidis, EM
    Waves and Antennas, ch. 19 discusses sparse/thinned arrays qualitatively
    but gives no equation for this scheme.

    Parameters
    ----------
    n_elements
        Number of elements. Must be a positive integer.
    aperture
        Aperture diameter, m. Must be positive.
    seed
        Seed for the pseudorandom generator; the same seed reproduces the
        same layout.

    Returns
    -------
    ndarray
        Shape ``(n_elements, 3)``, m. All elements have ``z == 0`` and lie
        within the disk of diameter ``aperture`` centered on the origin.
    """
    if not isinstance(n_elements, (int, np.integer)) or n_elements < 1:
        raise ValueError(f"n_elements must be a positive integer, got {n_elements!r}")
    if not np.isfinite(aperture) or aperture <= 0.0:
        raise ValueError(f"aperture must be positive and finite, got {aperture!r}")

    rng = np.random.default_rng(seed)
    radius = aperture / 2.0
    # Sample uniformly over the disk area (not uniformly in r), so density is
    # spatially uniform rather than concentrated at the center.
    r = radius * np.sqrt(rng.uniform(0.0, 1.0, size=n_elements))
    theta = rng.uniform(0.0, 2.0 * np.pi, size=n_elements)
    positions = np.zeros((n_elements, 3), dtype=np.float64)
    positions[:, 0] = r * np.cos(theta)
    positions[:, 1] = r * np.sin(theta)
    return positions


__all__ = ["linear_array", "planar_array", "sparse_array"]
