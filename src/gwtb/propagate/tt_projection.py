"""Transverse-traceless projection.

A gravitational wave has only two physical degrees of freedom. The TT projector
extracts them from a general symmetric tensor by removing the components along
the propagation direction and then removing the remaining trace.

The projector is applied along the **observation direction** ``n_hat`` — the
direction from source to observer — not along any fixed coordinate axis. Using a
fixed axis is a quiet, high-damage error: the result stays symmetric and looks
reasonable while being wrong everywhere off that axis.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.validation import as_tensor_3x3, as_unit_vector

_IDENTITY = np.eye(3, dtype=np.float64)


def transverse_projector(n_hat: ArrayLike) -> NDArray[np.float64]:
    """Transverse projector ``P_ij = delta_ij - n_i n_j``.

    Removes vector components parallel to ``n_hat``, leaving the plane
    orthogonal to the propagation direction.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.20

    Parameters
    ----------
    n_hat
        Shape ``(3,)`` unit vector, the propagation/observation direction.

    Returns
    -------
    ndarray
        Shape ``(3, 3)``, dimensionless. Symmetric and idempotent.
    """
    n = as_unit_vector(n_hat)
    return _IDENTITY - np.outer(n, n)


def tt_projector(n_hat: ArrayLike) -> NDArray[np.float64]:
    """Rank-4 transverse-traceless projector ``Lambda_ij,kl``.

    .. code-block:: text

        P_ij        = delta_ij - n_i n_j
        Lambda_ijkl = P_ik P_jl - (1/2) P_ij P_kl

    Contracting this with a symmetric tensor gives the transverse-traceless part
    as seen by an observer along ``n_hat``.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.22

    Parameters
    ----------
    n_hat
        Shape ``(3,)`` unit vector.

    Returns
    -------
    ndarray
        Shape ``(3, 3, 3, 3)``, dimensionless. Idempotent under contraction.
    """
    p = transverse_projector(n_hat)
    # einsum's numpy stub returns Any; annotate so mypy narrows the result back
    # to NDArray[np.float64] rather than silently widening the return type.
    result: NDArray[np.float64] = np.einsum("ik,jl->ijkl", p, p) - 0.5 * np.einsum(
        "ij,kl->ijkl", p, p
    )
    return result


def apply_tt(tensor: ArrayLike, n_hat: ArrayLike) -> NDArray[np.float64]:
    """Project a symmetric tensor into the transverse-traceless gauge.

    Computes ``Lambda_ijkl T_kl`` for an observer along ``n_hat``. The result is
    symmetric, traceless, and transverse (``n_i T^TT_ij = 0``).

    Building the rank-4 projector explicitly is avoided here: contracting via
    the rank-2 projector is algebraically identical and markedly cheaper, which
    matters once this runs per field point over a 3-D grid.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.22

    Parameters
    ----------
    tensor
        Shape ``(3, 3)``, symmetric. Units are preserved.
    n_hat
        Shape ``(3,)`` unit vector.

    Returns
    -------
    ndarray
        Shape ``(3, 3)``, same units as ``tensor``.
    """
    t = as_tensor_3x3(tensor, "tensor")
    p = transverse_projector(n_hat)

    # Lambda_ijkl T_kl = (P T P)_ij - (1/2) P_ij tr(P T)
    projected = p @ t @ p
    trace_term = np.einsum("ij,ji->", p, t)
    # einsum's numpy stub returns Any; annotate so mypy narrows the result back
    # to NDArray[np.float64] rather than silently widening the return type.
    result: NDArray[np.float64] = projected - 0.5 * p * trace_term
    return result


__all__ = ["apply_tt", "transverse_projector", "tt_projector"]
