"""Threat-population anchors for the deflection tradespace (Sprint 14, R8).

This module is exempt from the ``source``/``propagate``/``bodies``/``array``
citation-CI check (``tools/check_citations.py``) — it consumes measured
mass/diameter/velocity figures from the planetary-defense literature rather
than introducing new radiation physics, in the same style as
``target/coupling.py`` and ``target/deflection.py``. Every anchor still
carries an explicit source for auditability.

Sources (full verification record: ``docs/BACKLOG.md`` Sprint 14 header,
verified 2026-08-08):

- **[P13]** Popova, O. P. et al., "Chelyabinsk Airburst, Damage Assessment,
  Meteorite Recovery, and Characterization," *Science* **342**, 1069 (2013):
  entry speed 19.16 +/- 0.15 km/s, mass 1.3e7 kg (factor-of-two uncertainty),
  diameter 19.8 +/- 4.6 m.
- **[D23]** Daly, R. T. et al., "Successful kinetic impact into an asteroid
  for planetary defence," *Nature* **616**, 443 (2023): Dimorphos volume-
  equivalent diameter 151 +/- 5 m, assumed bulk density 2400 +/- 300 kg/m^3
  (equal to Didymos's). The paper states no mass directly — the 4.3e9 kg
  anchor below is *derived* from those two cited numbers, not quoted.
- **[S19]** Scheeres, D. J. et al., "The dynamic geophysical environment of
  (101955) Bennu based on OSIRIS-REx measurements," *Nature Astronomy* **3**,
  352 (2019): mass 7.329 +/- 0.009e10 kg, bulk density 1190 +/- 13 kg/m^3.
  (Not Lauretta et al., *Nature* 568:55 (2019) — that paper covers surface
  particle ejection, not mass/density, and is the wrong citation for this
  claim; see the Sprint 14 header's plan-review note.)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

#: Bulk density of a rubble-pile body, kg/m^3. Source: [S19] (Bennu).
RHO_RUBBLE_PILE = 1190.0

#: Bulk density of a monolithic/stony body, kg/m^3. Source: [D23] (Didymos,
#: assumed equal for Dimorphos).
RHO_STONY = 2400.0


@dataclass(frozen=True)
class ThreatAnchor:
    """One real, measured or well-constrained threat-object data point.

    Attributes
    ----------
    name
        Object name, e.g. ``"Chelyabinsk"``.
    diameter_m
        Effective diameter, m.
    mass_kg
        Mass, kg.
    speed_mps
        Earth-relative encounter or entry speed, m/s, or ``None`` if the
        source does not report one for this object (e.g. Dimorphos and
        Bennu are mass/density anchors, not velocity anchors).
    source
        Short citation key, e.g. ``"[P13]"`` — never empty (absence-loud).
    """

    name: str
    diameter_m: float
    mass_kg: float
    speed_mps: float | None
    source: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must be a non-empty string")
        if not self.source:
            raise ValueError(f"{self.name}: source must be a non-empty string")
        if not math.isfinite(self.diameter_m) or self.diameter_m <= 0.0:
            raise ValueError(
                f"{self.name}: diameter_m must be positive and finite, got {self.diameter_m!r}"
            )
        if not math.isfinite(self.mass_kg) or self.mass_kg <= 0.0:
            raise ValueError(
                f"{self.name}: mass_kg must be positive and finite, got {self.mass_kg!r}"
            )
        if self.speed_mps is not None and (
            not math.isfinite(self.speed_mps) or self.speed_mps <= 0.0
        ):
            raise ValueError(
                f"{self.name}: speed_mps must be positive and finite when given, "
                f"got {self.speed_mps!r}"
            )


ANCHORS: tuple[ThreatAnchor, ...] = (
    ThreatAnchor(
        name="Chelyabinsk",
        diameter_m=19.8,
        mass_kg=1.3e7,
        speed_mps=1.916e4,
        source="[P13]",
    ),
    ThreatAnchor(
        name="Dimorphos",
        diameter_m=151.0,
        mass_kg=4.3e9,
        speed_mps=None,
        source="[D23] -- mass derived from diameter + density, not directly stated",
    ),
    ThreatAnchor(
        name="Bennu",
        diameter_m=490.0,
        mass_kg=7.329e10,
        speed_mps=None,
        source="[S19]",
    ),
)


def mass_from_diameter(diameter: float, density: float) -> float:
    """Mass of a uniform sphere from diameter and bulk density.

    .. code-block:: text

        mass = density * pi * diameter^3 / 6

    Elementary geometry (sphere volume ``(4/3) pi r^3`` with ``r = diameter/2``)
    times a bulk density — not itself a citable physics claim, the same
    treatment as the impulse-momentum relation in
    ``target/deflection.py:delta_v``. Where a specific density is used, the
    source of *that number* is cited instead (see :data:`RHO_RUBBLE_PILE`,
    :data:`RHO_STONY`).

    Parameters
    ----------
    diameter
        m. Must be positive and finite.
    density
        kg/m^3. Must be positive and finite.

    Returns
    -------
    float
        kg.
    """
    if not math.isfinite(diameter) or diameter <= 0.0:
        raise ValueError(f"diameter must be positive and finite, got {diameter!r}")
    if not math.isfinite(density) or density <= 0.0:
        raise ValueError(f"density must be positive and finite, got {density!r}")

    return density * math.pi * diameter**3 / 6.0


__all__ = [
    "ANCHORS",
    "RHO_RUBBLE_PILE",
    "RHO_STONY",
    "ThreatAnchor",
    "mass_from_diameter",
]
