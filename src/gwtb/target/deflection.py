"""From an applied force to an orbital deflection: the last two links in the
chain from a coupling channel (``target/coupling.py``) to a miss distance.

Both relations here are elementary Newtonian mechanics — impulse-momentum and
a linearized orbital displacement — not GW-specific physics, so neither
carries a numbered-equation citation in the sense ``CLAUDE.md`` rule 1 asks
for radiation formulas. Where a specific number is checked (the DART
cross-check), the source of *that number* is cited instead.
"""

from __future__ import annotations

import math

import numpy as np

from gwtb.core.constants import M_SUN, G


def delta_v(force: float, duration: float, asteroid_mass: float) -> float:
    """Velocity change from a sustained force applied over a duration.

    .. code-block:: text

        delta_v = force * duration / asteroid_mass

    Elementary impulse-momentum (``F dt = m dv``), not itself a citable
    physics claim — the same treatment as the rod moment of inertia in
    ``tests/benchmarks/test_spinning_rod.py``.

    **Cross-check.** DART (NASA's Double Asteroid Redirection Test) delivered
    an impulse of ``force * duration ~ 1.16e7`` N s to Dimorphos
    (``asteroid_mass = 4.3e9`` kg), producing ``delta_v ~ 2.7`` mm/s — the
    published order of the DART mission's measured deflection (Daly, R. T.
    et al., "Successful kinetic impact into an asteroid for planetary
    defence," *Nature* **616**, 443-447 (2023), doi:10.1038/s41586-023-05810-5).
    ``tests/unit/test_deflection.py`` reproduces this to rtol 1e-2.

    .. note::
       Spelling verified against Crossref 2026-08-03: Nature published this
       with British "defence". The arXiv preprint (arXiv:2303.02248) uses
       American "defense", so an exact-title search on the preprint will not
       match the journal record -- same paper, house-style difference. This
       docstring previously had the preprint spelling and a truncated page
       number.

    Parameters
    ----------
    force
        N. May be any finite value (a signed deflection direction is
        physically meaningful); only ``duration`` and ``asteroid_mass`` are
        required positive.
    duration
        s. Must be positive and finite.
    asteroid_mass
        kg. Must be positive and finite.

    Returns
    -------
    float
        m/s.
    """
    if not math.isfinite(force):
        raise ValueError(f"force must be finite, got {force!r}")
    if not math.isfinite(duration) or duration <= 0.0:
        raise ValueError(f"duration must be positive and finite, got {duration!r}")
    if not math.isfinite(asteroid_mass) or asteroid_mass <= 0.0:
        raise ValueError(f"asteroid_mass must be positive and finite, got {asteroid_mass!r}")

    return force * duration / asteroid_mass


def miss_distance(delta_v: float, lead_time: float, orbit: float) -> float:
    """Along-track miss distance from a velocity perturbation, impulsive limit.

    .. code-block:: text

        miss_distance = delta_v * lead_time

    The leading-order (impulsive-limit) displacement from a velocity
    perturbation applied well before arrival — elementary kinematics
    (displacement ~ velocity-change x time), valid for ``lead_time`` short
    compared with the orbital period, where secular orbital-mechanics
    amplification (the well-known "factor of a few" enhancement from
    along-track drift over many orbits, e.g. Ahrens & Harris, *Nature* 360,
    429 (1992)) has not yet accumulated. ``orbit`` is retained as the
    semi-major axis for that domain check rather than folded into the
    formula, since this project does not derive the secular-amplification
    factor from a citable primary source.

    Parameters
    ----------
    delta_v
        m/s. May be any finite value.
    lead_time
        s. Time between the deflection impulse and the original close
        approach. Must be positive and finite.
    orbit
        m. The target's orbital semi-major axis, used only to check that
        ``lead_time`` is short compared with the orbital period (the regime
        this linear formula is valid in); it does not enter the returned
        value. Must be positive and finite.

    Returns
    -------
    float
        m. Positive and negative ``delta_v`` give displacements in opposite
        directions along the same axis.
    """
    if not math.isfinite(delta_v):
        raise ValueError(f"delta_v must be finite, got {delta_v!r}")
    if not math.isfinite(lead_time) or lead_time <= 0.0:
        raise ValueError(f"lead_time must be positive and finite, got {lead_time!r}")
    if not math.isfinite(orbit) or orbit <= 0.0:
        raise ValueError(f"orbit must be positive and finite, got {orbit!r}")

    period = 2.0 * np.pi * math.sqrt(orbit**3 / (G * M_SUN))
    if lead_time > period:
        raise ValueError(
            f"lead_time ({lead_time:.3e} s) exceeds the orbital period "
            f"({period:.3e} s) implied by orbit={orbit!r} m; the impulsive-"
            f"limit approximation this function implements is not valid "
            f"outside lead_time << period"
        )

    return delta_v * lead_time


__all__ = ["delta_v", "miss_distance"]
