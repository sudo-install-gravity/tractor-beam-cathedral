"""Mass multipole moments of a system of point masses, and their time derivatives.

The trace-free quadrupole moment is the first non-vanishing radiative multipole
(monopole is conserved mass; dipole is the centre of mass, whose second
derivative is the net external force and therefore zero for an isolated system —
see ``docs/PHYSICS.md`` §2). Everything downstream in ``gwtb`` is built on the
functions here.

**Derivatives are analytic, never finite-differenced.** The luminosity needs the
*third* derivative of ``Q_ij``, and central differences at that order are
roundoff-dominated as ``eps/h^3``: measured relative error is ``1.1e-1`` at step
``1e-5`` and ``1.1e+2`` at ``1e-6``, against ``8.0e-7`` at the optimal ``1e-3``.
A caller who differentiates numerically will get numbers that look plausible and
are wrong by orders of magnitude. See ``docs/PHYSICS.md`` §2.1 for the measured
error curve.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.bodies.sphere import Sphere
from gwtb.core.validation import as_body_array, as_masses

_IDENTITY = np.eye(3, dtype=np.float64)

#: Coefficient of ``-(kR)^2`` in the l=2 uniform-ball form factor, ADR-0007 eq. 3.
#: ``(l+3) / [2(2l+3)(l+5)]`` at ``l=2`` is ``5 / (2*7*7) = 5/98``.
_QUADRUPOLE_FORM_FACTOR_COEFF = 5.0 / 98.0

#: R/wavelength above which the long-wavelength assumption (docs/INDEX.md §3,
#: "Long wavelength (R << lambda)") is considered violated for T-4.7's purposes.
#: At this ratio the departure from unity is already 2.0142% (ADR-0007
#: "Recomputed acceptance criterion"); the series is meaningless past R/lambda
#: = 0.7046, where it goes negative (ADR-0007, validity floor).
_LONG_WAVELENGTH_ASSUMPTION_LIMIT = 0.1


class LongWavelengthAssumptionWarning(UserWarning):
    """Raised when a caller uses ``finite_size_correction`` outside its regime.

    Source: docs/adr/0007-uniform-sphere-quadrupole-form-factor.md, eq. n/a — a
    governance class, not a physics result; introduces no equation of its own.

    Names the specific assumption violated, per ``docs/INDEX.md`` §3's "Long
    wavelength (R << lambda)" row, so a caller can find the row and its
    consequences without guessing which of several assumptions tripped.
    """


def quadrupole_moment(masses: ArrayLike, positions: ArrayLike) -> NDArray[np.float64]:
    """Trace-free mass quadrupole moment ``Q_ij`` of a system of point masses.

    For a point-mass distribution ``rho(x, t) = sum_A m_A delta^3(x - x_A(t))``,
    the source integral reduces to

    .. code-block:: text

        Q_ij = sum_A m_A ( x_i x_j - (1/3) delta_ij |x|^2 )

    Note this is the **trace-free** moment throughout ``gwtb`` (ADR-0002 §6),
    not the second moment ``I_ij = sum_A m_A x_i x_j``.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 3

    Parameters
    ----------
    masses
        Shape ``(N,)``, kg.
    positions
        Shape ``(N, 3)``, m, in whatever frame the caller intends. For a
        radiating system this is normally the barycentric frame.

    Returns
    -------
    ndarray
        Shape ``(3, 3)``, kg m^2. Symmetric and traceless by construction.
    """
    m = as_masses(masses)
    x = as_body_array(positions, "positions", n_bodies=m.size)

    second_moment = np.einsum("a,ai,aj->ij", m, x, x)
    trace = np.einsum("a,ai,ai->", m, x, x)
    # einsum's numpy stub returns Any; annotate so mypy narrows the result back
    # to NDArray[np.float64] rather than silently widening the return type.
    result: NDArray[np.float64] = second_moment - _IDENTITY * (trace / 3.0)
    return result


def quadrupole_second_derivative(
    masses: ArrayLike,
    positions: ArrayLike,
    velocities: ArrayLike,
    accelerations: ArrayLike,
) -> NDArray[np.float64]:
    """Analytic second time derivative ``d2Q_ij/dt2``.

    Differentiating the point-mass form of the quadrupole moment twice:

    .. code-block:: text

        Qdd_ij = sum_A m_A ( a_i x_j + 2 v_i v_j + x_i a_j )
                 - (2/3) delta_ij sum_A m_A ( v.v + x.a )

    This is the quantity the quadrupole formula needs; see
    :func:`gwtb.source.quadrupole.strain_tt`.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 3 (differentiated)

    Claim category **B** (derived) in ``docs/CLAIMS.md``; validated against a
    circular binary in ``tests/benchmarks/test_binary.py``.

    Parameters
    ----------
    masses
        Shape ``(N,)``, kg.
    positions, velocities, accelerations
        Shape ``(N, 3)``, in m, m/s, m/s^2.

    Returns
    -------
    ndarray
        Shape ``(3, 3)``, kg m^2 s^-2. Symmetric and traceless.
    """
    m = as_masses(masses)
    n = m.size
    x = as_body_array(positions, "positions", n_bodies=n)
    v = as_body_array(velocities, "velocities", n_bodies=n)
    a = as_body_array(accelerations, "accelerations", n_bodies=n)

    term = (
        np.einsum("a,ai,aj->ij", m, a, x)
        + 2.0 * np.einsum("a,ai,aj->ij", m, v, v)
        + np.einsum("a,ai,aj->ij", m, x, a)
    )
    trace = np.einsum("a,ai,ai->", m, v, v) + np.einsum("a,ai,ai->", m, x, a)
    # einsum's numpy stub returns Any; annotate so mypy narrows the result back
    # to NDArray[np.float64] rather than silently widening the return type.
    result: NDArray[np.float64] = term - _IDENTITY * (2.0 / 3.0) * trace
    return result


def quadrupole_third_derivative(
    masses: ArrayLike,
    positions: ArrayLike,
    velocities: ArrayLike,
    accelerations: ArrayLike,
    jerks: ArrayLike,
) -> NDArray[np.float64]:
    """Analytic third time derivative ``d3Q_ij/dt3``.

    .. code-block:: text

        Qddd_ij = sum_A m_A ( j_i x_j + 3 a_i v_j + 3 v_i a_j + x_i j_j )
                  - (2/3) delta_ij sum_A m_A ( 3 v.a + x.j )

    Required by :func:`gwtb.source.quadrupole.luminosity`. **Do not compute this
    by differencing** :func:`quadrupole_second_derivative` — see the module
    docstring for the measured error curve.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 3 (differentiated)

    Claim category **B** (derived) in ``docs/CLAIMS.md``. Validated indirectly
    but far more stringently than by finite differences: the luminosity built
    from this quantity reproduces the closed form
    ``L = (32/5)(G/c^5) mu^2 a^4 omega^6`` to 4.1e-16, an exact algebraic
    identity.

    Parameters
    ----------
    masses
        Shape ``(N,)``, kg.
    positions, velocities, accelerations, jerks
        Shape ``(N, 3)``, in m, m/s, m/s^2, m/s^3.

    Returns
    -------
    ndarray
        Shape ``(3, 3)``, kg m^2 s^-3. Symmetric and traceless.
    """
    m = as_masses(masses)
    n = m.size
    x = as_body_array(positions, "positions", n_bodies=n)
    v = as_body_array(velocities, "velocities", n_bodies=n)
    a = as_body_array(accelerations, "accelerations", n_bodies=n)
    j = as_body_array(jerks, "jerks", n_bodies=n)

    term = (
        np.einsum("a,ai,aj->ij", m, j, x)
        + 3.0 * np.einsum("a,ai,aj->ij", m, a, v)
        + 3.0 * np.einsum("a,ai,aj->ij", m, v, a)
        + np.einsum("a,ai,aj->ij", m, x, j)
    )
    trace = 3.0 * np.einsum("a,ai,ai->", m, v, a) + np.einsum("a,ai,ai->", m, x, j)
    # einsum's numpy stub returns Any; annotate so mypy narrows the result back
    # to NDArray[np.float64] rather than silently widening the return type.
    result: NDArray[np.float64] = term - _IDENTITY * (2.0 / 3.0) * trace
    return result


def octupole_moment(masses: ArrayLike, positions: ArrayLike) -> NDArray[np.float64]:
    """Trace-free mass octupole moment ``Q_ijk`` of a system of point masses.

    The ``l=3`` symmetric trace-free (STF) mass multipole. For a point-mass
    distribution, the STF projection of ``sum_A m_A x_i x_j x_k`` is

    .. code-block:: text

        Q_ijk = sum_A m_A [ x_i x_j x_k
                            - (r_A^2 / 5) (delta_ij x_k + delta_jk x_i + delta_ki x_j) ]

    where ``r_A^2 = x_A . x_A``. This is fully symmetric under permutation of
    any two indices and traceless on every index pair (``ij``, ``jk``,
    ``ki``) by construction, mirroring the quadrupole's trace-free property
    (ADR-0002 §6) one multipole order up.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 123a, Newtonian point-mass limit

    .. note::
       **Citation scope, verified 2026-08-03 by reading the source.** Eq. (123a)
       is Theorem 6: the general STF source multipole ``I_L(u)`` of a
       *post-Newtonian* source, a finite-part-regularized integral carrying
       ``1/c^2`` and ``1/c^4`` correction terms. It states considerably more
       than this function implements, which is its **Newtonian, point-mass
       limit**. The citation is therefore scoped, and the row is DERIVED rather
       than VERIFIED -- the framework is cited, the specialization is ours.
       This is the same treatment EQ-034 gets, where DLMF supplies the input
       series and the uniform-ball specialization stays ours.

    Blanchet's Theorem 6 (eq. 123a) gives the general STF source multipole
    ``I_L`` for all ``l >= 2``; eq. (126) states explicitly that this reduces
    to the Newtonian quadrupole (eq. 3) at leading PN order, and the same
    Newtonian-order reduction applies term-by-term at ``l=3``. Cross-checked
    against Blanchet's explicit two-body Newtonian octupole (eq. 302a),
    ``I_ijk = -nu m Delta x_<ijk>``: substituting ``y_1 = (m2/m) x``,
    ``y_2 = -(m1/m) x`` into the point-mass sum above reproduces that form
    identically.

    Parameters
    ----------
    masses
        Shape ``(N,)``, kg.
    positions
        Shape ``(N, 3)``, m.

    Returns
    -------
    ndarray
        Shape ``(3, 3, 3)``, kg m^3. Fully symmetric; traceless on every
        index pair.
    """
    m = as_masses(masses)
    x = as_body_array(positions, "positions", n_bodies=m.size)

    r2 = np.einsum("ai,ai->a", x, x)
    triple = np.einsum("a,ai,aj,ak->ijk", m, x, x, x)
    s = np.einsum("a,ak->k", m * r2, x)

    correction = (
        np.einsum("ij,k->ijk", _IDENTITY, s)
        + np.einsum("jk,i->ijk", _IDENTITY, s)
        + np.einsum("ki,j->ijk", _IDENTITY, s)
    )
    # einsum's numpy stub returns Any; annotate so mypy narrows the result back
    # to NDArray[np.float64] rather than silently widening the return type.
    result: NDArray[np.float64] = triple - correction / 5.0
    return result


def finite_size_correction(sphere: Sphere, wavelength: float) -> float:
    """Leading finite-size (retardation) correction to the mass-quadrupole radiation.

    A body whose radius is not negligible against the wavelength radiates less
    than the point-mass idealization: the far side of the body is retarded
    relative to the near side, and the contributions partially dephase. The
    exact radiative source multipole replaces the long-wavelength radial weight
    ``r^l`` with the ``j_l(kr)`` factor of the outgoing Green's-function
    partial-wave expansion, and for an ``l``-pole whose radial profile is
    **uniform on [0, R]** the ratio to the point-mass result is

    .. code-block:: text

        F_l(kR) = 1 - (kR)^2 (l+3) / [2 (2l+3) (l+5)] + O((kR)^4)

    At ``l = 2`` (the mass quadrupole), ``2(2l+3)(l+5) = 2*7*7 = 98``, so

    .. code-block:: text

        F_2(kR) = 1 - 5 (kR)^2 / 98,    k = 2 pi / wavelength

    Source: docs/adr/0007-uniform-sphere-quadrupole-form-factor.md, eq. 3

    Claim category **B** (this project's own derivation) in ``docs/CLAIMS.md``.
    **No external numbered equation for this result was found** — see the ADR's
    "Citation status". It is instead verified numerically by three independent
    routes (exact rational series; a far-field retarded phase integral to
    1.7e-12; the exact retarded Green's function to 1.4e-8), none of which
    evaluates a spherical Bessel function.

    .. warning::

       **Two plausible-looking form factors are the wrong multipole order** and
       must never be substituted here (ADR-0007 "Context"):

       - ``sin(kR)/(kR)``, leading term ``1 - (kR)^2/6``, is ``l = 0`` and is
         **spin-1 antenna machinery** — the trap ``CLAUDE.md`` rule 4 exists to
         catch.
       - ``3 j_1(kR)/(kR)``, leading term ``1 - (kR)^2/10``, is the *total-mass
         monopole*, not the quadrupole.

       Both → 1 as ``R/lambda`` → 0 and both look reasonable. Only the
       coefficient distinguishes them. ``tests/unit/test_multipole.py`` guards
       against each by name.

    .. warning::

       This is the **volume-filling** profile. A body that gets its quadrupole
       by deforming its *surface* — an incompressible tidal or rotational
       deformation, i.e. :func:`gwtb.bodies.elastic.induced_quadrupole` and
       :func:`gwtb.bodies.sphere.oblateness_quadrupole` — has
       ``1 - (kR)^2/14`` instead, 40% larger (ADR-0007 eq. 5). Do not apply
       this function to those without re-deriving.

    Parameters
    ----------
    sphere
        The radiating body; only :attr:`Sphere.radius` enters.
    wavelength
        Gravitational-wave wavelength, m. Must be strictly positive and finite.

    Returns
    -------
    float
        Multiplicative correction ``F_2``, dimensionless. Exactly 1 in the
        point-mass limit and decreasing with ``R/wavelength``.

    Notes
    -----
    This is a **leading-order** correction. It reaches 0.98 at
    ``R/wavelength = 0.1`` (a 2.0142% departure) and passes through zero at
    ``R/wavelength = 0.7046``; it is meaningless well before that.

    Warns with :class:`LongWavelengthAssumptionWarning` (T-4.7) when
    ``R/wavelength >= 0.1`` — the "Long wavelength (R << lambda)" row of
    ``docs/INDEX.md`` §3 — since the correction itself cannot detect how far
    past that point it has been pushed; only the caller's choice of ``R`` and
    ``wavelength`` can.
    """
    if not math.isfinite(wavelength) or wavelength <= 0.0:
        raise ValueError(f"wavelength must be positive and finite, got {wavelength!r}")

    r_over_lambda = sphere.radius / wavelength
    if r_over_lambda >= _LONG_WAVELENGTH_ASSUMPTION_LIMIT:
        warnings.warn(
            "finite_size_correction: R/wavelength = "
            f"{r_over_lambda:.6g} >= {_LONG_WAVELENGTH_ASSUMPTION_LIMIT} violates the "
            "'Long wavelength (R << lambda)' assumption (docs/INDEX.md §3, Assumption "
            "Ledger). The leading-order form factor departs from unity by "
            f"{100.0 * _QUADRUPOLE_FORM_FACTOR_COEFF * (2.0 * math.pi * r_over_lambda) ** 2:.4g}% "
            "here and is not valid past R/wavelength = 0.7046 (ADR-0007).",
            LongWavelengthAssumptionWarning,
            stacklevel=2,
        )

    k_r = 2.0 * math.pi * r_over_lambda
    return 1.0 - _QUADRUPOLE_FORM_FACTOR_COEFF * k_r * k_r


__all__ = [
    "LongWavelengthAssumptionWarning",
    "finite_size_correction",
    "octupole_moment",
    "quadrupole_moment",
    "quadrupole_second_derivative",
    "quadrupole_third_derivative",
]
