"""Compute backend shim: a uniform array API dispatching to plain NumPy or a
Numba-JIT-accelerated path.

This module is infrastructure (core/), not physics, so it carries no
citation requirement. Its only job is to let downstream numerical kernels
(T-11.2 and later) write one implementation and pick a backend at call time,
without every kernel re-implementing its own dispatch.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

_KNOWN_BACKENDS = ("numpy", "numba")


def _identity_jit(func: Callable[..., Any]) -> Callable[..., Any]:
    """No-op stand-in for ``numba.njit`` on the plain NumPy backend."""
    return func


@dataclass(frozen=True)
class Backend:
    """A named compute backend: an array module and a JIT decorator.

    Attributes
    ----------
    name
        ``"numpy"`` or ``"numba"``.
    xp
        The array module (``numpy`` for both backends here — Numba
        JIT-compiles functions that call NumPy, it does not replace NumPy's
        API).
    jit
        Decorator to accelerate a function: ``numba.njit`` for the
        ``"numba"`` backend, an identity pass-through for ``"numpy"``.
    """

    name: str
    xp: Any
    jit: Callable[[Callable[..., Any]], Callable[..., Any]]


def get_backend(name: str) -> Backend:
    """Return the named compute backend.

    Parameters
    ----------
    name
        ``"numpy"`` or ``"numba"``.

    Returns
    -------
    Backend
        See class docstring.

    Raises
    ------
    ValueError
        If ``name`` is not one of the known backends.
    """
    if name == "numpy":
        return Backend(name="numpy", xp=np, jit=_identity_jit)
    if name == "numba":
        import numba

        return Backend(name="numba", xp=np, jit=numba.njit)
    raise ValueError(f"unknown backend {name!r}; expected one of {_KNOWN_BACKENDS}")


__all__ = ["Backend", "get_backend"]
