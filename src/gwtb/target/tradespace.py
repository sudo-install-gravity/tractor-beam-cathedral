"""The deflection tradespace: detection distance, closure velocity, threat
mass, and the gravity-spike strength required to convert an Earth-impacting
trajectory into a miss within the available lead time (Sprint 14, paper
Results section R8).

This module is arithmetic over results computed elsewhere (``target/threat.py``,
``target/deflection.py``, ``target/coupling.py``) and is exempt from
``tools/check_citations.py`` along with the rest of ``target/`` (see
``tools/check_citations.py``'s ``PHYSICS_PACKAGES``): it introduces no new
physics, only assembles cited results.

**Lives in ``target/``, not ``ledger/`` (deviation from the as-written
``docs/BACKLOG.md`` T-14.5 path).** The planned path was
``src/gwtb/ledger/tradespace.py``, but this module composes
``target/threat.py``, ``target/deflection.py`` and ``target/coupling.py`` --
and ``target/coupling.py`` already imports ``ledger/gap_report.py`` for
:class:`~gwtb.ledger.gap_report.GapReport`. Placing this module under
``ledger/`` would therefore create a new ``(ledger, target)`` package cycle,
caught by ``tests/unit/test_architecture.py``, alongside the one genuine,
documented cycle (``source``, ``propagate``). Unlike that one, this cycle
would be an accident of file placement, not a real mutual dependency -- so
the fix is to move the file to keep the existing one-directional rule
(``target`` depends on ``ledger``, never the reverse) rather than to
document a second cycle that misrepresents the architecture.

**The structural finding this module exists to compute (D-14.6,
``docs/BACKLOG.md`` Sprint 14):** with the decision chain fixed at planning
(radial-closing lead time ``t = d/v_infinity``, thrust duration = lead time,
absorption-channel force sized at the source-target distance), the required
luminosity reduces to

.. code-block:: text

    L_req = 4 * pi * c * mass * miss_required * v_infinity^2 / (k * cross_section)

where ``k`` is 1 for the impulsive-floor regime and 3 for the secular regime
-- **the detection distance ``d`` cancels exactly.** Detecting farther buys
a longer lead time and therefore a smaller required force and Delta-v, but
not a smaller required luminosity: the inverse-square dilution over the
longer path exactly offsets what the longer lead time buys. ``gap_decades_*``
is therefore independent of ``detection_distance_m`` at fixed
``(v_infinity_mps, diameter_m, density_kgm3)`` -- asserted in
``tests/unit/test_tradespace.py``, not merely claimed here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from gwtb.core.constants import AU, M_SUN, G
from gwtb.target.coupling import required_luminosity
from gwtb.target.deflection import required_delta_v, required_miss_distance
from gwtb.target.threat import mass_from_diameter

#: D-14.7 grid: detection distances, m.
DETECTION_DISTANCES_M: tuple[float, ...] = tuple(au * AU for au in (0.1, 0.3, 1.0, 3.0, 10.0, 40.0))

#: D-14.7 grid: hyperbolic excess (closing) speeds, m/s. 17300 m/s is the
#: [G12] mean impact speed 20.6 km/s stripped of gravitational focusing:
#: sqrt(20600^2 - 11190^2) (see the Sprint 14 header).
V_INFINITY_MPS: tuple[float, ...] = (5.0e3, 1.0e4, 1.73e4, 3.0e4, 5.0e4, 7.2e4)

#: D-14.7 grid: threat-object diameters, m.
DIAMETERS_M: tuple[float, ...] = (20.0, 50.0, 140.0, 500.0, 1.0e3, 1.0e4)

#: D-14.7 grid: threat-object bulk densities, kg/m^3 ([S19] rubble-pile,
#: [D23] stony -- see ``gwtb.target.threat``).
DENSITIES_KGM3: tuple[float, ...] = (1190.0, 2400.0)

#: Orbit used for the secular-regime validity guard and period, m (D-14.2).
_ORBIT_M = AU


def _orbital_period(orbit: float) -> float:
    """Kepler orbital period at semi-major axis ``orbit`` around the Sun."""
    return 2.0 * math.pi * math.sqrt(orbit**3 / (G * M_SUN))


@dataclass(frozen=True)
class TradespaceCell:
    """One point in the (detection distance, closure velocity, diameter,
    density) tradespace grid.

    Fifteen fields, fixed by ``docs/BACKLOG.md`` T-14.5. The three
    ``*_secular*`` float fields (``delta_v_secular_mps``,
    ``luminosity_secular_w``, ``gap_decades_secular``) are ``nan`` **iff**
    ``secular_valid`` is ``False`` -- enforced in :meth:`__post_init__`, so
    the invariant holds for every cell ever constructed, not just the ones
    :func:`tradespace` builds. **``secular_valid`` is the contract; ``nan``
    is only the poison behind it** -- every consumer must filter on the
    flag, never on ``math.isnan``, per the Sprint 14 header's trap list.

    There is deliberately no ``force_secular_n``: the d-cancelled secular
    luminosity is computed directly from ``delta_v_secular_mps`` without
    needing an intermediate force value, and a field nobody computes would
    invite a silent-wrong fill.

    Attributes
    ----------
    detection_distance_m, v_infinity_mps, diameter_m, density_kgm3
        The grid coordinates.
    mass_kg
        From :func:`gwtb.target.threat.mass_from_diameter`.
    lead_time_s
        ``detection_distance_m / v_infinity_mps`` (D-14.2).
    miss_required_m
        From :func:`gwtb.target.deflection.required_miss_distance`.
    delta_v_floor_mps, delta_v_secular_mps
        From :func:`gwtb.target.deflection.required_delta_v`.
    force_floor_n
        The impulsive-floor force implied by ``delta_v_floor_mps`` applied
        continuously over ``lead_time_s`` (D-14.4).
    luminosity_floor_w, luminosity_secular_w
        From :func:`gwtb.target.coupling.required_luminosity`.
    gap_decades_floor, gap_decades_secular
        ``log10(required_luminosity / achieved_luminosity)`` for each regime.
    secular_valid
        Whether ``lead_time_s`` is at least one orbital period at
        ``orbit = AU`` -- the secular regime's validity guard
        (:func:`gwtb.target.deflection.required_delta_v`).
    """

    detection_distance_m: float
    v_infinity_mps: float
    diameter_m: float
    density_kgm3: float
    mass_kg: float
    lead_time_s: float
    miss_required_m: float
    delta_v_floor_mps: float
    delta_v_secular_mps: float
    force_floor_n: float
    luminosity_floor_w: float
    luminosity_secular_w: float
    gap_decades_floor: float
    gap_decades_secular: float
    secular_valid: bool

    def __post_init__(self) -> None:
        always_finite = {
            "detection_distance_m": self.detection_distance_m,
            "v_infinity_mps": self.v_infinity_mps,
            "diameter_m": self.diameter_m,
            "density_kgm3": self.density_kgm3,
            "mass_kg": self.mass_kg,
            "lead_time_s": self.lead_time_s,
            "miss_required_m": self.miss_required_m,
            "delta_v_floor_mps": self.delta_v_floor_mps,
            "force_floor_n": self.force_floor_n,
            "luminosity_floor_w": self.luminosity_floor_w,
            "gap_decades_floor": self.gap_decades_floor,
        }
        for name, value in always_finite.items():
            if not math.isfinite(value):
                raise ValueError(
                    f"TradespaceCell(d={self.detection_distance_m!r}, "
                    f"v={self.v_infinity_mps!r}, D={self.diameter_m!r}, "
                    f"rho={self.density_kgm3!r}): {name} must be finite, got {value!r}"
                )

        secular_fields = {
            "delta_v_secular_mps": self.delta_v_secular_mps,
            "luminosity_secular_w": self.luminosity_secular_w,
            "gap_decades_secular": self.gap_decades_secular,
        }
        if self.secular_valid:
            for name, value in secular_fields.items():
                if not math.isfinite(value):
                    raise ValueError(
                        f"TradespaceCell(d={self.detection_distance_m!r}, "
                        f"v={self.v_infinity_mps!r}, D={self.diameter_m!r}, "
                        f"rho={self.density_kgm3!r}): secular_valid is True but "
                        f"{name} is not finite ({value!r})"
                    )
        else:
            for name, value in secular_fields.items():
                if not math.isnan(value):
                    raise ValueError(
                        f"TradespaceCell(d={self.detection_distance_m!r}, "
                        f"v={self.v_infinity_mps!r}, D={self.diameter_m!r}, "
                        f"rho={self.density_kgm3!r}): secular_valid is False so "
                        f"{name} must be nan, got {value!r}"
                    )


def _build_cell(
    detection_distance_m: float,
    v_infinity_mps: float,
    diameter_m: float,
    density_kgm3: float,
    achieved_luminosity: float,
) -> TradespaceCell:
    mass_kg = mass_from_diameter(diameter_m, density_kgm3)
    lead_time_s = detection_distance_m / v_infinity_mps
    miss_required_m = required_miss_distance(v_infinity_mps)
    cross_section = math.pi * (diameter_m / 2.0) ** 2

    delta_v_floor_mps = required_delta_v(miss_required_m, lead_time_s, _ORBIT_M, "impulsive-floor")
    force_floor_n = delta_v_floor_mps * mass_kg / lead_time_s
    luminosity_floor_w = required_luminosity(force_floor_n, cross_section, detection_distance_m)
    gap_decades_floor = math.log10(luminosity_floor_w / achieved_luminosity)

    secular_valid = lead_time_s >= _orbital_period(_ORBIT_M)
    if secular_valid:
        delta_v_secular_mps = required_delta_v(miss_required_m, lead_time_s, _ORBIT_M, "secular")
        force_secular_n = delta_v_secular_mps * mass_kg / lead_time_s
        luminosity_secular_w = required_luminosity(
            force_secular_n, cross_section, detection_distance_m
        )
        gap_decades_secular = math.log10(luminosity_secular_w / achieved_luminosity)
    else:
        delta_v_secular_mps = math.nan
        luminosity_secular_w = math.nan
        gap_decades_secular = math.nan

    return TradespaceCell(
        detection_distance_m=detection_distance_m,
        v_infinity_mps=v_infinity_mps,
        diameter_m=diameter_m,
        density_kgm3=density_kgm3,
        mass_kg=mass_kg,
        lead_time_s=lead_time_s,
        miss_required_m=miss_required_m,
        delta_v_floor_mps=delta_v_floor_mps,
        delta_v_secular_mps=delta_v_secular_mps,
        force_floor_n=force_floor_n,
        luminosity_floor_w=luminosity_floor_w,
        luminosity_secular_w=luminosity_secular_w,
        gap_decades_floor=gap_decades_floor,
        gap_decades_secular=gap_decades_secular,
        secular_valid=secular_valid,
    )


def tradespace(
    detection_distances: tuple[float, ...],
    v_infinities: tuple[float, ...],
    diameters: tuple[float, ...],
    densities: tuple[float, ...],
    achieved_luminosity: float,
) -> list[TradespaceCell]:
    """Build the full tradespace grid: one :class:`TradespaceCell` per
    combination of ``(detection_distances, v_infinities, diameters, densities)``.

    Iterates in that argument order (detection distance outermost, density
    innermost) -- callers relying on the returned list's ordering (e.g. the
    d-cancellation test, which groups by fixed ``(v, D, rho)``) may depend
    on this being stable.

    Parameters
    ----------
    detection_distances
        m. Typically :data:`DETECTION_DISTANCES_M`.
    v_infinities
        m/s. Typically :data:`V_INFINITY_MPS`.
    diameters
        m. Typically :data:`DIAMETERS_M`.
    densities
        kg/m^3. Typically :data:`DENSITIES_KGM3`.
    achieved_luminosity
        The array's achieved GW luminosity, W. Must be positive and finite.

    Returns
    -------
    list[TradespaceCell]
    """
    if not math.isfinite(achieved_luminosity) or achieved_luminosity <= 0.0:
        raise ValueError(
            f"achieved_luminosity must be positive and finite, got {achieved_luminosity!r}"
        )

    cells: list[TradespaceCell] = []
    for d in detection_distances:
        for v in v_infinities:
            for diam in diameters:
                for rho in densities:
                    cells.append(_build_cell(d, v, diam, rho, achieved_luminosity))
    return cells


def best_case_gap_decades(cells: list[TradespaceCell]) -> float:
    """Minimum ``gap_decades_secular`` over the ``secular_valid`` subset of
    ``cells`` -- the tradespace's most favourable corner.

    Filters on the :attr:`TradespaceCell.secular_valid` flag before taking
    the minimum, rather than calling ``min()`` directly on a sequence that
    may contain ``nan`` (order-dependent and silent -- see the module and
    Sprint 14 header's trap notes).

    Parameters
    ----------
    cells
        Typically the output of :func:`tradespace`.

    Returns
    -------
    float
        Decades. Raises ``ValueError`` if no cell has ``secular_valid``.
    """
    valid = [c.gap_decades_secular for c in cells if c.secular_valid]
    if not valid:
        raise ValueError("no secular_valid cells in the given tradespace -- nothing to report")
    return min(valid)


__all__ = [
    "DENSITIES_KGM3",
    "DETECTION_DISTANCES_M",
    "DIAMETERS_M",
    "V_INFINITY_MPS",
    "TradespaceCell",
    "best_case_gap_decades",
    "tradespace",
]
