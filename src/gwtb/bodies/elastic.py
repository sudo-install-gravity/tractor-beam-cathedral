"""Elastic deformation of a body under an applied tidal field.

This module is where the rigid model's mass/radius/density degeneracy finally
breaks. In the rigid long-wavelength picture (T-4.2, claim B-2 in
``docs/CLAIMS.md``) a sphere's self-quadrupole is identically zero and radius and
density enter only through the total mass ``M``: two spheres of equal mass but
different ``(R, rho)`` are radiatively indistinguishable. An *elastic* sphere
deforms, and the induced quadrupole depends on ``R^5`` and on the material's
rigidity — so ``R`` and ``rho`` appear independently for the first time.

The response implemented here is the **static** (adiabatic) tidal response: the
body is assumed to reach equilibrium deformation instantaneously compared with
the driving timescale. That assumption fails as the drive approaches the body's
internal oscillation modes, and the assumption ledger in ``docs/INDEX.md``
records it.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.bodies.sphere import Sphere
from gwtb.core.constants import G
from gwtb.core.validation import as_tensor_3x3


def love_number_k2(sphere: Sphere, rigidity: float) -> float:
    """Degree-2 tidal Love number of a homogeneous incompressible elastic sphere.

    .. code-block:: text

        k_2 = k_f / (1 + mu_tilde),    mu_tilde = 19 mu / (2 rho g R)

    with ``k_f = 3/2`` the fluid (zero-rigidity) limit for a homogeneous
    incompressible body, ``mu`` the shear rigidity, and ``g = G M / R^2`` the
    surface gravity. ``mu_tilde`` is the classical "effective rigidity": the
    ratio of material strength to self-gravity. A body held together by gravity
    (``mu_tilde -> 0``) responds as a fluid with ``k_2 -> 3/2``; a body held
    together by material strength (``mu_tilde -> inf``) barely deforms and
    ``k_2 -> 0``.

    Source: Cheng, Lee & Peale, Icarus 233:242 (2014), arXiv:1402.0625, eq. 8
    (``k_2 = k_f / (1 + mu_tilde)``) and eq. 9 (``mu_tilde = 19 mu / (2 rho g
    R)``)

    Those equations trace back to Munk & MacDonald (1960) §5.6 and Peale (1973);
    the open-access arXiv reproduction is cited here because its equation
    numbers can be checked by a stranger, per ``CLAUDE.md``'s citation rule.

    **Applies to monolithic, homogeneous, incompressible bodies.** A
    differentiated, porous or rubble-pile asteroid violates the derivation's
    premises, and this function cannot detect that from its arguments.

    Parameters
    ----------
    sphere
        The undeformed body, supplying ``R``, ``rho`` and hence ``g``.
    rigidity
        Shear modulus ``mu``, Pa. Must be finite and non-negative. Zero gives
        the fluid limit ``k_2 = 3/2`` exactly.

    Returns
    -------
    float
        Dimensionless ``k_2``, in ``(0, 3/2]``.
    """
    if not math.isfinite(rigidity) or rigidity < 0.0:
        raise ValueError(f"rigidity must be finite and non-negative, got {rigidity!r}")

    surface_gravity = G * sphere.mass / sphere.radius**2
    mu_tilde = 19.0 * rigidity / (2.0 * sphere.density * surface_gravity * sphere.radius)
    return 1.5 / (1.0 + mu_tilde)


def induced_quadrupole(
    sphere: Sphere,
    tidal_field: ArrayLike,
    love_k2: float | None = None,
    rigidity: float | None = None,
) -> NDArray[np.float64]:
    """Quadrupole moment induced in an elastic sphere by an applied tidal field.

    .. code-block:: text

        Q_ij = -lambda E_ij,    lambda = (2/3) k_2 R^5 / G

    so that ``Q_ij = -(2/3) (k_2 R^5 / G) E_ij``. The minus sign is the standard
    induced-response convention: the body deforms so as to oppose the applied
    field.

    Source: Hinderer, ApJ 677:1216 (2008), arXiv:0711.2420, eq. 4
    (``Q_ij = -lambda E_ij``) and eq. 5 (``k_2 = (3/2) G lambda R^-5``)

    Hinderer states ``c = G = 1`` generally, but **eq. 5 is printed with ``G``
    explicit**, so the SI form above is unambiguous and no factor has been
    reinserted by hand — the failure mode ADR-0002 §4 exists to prevent.

    Supply exactly one of ``love_k2`` (a measured or assumed Love number) or
    ``rigidity`` (from which ``k_2`` is computed by :func:`love_number_k2`).

    Parameters
    ----------
    sphere
        The undeformed body, supplying ``R`` and — via ``rigidity`` — ``k_2``.
    tidal_field
        Shape ``(3, 3)``, s^-2. The tidal tensor ``E_ij``, conventionally the
        trace-free second spatial derivative of the external potential. Its
        trace is not used: only the trace-free part drives an ``l = 2``
        response, and the returned quadrupole is trace-free regardless.
    love_k2
        Dimensionless degree-2 Love number. Mutually exclusive with
        ``rigidity``.
    rigidity
        Shear modulus ``mu``, Pa. Mutually exclusive with ``love_k2``.

    Returns
    -------
    ndarray
        Shape ``(3, 3)``, kg m^2. Symmetric and trace-free. Scales linearly
        with ``tidal_field``, and tends to zero as ``rigidity -> inf``.
    """
    if (love_k2 is None) == (rigidity is None):
        raise ValueError(
            "supply exactly one of love_k2 or rigidity: love_k2 states the "
            "response directly, rigidity derives it via love_number_k2()"
        )

    if love_k2 is None:
        assert rigidity is not None  # narrowed by the check above
        k2 = love_number_k2(sphere, rigidity)
    else:
        if not math.isfinite(love_k2) or love_k2 < 0.0:
            raise ValueError(f"love_k2 must be finite and non-negative, got {love_k2!r}")
        k2 = love_k2

    field = as_tensor_3x3(tidal_field, "tidal_field")
    # Only the trace-free part drives an l = 2 response; removing the trace here
    # makes the returned moment trace-free for any input, consistent with
    # ADR-0002 §6.
    field_tf = field - np.eye(3) * (np.trace(field) / 3.0)

    lambda_tidal = (2.0 / 3.0) * k2 * sphere.radius**5 / G
    result: NDArray[np.float64] = -lambda_tidal * field_tf
    return result


__all__ = ["induced_quadrupole", "love_number_k2"]
