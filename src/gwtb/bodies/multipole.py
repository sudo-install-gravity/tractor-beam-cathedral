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

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.validation import as_body_array, as_masses

_IDENTITY = np.eye(3, dtype=np.float64)


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

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 123a

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


__all__ = [
    "octupole_moment",
    "quadrupole_moment",
    "quadrupole_second_derivative",
    "quadrupole_third_derivative",
]
