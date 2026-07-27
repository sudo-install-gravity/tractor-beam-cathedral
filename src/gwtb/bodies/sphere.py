"""Rigid uniform sphere: mass, moment of inertia, and the mass/radius/density
degeneracy that the rigid long-wavelength model cannot break.

Every quantity here reduces the sphere to a single point mass at its centroid
when it enters :func:`gwtb.bodies.multipole.quadrupole_moment` — that is
exactly why its self-quadrupole (T-4.2) vanishes and why radius and density
matter only through their product with volume (claim B-2 in
``docs/CLAIMS.md``). Breaking that degeneracy requires elastic deformation
(T-4.3), finite-size retardation (T-4.5), or rotational oblateness (below).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from gwtb.core.constants import G


@dataclass(frozen=True)
class Sphere:
    """A rigid, uniform-density sphere.

    Source: Fitzpatrick, Newtonian Dynamics, eq. 1361
        (farside.ph.utexas.edu/teaching/301/lectures/node103.html)

    Parameters
    ----------
    radius
        Sphere radius, m. Must be strictly positive.
    density
        Uniform mass density, kg m^-3. Must be strictly positive.
    """

    radius: float
    density: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.radius) or self.radius <= 0.0:
            raise ValueError(f"radius must be positive and finite, got {self.radius!r}")
        if not math.isfinite(self.density) or self.density <= 0.0:
            raise ValueError(f"density must be positive and finite, got {self.density!r}")

    @property
    def mass(self) -> float:
        """Total mass, kg: ``M = (4/3) pi R^3 rho``.

        Source: Fitzpatrick, Newtonian Dynamics, eq. 1361
        (farside.ph.utexas.edu/teaching/301/lectures/node103.html)
        """
        return (4.0 / 3.0) * math.pi * self.radius**3 * self.density

    @property
    def moment_of_inertia(self) -> float:
        """Moment of inertia about any diameter, kg m^2: ``I = (2/5) M R^2``.

        Source: Fitzpatrick, Newtonian Dynamics, eq. 1361
        (farside.ph.utexas.edu/teaching/301/lectures/node103.html)
        """
        return (2.0 / 5.0) * self.mass * self.radius**2

    def self_quadrupole(self) -> NDArray[np.float64]:
        """Trace-free quadrupole moment of the sphere about its own centroid.

        In the rigid point-mass representation used throughout ``gwtb``
        (:func:`gwtb.bodies.multipole.quadrupole_moment`), a body enters the
        radiation calculation as a single point mass at its centroid. Applying
        that definition to one body at its own origin, ``Q_ij = m(x_i x_j -
        (1/3) delta_ij |x|^2)`` with ``x = 0``, gives exactly zero — the sphere
        contributes no *internal* quadrupole; only its trajectory does.

        Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 3 (evaluated for
        a single body at its own centroid)

        Returns
        -------
        ndarray
            Shape ``(3, 3)``, exact zeros (kg m^2).
        """
        return np.zeros((3, 3), dtype=np.float64)

    def degeneracy_warning(self) -> str:
        """Explain why radius and density do not appear independently here.

        In the rigid, long-wavelength model, a sphere's radiative signature
        depends on its trajectory and total mass ``M`` only —
        :meth:`self_quadrupole` is identically zero regardless of ``(R, rho)``,
        so two spheres with equal mass but different radius and density are
        radiatively indistinguishable. Breaking the degeneracy requires
        elastic deformation, finite-size retardation, or rotational
        oblateness.

        Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 3 (corollary:
        internal structure enters only through M for a point-mass source)

        Returns
        -------
        str
            Human-readable explanation, referencing claim B-2 in
            ``docs/CLAIMS.md``.
        """
        return (
            "In the rigid long-wavelength model (claim B-2, docs/CLAIMS.md), "
            "a sphere's self-quadrupole is identically zero for any (radius, "
            "density) pair with a given mass M: radiation depends on the "
            "trajectory and M alone. Two spheres with equal M but different "
            "(R, rho) are therefore radiatively identical here. Breaking this "
            "degeneracy requires elastic deformation (T-4.3), finite-size "
            "retardation (T-4.5), or rotational oblateness (oblateness_quadrupole)."
        )


def oblateness_quadrupole(sphere: Sphere, spin_rate: float) -> NDArray[np.float64]:
    """Static quadrupole moment from slow rotational flattening.

    A uniform, self-gravitating fluid sphere spinning at angular rate
    ``Omega`` about the z-axis settles into a Maclaurin spheroid. In the
    slow-rotation (small ``m = Omega^2 R^3 / (G M)``) limit, the equatorial
    flattening is

    .. code-block:: text

        epsilon = (5/4) m,   m = Omega^2 R^3 / (G M)

    Source: Fitzpatrick, Theoretical Fluid Mechanics, eq. 2.130
    (farside.ph.utexas.edu/teaching/336L/Fluidhtml/node35.html)

    Converting that flattening to the trace-free quadrupole moment
    ``Q_ij`` used throughout ``gwtb`` is this project's own derivation, not
    Fitzpatrick's: for an oblate spheroid of equatorial radius ``a`` and
    polar radius ``c = a(1 - epsilon)``, the moment-of-inertia tensor has
    ``I_zz = (2/5) M a^2`` and ``I_xx = I_yy = (1/5) M (a^2 + c^2)``
    (uniform-ellipsoid moment of inertia, same source class as
    :attr:`Sphere.moment_of_inertia`), and ``Q_ij = -(I_ij - (1/3) delta_ij
    tr I)`` (ADR-0002 §6 trace-free convention). To leading order in
    ``epsilon``, ``a^2 - c^2 ~= 2 a^2 epsilon``, giving

    .. code-block:: text

        Q_zz = -(2/15) M (a^2 - c^2) ~= -(1/3) Omega^2 R^5 / G   (Q_xx = Q_yy = -Q_zz/2)

    independent of mass — the centrifugal and self-gravity mass dependence
    cancel, leaving only ``Omega``, ``R``, and ``G``.

    Parameters
    ----------
    sphere
        The undeformed rigid sphere, giving ``R`` and (via :attr:`Sphere.mass`)
        the equilibrium self-gravity scale.
    spin_rate
        Angular spin rate ``Omega``, rad/s.

    Returns
    -------
    ndarray
        Shape ``(3, 3)``, kg m^2. Diagonal, traceless: ``diag(-Q_zz/2, -Q_zz/2,
        Q_zz)`` with ``Q_zz`` as above. Zero at zero spin; scales as
        ``spin_rate**2``.
    """
    if not math.isfinite(spin_rate):
        raise ValueError(f"spin_rate must be finite, got {spin_rate!r}")

    q_zz = -(spin_rate**2 * sphere.radius**5) / (3.0 * G)
    q = np.zeros((3, 3), dtype=np.float64)
    q[0, 0] = -q_zz / 2.0
    q[1, 1] = -q_zz / 2.0
    q[2, 2] = q_zz
    return q


__all__ = ["Sphere", "oblateness_quadrupole"]
