"""Benchmark: Hulse-Taylor pulsar PSR B1913+16 orbital decay (T-12.2).

The first observational confirmation that binary systems radiate energy as
gravitational waves (Hulse & Taylor, 1975 discovery; Taylor & Weisberg, 1982
first decay measurement) — this benchmark checks that the project's cited
eccentric-orbit decay formula reproduces the real, measured number.

**Eccentric-orbit secular decay rates.**

.. code-block:: text

    <da/dt> = -beta/a^3 * Psi(e),   Psi(e) = [1 + (73/24)e^2 + (37/96)e^4] / (1-e^2)^(7/2)
    <de/dt> = -(19/12) beta/a^4 * Phi(e),   Phi(e) = e[1 + (121/304)e^2] / (1-e^2)^(5/2)
    beta = (64/5) G^3 m1 m2 (m1+m2) / c^5

Source: Kowalska, Bulik, Belczynski, Dominik & Gondek-Rosinska, "The
eccentricity distribution of compact binaries," Astron. Astrophys. 527:A70
(2011), arXiv:1010.0511, eq. (1) [<da/dt>] and eq. (3) [<de/dt>].

**Not the original Peters (1964), Phys. Rev. 136, B1224.** That paper is
paywalled with no open mirror this project could confirm an equation number
against (two `researcher` passes tried and failed; see BACKLOG.md T-12.2's
resolution note, 2026-08-02). Kowalska et al. is cited instead: open-access,
peer-reviewed, and its eq. (1)/(3) prefactors verify algebraically against
the widely-quoted 73/24, 37/96, 121/304-coefficient form this project had
already confirmed via secondary sources (`-(19/12) * (64/5) = -304/15`,
exactly the de/dt coefficient). Their paper attributes the physics to Peters
& Mathews (1963) and Peters (1964).

**Converting <da/dt> to the observable, orbital-period decay Pdot_b**, via
Kepler's third law (`P_b^2 = 4 pi^2 a^3 / (G M)`, elementary — not itself a
citable claim): differentiating gives `Pdot_b / P_b = (3/2)(da/dt)/a`.

PSR B1913+16 system parameters (masses, orbital period, eccentricity,
observed Pdot_b) from Weisberg & Huang, "Relativistic Measurements from
Timing the Binary Pulsar PSR B1913+16," Astrophys. J. 829:55 (2016),
arXiv:1606.04581, Table 1 (masses, period, eccentricity) and eq. (1)/Table 1
(the Galactic-acceleration-corrected intrinsic Pdot_b).
"""

from __future__ import annotations

import math

import pytest

from tests.benchmarks.helpers import ReferenceConstants, assert_relative

# --- PSR B1913+16 system parameters -----------------------------------------
# Weisberg & Huang, ApJ 829:55 (2016), arXiv:1606.04581, Table 1.

_M_PULSAR_MSUN = 1.438  # pulsar mass, solar masses
_M_COMPANION_MSUN = 1.390  # companion mass, solar masses
_ORBITAL_PERIOD_S = 27906.9807520  # s (0.322997448918 days)
_ECCENTRICITY = 0.6171334

#: Observed, Galactic-acceleration-corrected intrinsic orbital decay rate,
#: dimensionless (s/s). Weisberg & Huang (2016) Table 1.
_OBSERVED_PDOT_B = -2.398e-12


def _psi(e: float) -> float:
    """Eccentricity factor for <da/dt>, Kowalska et al. eq. (1)."""
    return (1.0 + (73.0 / 24.0) * e**2 + (37.0 / 96.0) * e**4) / (1.0 - e**2) ** 3.5


def _phi(e: float) -> float:
    """Eccentricity factor for <de/dt>, Kowalska et al. eq. (3)."""
    return e * (1.0 + (121.0 / 304.0) * e**2) / (1.0 - e**2) ** 2.5


def _beta(m1: float, m2: float, ref: ReferenceConstants) -> float:
    """The mass/coupling prefactor shared by <da/dt> and <de/dt>."""
    return (64.0 / 5.0) * ref.G**3 * m1 * m2 * (m1 + m2) / ref.c**5


def _da_dt(a: float, e: float, m1: float, m2: float, ref: ReferenceConstants) -> float:
    """<da/dt>, m/s. Kowalska et al. eq. (1)."""
    return -_beta(m1, m2, ref) / a**3 * _psi(e)


def _de_dt(a: float, e: float, m1: float, m2: float, ref: ReferenceConstants) -> float:
    """<de/dt>, 1/s. Kowalska et al. eq. (3)."""
    return -(19.0 / 12.0) * _beta(m1, m2, ref) / a**4 * _phi(e)


