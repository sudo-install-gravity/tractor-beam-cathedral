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

from gwtb.core.constants import GM_EARTH, M_SUN, R_EARTH_EQ, G


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


def required_miss_distance(v_infinity: float) -> float:
    """Impact parameter an object must clear to miss Earth, given its
    hyperbolic excess speed (gravitational focusing).

    .. code-block:: text

        v_esc = sqrt(2 * GM_EARTH / R_EARTH_EQ)
        required_miss_distance = R_EARTH_EQ * sqrt(1 + v_esc^2 / v_infinity^2)

    Elementary two-body mechanics (conservation of energy and angular
    momentum in an unperturbed hyperbolic encounter: for an object with
    impact parameter ``b`` and speed ``v_infinity`` at infinity, angular
    momentum ``L = v_infinity * b`` equals ``v_peri * R_EARTH_EQ`` at closest
    approach, and energy conservation gives ``v_peri^2 = v_infinity^2 +
    v_esc^2``; combining and solving for the ``b`` that grazes the surface
    yields the closed form above) — not itself a citable physics claim, the
    same treatment as ``delta_v`` and ``miss_distance`` above.

    **No open source with a citable equation number for this exact
    combination was found** despite four documented search attempts
    (``docs/BACKLOG.md`` Sprint 14 header, researcher pass 2026-08-08); this
    invokes the module's elementary-mechanics carve-out rather than citing
    a chapter reference, which ``CLAUDE.md`` rule 1 rejects as not a
    citation.

    Parameters
    ----------
    v_infinity
        Hyperbolic excess (closing) speed relative to Earth, far from
        Earth's gravity well, m/s. Must be positive and finite.

    Returns
    -------
    float
        m. The minimum unperturbed impact parameter for a miss; strictly
        decreasing in ``v_infinity`` (a faster object is focused less).
    """
    if not math.isfinite(v_infinity) or v_infinity <= 0.0:
        raise ValueError(f"v_infinity must be positive and finite, got {v_infinity!r}")

    v_esc = math.sqrt(2.0 * GM_EARTH / R_EARTH_EQ)
    return R_EARTH_EQ * math.sqrt(1.0 + (v_esc / v_infinity) ** 2)


def required_delta_v(miss: float, lead_time: float, orbit: float, regime: str) -> float:
    """Required velocity change to open a given miss distance, in either of
    two published regimes.

    .. code-block:: text

        impulsive-floor:  delta_v = miss / lead_time
        secular:          delta_v = miss / (3 * lead_time)

    ``"impulsive-floor"`` is the elementary impulsive-limit relation (see
    :func:`miss_distance`, inverted) and is an **upper bound** on the true
    requirement at every lead time, since secular orbital drift never
    delivers less displacement per unit Delta-v than the impulsive estimate.

    ``"secular"`` is the long-lead-time regime, where the along-track drift
    from a change in orbital mean motion accumulates over many orbits.

    Source: Izzo, D., "On the Deflection of Potentially Hazardous Objects,"
    AAS 05-141 (2005), eq. (2) (``s = 3 * delta_v * t_s`` in the impulsive,
    near-circular-orbit reduction of the paper's general integral form, for
    a tangential Delta-v applied a time ``t_s`` before the original close
    approach), specialized here with the paper's eq. (3) geometry factor
    gamma = 1 (real encounters have gamma in [0.65, 1] per the paper's
    Table 1; this makes the requirement optimistic by at most ~0.19 decades,
    negligible against the ~30-decade gaps this project reports -- see the
    assumption ledger, ``docs/BACKLOG.md`` Sprint 14 D-14.3).

    The secular regime needs multiple orbits to accumulate the stated drift,
    so this raises when ``lead_time`` is shorter than the orbital period
    implied by ``orbit`` -- the mirror image of :func:`miss_distance`'s
    guard, which instead requires the *impulsive* limit's short-lead-time
    assumption.

    Parameters
    ----------
    miss
        Required miss distance, m. Must be positive and finite.
    lead_time
        Time between the deflection action and the original close approach,
        s. Must be positive and finite.
    orbit
        The target's orbital semi-major axis, m. Used to compute the orbital
        period for the ``"secular"`` regime's validity guard. Must be
        positive and finite.
    regime
        ``"impulsive-floor"`` or ``"secular"``. Any other value raises --
        there is no silent default (``CLAUDE.md`` rule 8).

    Returns
    -------
    float
        m/s. Always positive (both ``miss`` and ``lead_time`` are required
        positive).
    """
    if not math.isfinite(miss) or miss <= 0.0:
        raise ValueError(f"miss must be positive and finite, got {miss!r}")
    if not math.isfinite(lead_time) or lead_time <= 0.0:
        raise ValueError(f"lead_time must be positive and finite, got {lead_time!r}")
    if not math.isfinite(orbit) or orbit <= 0.0:
        raise ValueError(f"orbit must be positive and finite, got {orbit!r}")

    if regime == "impulsive-floor":
        return miss / lead_time

    if regime == "secular":
        period = 2.0 * np.pi * math.sqrt(orbit**3 / (G * M_SUN))
        if lead_time < period:
            raise ValueError(
                f"lead_time ({lead_time:.3e} s) is shorter than the orbital "
                f"period ({period:.3e} s) implied by orbit={orbit!r} m; the "
                f"secular regime requires multiple orbits for the along-"
                f"track drift to accumulate"
            )
        return miss / (3.0 * lead_time)

    raise ValueError(f"regime must be 'impulsive-floor' or 'secular', got {regime!r}")


__all__ = ["delta_v", "miss_distance", "required_delta_v", "required_miss_distance"]
