"""Spin-2 polarization basis and quadrupole element patterns.

A gravitational wave has exactly two degrees of freedom. This module supplies the
basis they live in, and the angular patterns of the two canonical radiating
elements.

**Everything here is spin-2 and behaves unlike its electromagnetic analogue.**
The two facts that matter, both asserted in the tests rather than assumed:

* Rotating the polarization frame by ``psi`` about the line of sight transforms
  the amplitudes by ``e^(2i psi)``, not ``e^(i psi)``. The basis therefore has
  period ``pi``, not ``2 pi``, and ``h_plus`` and ``h_cross`` are **45 degrees**
  apart rather than 90.
* The linear element pattern is **zero on-axis and maximal broadside** — the
  opposite of a dipole antenna. Anyone porting radar intuition will get this
  backwards, and the result will look plausible.

See [ADR-0003](../../../docs/adr/0003-spin2-superposition.md) for the
consequences for array synthesis.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.validation import as_unit_vector

_POLE_TOL = 1e-12


def _transverse_frame(
    n: NDArray[np.float64], psi: float
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Orthonormal pair spanning the plane transverse to ``n``, rotated by ``psi``.

    Uses the spherical convention ``(e_theta, e_phi)``: for
    ``n = (sinθcosφ, sinθsinφ, cosθ)``,

    .. code-block:: text

        e_theta = ( cosθcosφ,  cosθsinφ, -sinθ )
        e_phi   = (    -sinφ,      cosφ,      0 )

    At the poles ``φ`` is degenerate; we fix ``φ = 0`` there so the frame stays
    deterministic. **The frame choice is a convention**, and an unstated one is
    exactly what made T-1.9's sign reproducible only by accident — so it is
    pinned here and asserted in the tests.
    """
    sin_theta = float(np.hypot(n[0], n[1]))
    if sin_theta < _POLE_TOL:  # on the pole: phi is degenerate, choose phi = 0
        cos_phi, sin_phi = 1.0, 0.0
        cos_theta = float(np.sign(n[2])) or 1.0
        e_theta = np.array([cos_theta, 0.0, 0.0])
        e_phi = np.array([0.0, 1.0, 0.0])
    else:
        cos_phi, sin_phi = n[0] / sin_theta, n[1] / sin_theta
        cos_theta = float(n[2])
        e_theta = np.array([cos_theta * cos_phi, cos_theta * sin_phi, -sin_theta])
        e_phi = np.array([-sin_phi, cos_phi, 0.0])

    if psi:
        c, s = np.cos(psi), np.sin(psi)
        e_theta, e_phi = c * e_theta + s * e_phi, -s * e_theta + c * e_phi
    return e_theta, e_phi


def polarization_basis(
    n_hat: ArrayLike, psi: float = 0.0
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Unit polarization tensors ``(e_plus, e_cross)`` for propagation along ``n_hat``.

    With ``(u, v)`` an orthonormal pair transverse to ``n_hat``:

    .. code-block:: text

        e_plus  = u⊗u - v⊗v
        e_cross = u⊗v + v⊗u

    so that any TT strain decomposes as
    ``h_ij = h_plus e_plus + h_cross e_cross``, matching the component
    definition ``h^TT_xx = -h^TT_yy = h_plus``, ``h^TT_xy = h^TT_yx = h_cross``
    for a wave along z.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 2.22

    Parameters
    ----------
    n_hat
        Shape ``(3,)`` unit vector, the propagation direction.
    psi
        Rotation of the transverse frame about ``n_hat``, radians. **Amplitudes
        transform by ``e^(2i psi)``**, so the basis is periodic in ``psi`` with
        period ``pi``. Defaults to the canonical spherical frame.

    Returns
    -------
    tuple of ndarray
        ``(e_plus, e_cross)``, each shape ``(3, 3)``, dimensionless. Both are
        symmetric, traceless, and transverse to ``n_hat``, and they are
        orthonormal under the double contraction ``e_A : e_B = 2 δ_AB``.
    """
    n = as_unit_vector(n_hat)
    u, v = _transverse_frame(n, float(psi))
    return np.outer(u, u) - np.outer(v, v), np.outer(u, v) + np.outer(v, u)


def element_pattern_rotating(theta: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Angular pattern of a **rotating** mass quadrupole (two masses in a circular orbit).

    .. code-block:: text

        h_plus  ∝ (1 + cos²θ) / 2
        h_cross ∝ cos θ

    where ``θ`` is measured from the rotation axis. Face-on (``θ = 0``) gives
    equal-amplitude circular polarization; edge-on (``θ = π/2``) gives linear
    polarization with ``h_cross`` vanishing.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 2 (quadrupole
    waveform) applied to the circular-orbit quadrupole of eq. 3

    Claim category **B** (derived) in ``docs/CLAIMS.md``. Verified against the
    already-validated `quadrupole_second_derivative` + `apply_tt` path: both
    components reproduce these closed forms, with residuals falling as ``1/N²``
    in the orbital-phase sampling, confirming exactness rather than coincidence.

    Parameters
    ----------
    theta
        Polar angle from the rotation axis, radians. Scalar or array.

    Returns
    -------
    tuple of ndarray
        ``(h_plus, h_cross)`` pattern factors, normalised to 1 on-axis,
        dimensionless.
    """
    th = np.asarray(theta, dtype=np.float64)
    cos_theta = np.cos(th)
    return (1.0 + cos_theta**2) / 2.0, cos_theta


def element_pattern_linear(theta: ArrayLike) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Angular pattern of a **linear** mass quadrupole (oscillation along one axis).

    .. code-block:: text

        h_plus  ∝ sin²θ
        h_cross = 0

    where ``θ`` is measured from the oscillation axis.

    ⚠️ **This is zero on-axis and maximal broadside — the opposite of a dipole
    antenna pattern.** A linear oscillator radiates nothing along its own axis of
    motion. Substituting spin-1 intuition here inverts the pattern and yields a
    beam pointed exactly where the source is silent.

    ``h_cross`` vanishes identically: a linear oscillator has no handedness, so
    it excites only the polarization aligned with its own axis.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 2 (quadrupole
    waveform) applied to a single-axis quadrupole of eq. 3

    Claim category **B** (derived) in ``docs/CLAIMS.md``, verified numerically
    against `quadrupole_second_derivative` + `apply_tt` to 1e-9.

    Parameters
    ----------
    theta
        Polar angle from the oscillation axis, radians. Scalar or array.

    Returns
    -------
    tuple of ndarray
        ``(h_plus, h_cross)`` pattern factors, dimensionless. ``h_cross`` is
        identically zero.
    """
    th = np.asarray(theta, dtype=np.float64)
    return np.sin(th) ** 2, np.zeros_like(th)


__all__ = [
    "element_pattern_linear",
    "element_pattern_rotating",
    "polarization_basis",
]