def _semi_major_axis(period: float, m1: float, m2: float, ref: ReferenceConstants) -> float:
    """Kepler's third law: a from the orbital period and total mass."""
    total_mass = m1 + m2
    return (ref.G * total_mass * period**2 / (4.0 * math.pi**2)) ** (1.0 / 3.0)


def _pdot_b(period: float, e: float, m1: float, m2: float, ref: ReferenceConstants) -> float:
    """Predicted dimensionless orbital-period decay rate Pdot_b, from the
    Kowalska <da/dt> via Kepler's third law (Pdot_b/P_b = (3/2)(da/dt)/a)."""
    a = _semi_major_axis(period, m1, m2, ref)
    return 1.5 * period * _da_dt(a, e, m1, m2, ref) / a


def test_reproduces_the_observed_orbital_decay_rate() -> None:
    """AC: reproduces -2.4e-12 s/s to rtol 1e-2."""
    ref = ReferenceConstants()
    m1 = _M_PULSAR_MSUN * ref.M_sun
    m2 = _M_COMPANION_MSUN * ref.M_sun

    predicted = _pdot_b(_ORBITAL_PERIOD_S, _ECCENTRICITY, m1, m2, ref)

    assert_relative(predicted, -2.4e-12, rtol=1e-2, what="PSR B1913+16 Pdot_b")
    assert_relative(predicted, _OBSERVED_PDOT_B, rtol=1e-2, what="PSR B1913+16 Pdot_b vs. observed")


def test_decay_rate_is_negative() -> None:
    """The orbit shrinks — energy is radiated away, not gained."""
    ref = ReferenceConstants()
    m1 = _M_PULSAR_MSUN * ref.M_sun
    m2 = _M_COMPANION_MSUN * ref.M_sun
    assert _pdot_b(_ORBITAL_PERIOD_S, _ECCENTRICITY, m1, m2, ref) < 0.0


def test_eccentricity_amplifies_the_decay_rate() -> None:
    """Psi(e) is monotonically increasing in e — the eccentric orbit's
    perihelion-concentrated radiation makes it decay faster than a circular
    orbit of the same semi-major axis, a basic sanity property of the
    formula rather than an independent verification of it."""
    assert _psi(0.6171334) > _psi(0.3)
    assert _psi(0.3) > _psi(0.0)
    assert _psi(0.0) == pytest.approx(1.0)


def test_psi_and_phi_are_positive_for_a_physical_eccentricity() -> None:
    for e in (0.0, 0.1, 0.3, 0.6171334, 0.9):
        assert _psi(e) > 0.0
        assert _phi(e) >= 0.0  # zero only at e=0


def test_de_dt_coefficient_matches_the_previously_verified_304_over_15_form() -> None:
    """Cross-check the Kowalska-form prefactor against the already-verified
    (via multiple secondary sources, per BACKLOG.md) -304/15 e-coefficient
    form of <de/dt>, independent of the beta/Psi/Phi parametrization above."""
    assert -(19.0 / 12.0) * (64.0 / 5.0) == pytest.approx(-304.0 / 15.0, rel=1e-14)


def test_decay_rate_scales_as_expected_with_total_mass() -> None:
    """beta ~ m1 m2 (m1+m2), and a ~ (M P^2)^(1/3) at fixed period, so
    Pdot_b picks up a net M^(5/3)-like sensitivity for fixed mass ratio —
    checked here only as a monotonicity property (heavier system, faster
    decay at fixed period and eccentricity), not a specific exponent."""
    ref = ReferenceConstants()
    e = 0.3
    light = _pdot_b(_ORBITAL_PERIOD_S, e, 1.0 * ref.M_sun, 1.0 * ref.M_sun, ref)
    heavy = _pdot_b(_ORBITAL_PERIOD_S, e, 2.0 * ref.M_sun, 2.0 * ref.M_sun, ref)
    assert abs(heavy) > abs(light)


def test_semi_major_axis_matches_the_known_hulse_taylor_value() -> None:
    """PSR B1913+16's semi-major axis is well known (~1.95e9 m, ~0.013 AU —
    the two neutron stars orbit well inside Mercury's orbit) — an independent
    sanity check on the Kepler's-third-law conversion."""
    ref = ReferenceConstants()
    m1 = _M_PULSAR_MSUN * ref.M_sun
    m2 = _M_COMPANION_MSUN * ref.M_sun
    a = _semi_major_axis(_ORBITAL_PERIOD_S, m1, m2, ref)
    assert_relative(a, 1.95e9, rtol=1e-2, what="PSR B1913+16 semi-major axis")
