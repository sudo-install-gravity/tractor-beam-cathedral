"""Mass dipole moment and its second time derivative, and the flagged
"dipole strain" diagnostic.

The mass dipole is the system's center of mass. Its second derivative equals
``dP/dt``, the net external force — for an isolated, momentum-conserving
system this vanishes identically, which is why the leading radiative
multipole is the quadrupole rather than the dipole (Blanchet, Living Rev.
Relativ. 17:2 (2014), eq. 3; see ``docs/PHYSICS.md`` §2).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.constants import G_OVER_C4
from gwtb.core.validation import as_body_array, as_float64, as_masses, as_unit_vector
from gwtb.propagate.tt_projection import apply_tt
from gwtb.source.conservation import StampedResult


def dipole_moment(masses: ArrayLike, positions: ArrayLike) -> NDArray[np.float64]:
    """Mass dipole moment ``d_i`` of a system of point masses.

    .. code-block:: text

        d_i = sum_A m_A x_A,i

    For a point-mass distribution ``rho = sum_A m_A delta^3(x - x_A)``, this
    is the ``l=1`` term of the mass multipole expansion — the system's
    center-of-mass position weighted by total mass, ``M * x_cm``.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.30

    Flanagan & Hughes define ``M_1 = integral rho(x) x_i d^3x`` (their eq.
    4.30, ``rho`` being ``T^tt``); substituting the point-mass density gives
    the sum above directly.

    Parameters
    ----------
    masses
        Shape ``(N,)``, kg.
    positions
        Shape ``(N, 3)``, m.

    Returns
    -------
    ndarray
        Shape ``(3,)``, kg m.
    """
    m = as_masses(masses)
    x = as_body_array(positions, "positions", n_bodies=m.size)
    result: NDArray[np.float64] = np.einsum("a,ai->i", m, x)
    return result


def dipole_second_derivative(masses: ArrayLike, accelerations: ArrayLike) -> NDArray[np.float64]:
    """Analytic second time derivative ``d2(d_i)/dt2`` of the mass dipole.

    .. code-block:: text

        d_i_ddot = sum_A m_A a_A,i = dP_i/dt

    Equal to the system's total momentum derivative, i.e. the net external
    force. For an isolated (momentum-conserving) system this is exactly zero
    — that vanishing is *the* reason mass-dipole gravitational radiation does
    not occur, not an incidental fact (``docs/PHYSICS.md`` §2). Do not "fix"
    a nonzero result for a momentum-conserving configuration; a nonzero value
    correctly signals an unbalanced external force, which is what
    :func:`gwtb.source.conservation.audit` exists to flag.

    **Analytic. Never finite-difference** — this is one time-derivative of
    Flanagan & Hughes eq. (4.35), ``dM_1/dt = P``, applied again; no numerical
    differentiation is needed or permitted since the accelerations are already
    given.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.35, differentiated once

    Citation verified 2026-08-03 by reading the source: their eq. (4.35) is
    ``dM_1/dt = d/dt integral rho x_i d^3x = integral rho v_i d^3x = P_i`` --
    the **first** derivative, equal to total momentum. This function returns
    the **second**, so the citation is that equation differentiated once, and
    the row is DERIVED rather than VERIFIED. Same treatment as EQ-002/EQ-003,
    which cite Blanchet eq. 3 differentiated.

    Parameters
    ----------
    masses
        Shape ``(N,)``, kg.
    accelerations
        Shape ``(N, 3)``, m/s^2.

    Returns
    -------
    ndarray
        Shape ``(3,)``, kg m s^-2 (N). Zero to numerical roundoff for a
        momentum-conserving configuration.
    """
    m = as_masses(masses)
    a = as_body_array(accelerations, "accelerations", n_bodies=m.size)
    result: NDArray[np.float64] = np.einsum("a,ai->i", m, a)
    return result


def dipole_strain(
    d_ddot: ArrayLike, r: float, n_hat: ArrayLike, allow_trivial: bool = False
) -> StampedResult:
    """Diagnostic "strain" from an uncancelled mass dipole — always UNPHYSICAL.

    **There is no established formula here, because there is no such thing as
    physical mass-dipole gravitational radiation** (A-2, ``docs/CLAIMS.md``):
    a nonzero, time-varying mass dipole in an isolated system is a coordinate
    artifact removable by choosing the center-of-mass frame, and the standard
    multipole-radiation derivation assumes an isolated (momentum-conserving)
    system throughout. A system where ``d_ddot`` is genuinely nonzero has
    already violated that premise, so no citable formula applies to it. This
    function's construction is **this project's own diagnostic, not an
    external citation** — the same category as the maneuvering-body
    modeling decision in ADR-0004.

    **Construction.** ``(G/c^4) d_ddot`` is dimensionless per component (in SI,
    ``G/c^4`` carries units of inverse force — ``c^4/G`` is the well-known
    "maximum force" scale of GR). Call this dimensionless vector ``e_i``. The
    diagnostic tensor is its own trace-free outer square, TT-projected exactly
    as a physical quadrupole strain would be:

    .. code-block:: text

        e_i          = (G / c^4) * d_ddot_i
        D_ij         = e_i e_j - (1/3) delta_ij |e|^2
        h_ij         = Lambda_ij,kl(n_hat) * D_kl

    A first attempt at this function symmetrized ``d_ddot`` directly against
    ``n_hat`` (``n_hat_i d_ddot_j + n_hat_j d_ddot_i``). That construction is
    **identically zero for every input**: the transverse projector satisfies
    ``P @ n_hat = 0`` exactly, and any tensor built by pairing a vector with
    ``n_hat`` itself is annihilated by projection along that same ``n_hat``,
    regardless of the other vector. The self-outer-square above has no such
    degeneracy, and correctly reduces to zero **only** when ``d_ddot`` is
    exactly parallel to ``n_hat`` — the expected on-axis null of a
    quadrupole-like pattern (see :func:`gwtb.propagate.polarization.
    element_pattern_linear`), not an unconditional identity.

    **This construction does not depend on ``r``.** ``r`` is validated as a
    sane physical distance for API consistency with every other strain-like
    function in this codebase, but the diagnostic itself does not fall off
    with distance — unlike genuine radiation, which always does. That
    r-independence is itself evidence this is not a physical radiated field,
    and is precisely why the result must remain permanently stamped rather
    than ever being read as one.

    Source: this project's own construction, eq. n/a (see above; no
    established GW-memory or multipole-radiation reference applies to a
    momentum-non-conserving source)

    Parameters
    ----------
    d_ddot
        Shape ``(3,)``, N (``kg m/s^2``). The dipole's second time derivative,
        i.e. the system's net external force — see
        :func:`dipole_second_derivative`.
    r
        Observer distance, m. Must be positive and finite.
    n_hat
        Shape ``(3,)`` unit vector from source to observer.
    allow_trivial
        If ``False`` (default), raises when ``d_ddot`` is exactly zero — a
        momentum-conserving source has no dipole term to diagnose, and
        calling this function on one is almost always a mistake upstream
        (the caller likely meant :func:`gwtb.source.quadrupole.strain_tt`).
        Set ``True`` to permit it anyway, e.g. for a regression test
        asserting the zero case.

    Returns
    -------
    StampedResult
        Wraps a shape ``(3, 3)`` tensor, dimensionless, symmetric, traceless
        and transverse to ``n_hat``. **Always stamped** ``UNPHYSICAL`` (see
        :data:`gwtb.source.conservation.UNPHYSICAL_STAMP`) regardless of
        ``d_ddot``'s value — even the trivial zero case, since the function
        was invoked on the non-radiating dipole channel at all.
    """
    d = as_float64(d_ddot, "d_ddot")
    if d.shape != (3,):
        raise ValueError(f"d_ddot must have shape (3,), got {d.shape}")
    n = as_unit_vector(n_hat, "n_hat")
    if not np.isscalar(r) and np.asarray(r).ndim != 0:
        raise TypeError("r must be a scalar distance in metres")
    r_val = float(r)
    if not np.isfinite(r_val):
        raise ValueError(f"r must be finite, got {r!r}")
    if r_val <= 0.0:
        raise ValueError(f"r must be positive, got {r_val!r}")

    if np.all(d == 0.0) and not allow_trivial:
        raise ValueError(
            "d_ddot is exactly zero: the source conserves momentum and has no "
            "dipole term to diagnose. Pass allow_trivial=True to compute the "
            "(zero) result anyway, or use gwtb.source.quadrupole.strain_tt for "
            "the physical quadrupole channel."
        )

    e = G_OVER_C4 * d
    tensor = np.outer(e, e) - np.eye(3) * (float(e @ e) / 3.0)
    h = apply_tt(tensor, n)

    return StampedResult.unphysical(
        h,
        reason=(
            "mass-dipole diagnostic (source/multipole_rad.py:dipole_strain); "
            "nonzero only when the source does not conserve momentum "
            "(CLAUDE.md rule 2)"
        ),
    )


__all__ = ["dipole_moment", "dipole_second_derivative", "dipole_strain"]
