"""Benchmark: GW luminosity of a rigid spinning rod (T-2.8).

.. code-block:: text

    P = (2/45) (G/c^5) M^2 L^4 omega^6

**Citation status: VERIFIED by direct derivation**, not a `[verify]` textbook
placeholder. The `researcher` agent confirmed this reduces exactly from two
equation numbers already anchored in this codebase:

- Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 3 (trace-free quadrupole
  moment definition)
- Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 4 (quadrupole luminosity,
  ``F = (G/5c^5) Qddd_ij Qddd_ij``, matching ``gwtb.source.quadrupole.
  luminosity``)

**Derivation** (reproduced here so a future contributor can check it without
re-deriving): a uniform rod of mass ``M`` and length ``L`` has moment of
inertia about a perpendicular axis through its center ``I0 = M L^2 / 12``
(elementary integration, not itself a citable physics claim). Spinning about
that axis at angular rate ``omega``, its trace-free quadrupole moment is
``Q_ij(t) = I0 (n_i(t) n_j(t) - delta_ij/3)`` with
``n(t) = (cos(omega t), sin(omega t), 0)``. Differentiating three times:

.. code-block:: text

    Qddd_xx =  4 I0 omega^3 sin(2 omega t)
    Qddd_yy = -4 I0 omega^3 sin(2 omega t)
    Qddd_xy = -4 I0 omega^3 cos(2 omega t)
    Qddd_zz =  0

so ``Qddd_ij Qddd_ij = 32 I0^2 omega^6`` (constant in time — a feature of
rigid rotation). Substituting into eq. (4):

.. code-block:: text

    F = (G / 5c^5) * 32 I0^2 omega^6
      = (32 G / 5c^5) * (M L^2/12)^2 * omega^6
      = (2/45) (G/c^5) M^2 L^4 omega^6

an exact algebraic identity, confirmed numerically below to far tighter than
the required rtol 1e-6.

**Model used here.** ``gwtb.bodies.multipole`` operates on point-mass
systems, not continuum bodies, and finite-difference discretization of a
continuous rod would only converge to the required precision at large N.
Instead this benchmark uses an *exact* two-point-mass proxy: two point masses
of ``M/2`` each, held rigidly at the opposite ends of a rotating diameter of
length ``2 r_eff`` with ``r_eff = L / (2 sqrt(3))``, chosen so the proxy's
moment of inertia about the center exactly equals the continuous rod's
``I0 = M L^2/12`` (``2 * (M/2) * r_eff^2 = M r_eff^2 = M L^2/12``). Because
the quadrupole moment (and everything derived from it) depends on the mass
distribution only through this second moment, the two-point proxy reproduces
the continuous rod's quadrupole moment, ``Qddd``, and luminosity *exactly* —
not approximately — while exercising the actual production code
(``gwtb.bodies.multipole.quadrupole_second_derivative``/
``quadrupole_third_derivative`` and ``gwtb.source.quadrupole.luminosity``)
rather than reimplementing the formula by hand.

Per ``tests/benchmarks/helpers.py`` convention, reference constants are kept
independent of ``gwtb.core.constants`` so a drift in the package's own
constants cannot silently pass its own benchmark.
"""

from __future__ import annotations

import math

import numpy as np

from gwtb.bodies.multipole import quadrupole_second_derivative, quadrupole_third_derivative
from gwtb.source.quadrupole import luminosity
from tests.benchmarks.helpers import ReferenceConstants, assert_relative

_M = 1.0e4  # kg, rod total mass
_L = 10.0  # m, rod length
_OMEGA = 2.0 * math.pi * 1.0e3  # rad/s, 1 kHz spin


