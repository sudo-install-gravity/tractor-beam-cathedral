"""Non-gravitational-wave coupling channels for comparison: the gravity
tractor (near-zone Newtonian gravitational attraction).

This module is exempt from the ``source``/``propagate``/``bodies``/``array``
citation-CI check (it consumes/compares results rather than introducing new
radiation physics), but the formula below is still cited for auditability.

Source: R. Schweickart, C. Chapman, D. Durda & P. Hut, "Threat Mitigation:
The Gravity Tractor," B612 Foundation White Paper 042, arXiv:physics/0608157
(2006), p.2 §II (unnumbered display equation; restates Lu & Love, *Nature*
438, 177 (2005), which is itself a two-page unnumbered-equation letter).
Worked example confirmed against Fig. 2 (p.9) of the same paper.
"""

from __future__ import annotations

import numpy as np

from gwtb.core.constants import G


def channel_gravity_tractor(tractor_mass: float, separation: float, asteroid_mass: float) -> float:
    """Gravitational-tractor thrust: simple Newtonian two-point-mass
    attraction, treating both tractor and asteroid as point masses.

    .. code-block:: text

        F = G * tractor_mass * asteroid_mass / separation^2

    This neglects the asteroid's own finite extent and internal structure
    (it is not a point mass at the separations of interest, e.g.
    ``separation ~ 1.5 * asteroid_radius`` in the paper's own worked
    example) — an assumption the source paper itself does not quantify, and
    which this project's assumption ledger should record if this channel is
    used quantitatively (BACKLOG.md T-8.5, open question OQ-5).

    Source: Schweickart, Chapman, Durda & Hut, arXiv:physics/0608157 (2006),
    p.2, eq. n/a (unnumbered; see module docstring)

    Parameters
    ----------
    tractor_mass
        Mass of the tractor spacecraft, kg. Must be positive.
    separation
        Distance between tractor and asteroid center, m. Must be positive.
    asteroid_mass
        Mass of the target asteroid, kg. Must be positive.

    Returns
    -------
    float
        Thrust force, N.
    """
    for name, value in (
        ("tractor_mass", tractor_mass),
        ("separation", separation),
        ("asteroid_mass", asteroid_mass),
    ):
        if not np.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be positive and finite, got {value!r}")

    return G * tractor_mass * asteroid_mass / separation**2


__all__ = ["channel_gravity_tractor"]
