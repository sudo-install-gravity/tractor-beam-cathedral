"""Physical constants, in SI, with sources.

Single source of truth for every constant in the package. Per
``docs/adr/0002-array-conventions.md`` §4 the whole codebase works in SI — no
geometric units (``G = c = 1``) anywhere — so the coupling factors below appear
explicitly in every equation rather than being absorbed into the units.

That is deliberate. Much of the source literature works in geometric units
(Flanagan & Hughes eq. 4.23 is an example), and the conversion back to SI is
exactly where factors of ``G/c^4`` get silently dropped.
"""

from __future__ import annotations

# --- Fundamental -----------------------------------------------------------

#: Newtonian constant of gravitation, m^3 kg^-1 s^-2. CODATA 2018.
G = 6.67430e-11

#: Speed of light in vacuum, m s^-1. Exact by SI definition (not measured).
c = 299792458.0

# --- Astronomical ----------------------------------------------------------

#: Astronomical unit, m. IAU 2012 Resolution B2 — exact by definition.
AU = 1.495978707e11

#: Nominal solar mass, kg. Derived from the IAU 2015 Resolution B3 nominal
#: solar mass parameter GM_sun / G.
M_SUN = 1.98892e30

#: Parsec, m. IAU 2015 Resolution B2: 648000/pi astronomical units.
PARSEC = 3.0856775814913673e16

# --- Derived coupling factors ---------------------------------------------
#
# These two numbers set the scale of everything this project computes, and
# their smallness is the feasibility gap documented in docs/PHYSICS.md §8.

#: Strain coupling, s^2 kg^-1 m^-1. Prefactor of the quadrupole formula.
G_OVER_C4 = G / c**4

#: Luminosity coupling, s^3 kg^-1 m^-2. Prefactor of the quadrupole flux.
G_OVER_C5 = G / c**5

# --- Project-specific ------------------------------------------------------

#: Nominal engagement range for the tractor-beam concept, m (40 AU).
TARGET_RANGE = 40.0 * AU

#: Earth nominal terrestrial mass parameter, m^3 s^-2. IAU 2015 Resolution
#: B3 nominal value. Source: Prsa, A. et al., "Nominal values for selected
#: solar and planetary quantities: IAU 2015 Resolution B3," Astron. J. 152,
#: 41 (2016), arXiv:1605.09788, Table 1.
GM_EARTH = 3.986004e14

#: Earth nominal equatorial radius, m. IAU 2015 Resolution B3 nominal value.
#: Source: Prsa et al. 2016 (above), Table 1.
R_EARTH_EQ = 6.3781e6

__all__ = [
    "AU",
    "G",
    "GM_EARTH",
    "G_OVER_C4",
    "G_OVER_C5",
    "M_SUN",
    "PARSEC",
    "R_EARTH_EQ",
    "TARGET_RANGE",
    "c",
]