def _rod_kinematics(
    m_total: float, length: float, omega: float, t: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Two-point-mass proxy for a rigid rod spinning at angular rate omega.

    See module docstring: r_eff is chosen so 2*(m_total/2)*r_eff^2 equals the
    continuous rod's I0 = m_total*length^2/12 exactly.
    """
    r_eff = length / (2.0 * math.sqrt(3.0))

    cos_wt, sin_wt = math.cos(omega * t), math.sin(omega * t)
    n_hat = np.array([cos_wt, sin_wt, 0.0])
    n_hat_dot = omega * np.array([-sin_wt, cos_wt, 0.0])
    n_hat_ddot = -(omega**2) * n_hat
    n_hat_dddot = (omega**3) * np.array([sin_wt, -cos_wt, 0.0])

    masses = np.array([m_total / 2.0, m_total / 2.0])
    positions = np.array([r_eff * n_hat, -r_eff * n_hat])
    velocities = np.array([r_eff * n_hat_dot, -r_eff * n_hat_dot])
    accelerations = np.array([r_eff * n_hat_ddot, -r_eff * n_hat_ddot])
    jerks = np.array([r_eff * n_hat_dddot, -r_eff * n_hat_dddot])

    return masses, positions, velocities, accelerations, jerks


def test_spinning_rod_luminosity_matches_closed_form() -> None:
    ref = ReferenceConstants()
    t = 0.37  # arbitrary; Qddd_ij Qddd_ij is time-independent for rigid rotation
    masses, positions, velocities, accelerations, jerks = _rod_kinematics(_M, _L, _OMEGA, t)

    q_dddot = quadrupole_third_derivative(masses, positions, velocities, accelerations, jerks)
    power = luminosity(q_dddot)

    expected = (2.0 / 45.0) * ref.G_over_c5 * _M**2 * _L**4 * _OMEGA**6
    assert_relative(power, expected, rtol=1e-6, what="spinning rod GW luminosity")


def test_spinning_rod_luminosity_is_time_independent() -> None:
    """Rigid rotation: Qddd_ij Qddd_ij (and hence luminosity) does not depend
    on the phase at which it is evaluated -- a feature of the derivation, and
    a check that the two-point proxy behaves as a rigid body should."""
    powers = []
    for t in (0.0, 0.11, 0.53, 1.7, 3.3):
        masses, positions, velocities, accelerations, jerks = _rod_kinematics(_M, _L, _OMEGA, t)
        q_dddot = quadrupole_third_derivative(masses, positions, velocities, accelerations, jerks)
        powers.append(luminosity(q_dddot))

    powers_arr = np.array(powers)
    assert_relative(
        float(np.max(powers_arr)),
        float(np.min(powers_arr)),
        rtol=1e-9,
        what="time-independence of rigid-rotor luminosity",
    )


def test_spinning_rod_proxy_moment_of_inertia_matches_continuous_rod() -> None:
    """Sanity check on the two-point proxy itself: its quadrupole moment
    amplitude I0 must equal the continuous rod's M L^2/12 exactly."""
    t = 0.0
    masses, positions, _, _, _ = _rod_kinematics(_M, _L, _OMEGA, t)
    # At t=0, n_hat = (1,0,0), so Q_xx = I0*(2/3) directly (same algebra as
    # the T-1.3 unit-mass-on-axis check).
    from gwtb.bodies.multipole import quadrupole_moment

    q = quadrupole_moment(masses, positions)
    i0_expected = _M * _L**2 / 12.0
    assert_relative(float(q[0, 0]), (2.0 / 3.0) * i0_expected, rtol=1e-12, what="proxy I0")


def test_spinning_rod_luminosity_is_nonnegative() -> None:
    masses, positions, velocities, accelerations, jerks = _rod_kinematics(_M, _L, _OMEGA, 0.0)
    q_ddot = quadrupole_second_derivative(masses, positions, velocities, accelerations)
    q_dddot = quadrupole_third_derivative(masses, positions, velocities, accelerations, jerks)
    assert luminosity(q_dddot) >= 0.0
    assert q_ddot.shape == (3, 3)
