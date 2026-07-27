"""Grating-lobe spacing constraint for a scanned phased array.

Source: S. J. Orfanidis, *Electromagnetic Waves and Antennas* (open-access,
www.ece.rutgers.edu/~orfanidi/ewa), ch. 19, eq. 19.9.6: the no-grating-lobe
condition ``d < lambda / (1 + |cos(phi0)|)``, where ``phi0`` is measured from
the array axis. ``gwtb`` measures ``scan_angle`` from broadside instead
(the common phased-array convention), which is the complementary angle:
``cos(phi0) = sin(theta_scan)``, giving ``d_max = lambda / (1 +
|sin(theta_scan)|)`` below. This axis-convention swap is a real trap (noted
by `researcher`), not a re-derivation of the physics.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def max_spacing(wavelength: float, scan_angle_max: float) -> float:
    """Largest element spacing that avoids grating lobes over the full scan
    range ``[-scan_angle_max, scan_angle_max]`` (measured from broadside).

    .. code-block:: text

        d_max = lambda / (1 + |sin(theta_scan_max)|)

    Source: Orfanidis, *EM Waves and Antennas*, ch. 19, eq. 19.9.6
    (broadside-referenced form; see module docstring)

    Parameters
    ----------
    wavelength
        Radiation wavelength, m. Must be positive.
    scan_angle_max
        Maximum scan angle from broadside, rad.

    Returns
    -------
    float
        Maximum grating-lobe-free spacing, m.
    """
    if not np.isfinite(wavelength) or wavelength <= 0.0:
        raise ValueError(f"wavelength must be positive and finite, got {wavelength!r}")
    if not np.isfinite(scan_angle_max):
        raise ValueError(f"scan_angle_max must be finite, got {scan_angle_max!r}")
    return float(wavelength / (1.0 + abs(np.sin(scan_angle_max))))


def has_grating_lobes(geometry: ArrayLike, wavelength: float, scan_angle_max: float) -> bool:
    """Whether the given element geometry can produce grating lobes when
    scanned up to ``scan_angle_max`` from broadside.

    Uses the minimum nearest-neighbor spacing in ``geometry`` as the
    controlling spacing (the tightest-packed pair sets the constraint).

    Source: Orfanidis, *EM Waves and Antennas*, ch. 19, eq. 19.9.6

    Parameters
    ----------
    geometry
        Shape ``(N, 3)`` element positions, m.
    wavelength
        Radiation wavelength, m.
    scan_angle_max
        Maximum scan angle from broadside, rad.

    Returns
    -------
    bool
        ``True`` if the minimum nearest-neighbor spacing exceeds
        :func:`max_spacing`.
    """
    pos = np.asarray(geometry, dtype=np.float64)
    if pos.ndim != 2 or pos.shape[1] != 3 or pos.shape[0] < 2:
        raise ValueError(f"geometry must have shape (N, 3) with N >= 2, got {pos.shape}")

    diffs = pos[:, None, :] - pos[None, :, :]
    dist = np.linalg.norm(diffs, axis=-1)
    np.fill_diagonal(dist, np.inf)
    min_spacing = float(np.min(dist))

    return bool(min_spacing > max_spacing(wavelength, scan_angle_max))


def _nearest_neighbor_spacing(geometry: NDArray[np.float64]) -> float:
    """Helper retained for tests: the minimum pairwise distance in geometry."""
    diffs = geometry[:, None, :] - geometry[None, :, :]
    dist = np.linalg.norm(diffs, axis=-1)
    np.fill_diagonal(dist, np.inf)
    return float(np.min(dist))


__all__ = ["has_grating_lobes", "max_spacing"]
