"""Stress-energy conservation auditing.

The mass dipole's second derivative equals the net external force on a system
(``sum_A m_A a_A = dP/dt``, see :mod:`gwtb.source.multipole_rad`). For an
isolated system this vanishes, which is *why* the leading radiative multipole
is the quadrupole rather than the dipole (``docs/PHYSICS.md`` §2). This module
checks that assumption numerically rather than assuming it silently: any
downstream calculation built on a non-conserving source is otherwise
indistinguishable from a physical one until someone notices the numbers are
wrong by ten orders of magnitude (CLAUDE.md rule 2).

Two layers live here, and the split is deliberate. :func:`audit` *detects*
whether a configuration conserves momentum. :class:`StampedResult` (T-2.2)
*carries that verdict forward* through every downstream computation, so a
number derived from a non-conserving source cannot reach a plot or a ledger row
still looking physical. Detection without propagation is the gap T-2.2 closes:
the ten-orders-of-magnitude dipole artifact is only dangerous once it has been
laundered through arithmetic into something that no longer remembers where it
came from.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, DTypeLike, NDArray

from gwtb.core.validation import as_body_array, as_masses

#: Relative-residual threshold below which a configuration is judged
#: momentum-conserving. Matches the tolerance used by the T-1.10 dipole-
#: cancellation benchmark, which established that a momentum-conserving
#: configuration cancels to machine-roundoff (~1e-16), leaving many orders of
#: margin before this threshold.
_CONSERVING_TOL = 1e-12


@dataclass(frozen=True)
class ConservationReport:
    """Result of auditing a system of point masses for momentum conservation.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.35

    Attributes
    ----------
    net_force
        Shape ``(3,)``, N. ``sum_A m_A a_A``, the mass dipole's second time
        derivative, equal to ``dP/dt`` by eq. (4.35).
    is_conserving
        ``True`` if ``residual`` is below the conserving threshold.
    residual
        Dimensionless. ``|net_force| / (M_total * a_char)``, where
        ``a_char = max_A |a_A|``. Zero for an exactly balanced configuration;
        scales linearly with an imposed imbalance small compared to
        ``a_char`` (the regime in which ``a_char`` itself is not disturbed by
        the imbalance being measured).
    """

    net_force: NDArray[np.float64]
    is_conserving: bool
    residual: float


def audit(masses: ArrayLike, accelerations: ArrayLike) -> ConservationReport:
    """Audit a system of point masses for momentum conservation.

    Computes the net external force ``sum_A m_A a_A`` (the mass dipole's
    second derivative — see :func:`gwtb.source.multipole_rad.
    dipole_second_derivative`, which this duplicates rather than imports, to
    keep this module's only dependency on the validated masses/accelerations
    contract) and reports whether it vanishes relative to the system's
    characteristic force scale.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.35

    Flanagan & Hughes eq. (4.34)-(4.35) identify ``dM_1/dt = P`` (momentum);
    one further time derivative gives ``d^2 M_1/dt^2 = dP/dt``, the net
    external force. For an isolated system, momentum conservation forces this
    to vanish — this function tests that numerically rather than assuming it.

    Parameters
    ----------
    masses
        Shape ``(N,)``, kg.
    accelerations
        Shape ``(N, 3)``, m/s^2.

    Returns
    -------
    ConservationReport
        See class docstring. Not stamped; see module docstring.
    """
    m = as_masses(masses)
    a = as_body_array(accelerations, "accelerations", n_bodies=m.size)

    net_force: NDArray[np.float64] = np.einsum("a,ai->i", m, a)

    m_total = float(np.sum(m))
    a_char = float(np.max(np.linalg.norm(a, axis=1)))
    scale = m_total * a_char

    if scale > 0.0:
        residual = float(np.linalg.norm(net_force) / scale)
    else:
        # a_char == 0: every body is unaccelerated, so the system trivially
        # conserves momentum regardless of net_force's (necessarily zero)
        # floating-point noise.
        residual = 0.0

    return ConservationReport(
        net_force=net_force,
        is_conserving=bool(residual < _CONSERVING_TOL),
        residual=residual,
    )


#: The stamp itself. Any result computed from a source that violates
#: stress-energy conservation carries this string in its provenance, and every
#: rendering of that result — ``repr``, ``str``, JSON — reproduces it verbatim.
#: CLAUDE.md rule 2: **never strip it.**
UNPHYSICAL_STAMP = "UNPHYSICAL: violates d_mu T^mu-nu = 0"


class StampStrippedError(TypeError):
    """Raised when an ``UNPHYSICAL``-stamped result is coerced to a bare array.

    Subclasses :class:`TypeError` because that is what NumPy callers already
    expect from a failed array coercion.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.35 (the
    conservation condition whose violation this class guards)
    """


def _merge_provenance(operands: tuple[object, ...]) -> str | None:
    """Provenance of a result computed from ``operands``.

    Unphysicality is **contagious**: anything computed from a stamped input is
    itself stamped. Distinct provenance strings are joined so a result built
    from two different unphysical sources names both.
    """
    seen: list[str] = []
    for op in operands:
        if isinstance(op, StampedResult) and op.provenance is not None:
            if op.provenance not in seen:
                seen.append(op.provenance)
    if not seen:
        return None
    return " | ".join(seen)


class StampedResult:
    """An array carrying the provenance of the source it was computed from.

    Wraps any array-like together with a ``provenance`` string. When that
    provenance contains :data:`UNPHYSICAL_STAMP`, every rendering of the value
    reproduces the stamp, and coercion to a bare NumPy array *raises* rather
    than quietly discarding it.

    **Why this is a wrapper and not an** ``ndarray`` **subclass.** The subclass
    is the more obvious design and it was measured first. It propagates
    provenance beautifully through arithmetic, slicing, ufuncs and reductions
    via ``__array_finalize__`` — but ``np.asarray`` on an ``ndarray`` subclass
    takes a fast path that returns a base-class array *without ever calling*
    ``__array__``. There is no hook, so the stamp vanishes silently on the one
    call most likely to appear in plotting and serialization code. A wrapper is
    more work — arithmetic must be routed through
    ``__array_ufunc__`` — but ``np.asarray`` is then obliged to call
    ``__array__``, which is what makes the guarantee real. See
    ``docs/adr/0005-unphysical-stamp-propagation.md``.

    There is deliberately **no** ``unstamp()`` method. The sanctioned way to
    obtain raw numbers is the :attr:`value` attribute, which is explicit,
    greppable, and auditable in review — unlike a method whose name would
    suggest that removing the stamp is a supported operation.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.35 (this class
    introduces no equation of its own; it carries the provenance of the
    conservation condition stated there)

    Parameters
    ----------
    value
        Any array-like. Stored as a NumPy array; not restricted to float64,
        since comparisons legitimately produce boolean results.
    provenance
        Free text, or ``None`` for an unstamped result. Pass a string
        containing :data:`UNPHYSICAL_STAMP` to stamp it — or better, use
        :meth:`unphysical`.

    Attributes
    ----------
    value
        The wrapped array.
    provenance
        The provenance string, or ``None``.
    """

    __slots__ = ("provenance", "value")

    #: Ensure NumPy defers binary ops with plain ndarrays to this class rather
    #: than broadcasting into an ndarray and dropping the wrapper.
    __array_priority__ = 1000.0

    def __init__(self, value: ArrayLike, provenance: str | None = None) -> None:
        self.value: NDArray[Any] = np.asarray(value)
        self.provenance: str | None = provenance

    # -- construction -------------------------------------------------------

    @classmethod
    def physical(cls, value: ArrayLike) -> StampedResult:
        """Wrap a result from a momentum-conserving source (no stamp).

        Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.35
        """
        return cls(value, None)

    @classmethod
    def unphysical(cls, value: ArrayLike, reason: str | None = None) -> StampedResult:
        """Wrap a result from a source that violates momentum conservation.

        The provenance is :data:`UNPHYSICAL_STAMP`, optionally followed by
        ``reason`` for context (e.g. which term or task produced it).

        Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.35
        """
        stamp = UNPHYSICAL_STAMP if reason is None else f"{UNPHYSICAL_STAMP} ({reason})"
        return cls(value, stamp)

    # -- inspection ---------------------------------------------------------

    @property
    def is_unphysical(self) -> bool:
        """Whether this result's provenance carries :data:`UNPHYSICAL_STAMP`.

        Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.35
        """
        return self.provenance is not None and UNPHYSICAL_STAMP in self.provenance

    def to_json(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict, carrying the stamp.

        Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 4.35
        """
        return {
            "value": self.value.tolist(),
            "provenance": self.provenance,
            "is_unphysical": self.is_unphysical,
        }

    # -- rendering ----------------------------------------------------------

    def __repr__(self) -> str:
        if self.provenance is None:
            return f"StampedResult({self.value!r})"
        return f"StampedResult({self.value!r}, provenance={self.provenance!r})"

    def __str__(self) -> str:
        if self.provenance is None:
            return str(self.value)
        return f"{self.value}\n{self.provenance}"

    # -- NumPy interoperation ----------------------------------------------

    def __array__(self, dtype: DTypeLike | None = None, copy: bool | None = None) -> NDArray[Any]:
        """Coerce to a bare array — refused while the stamp is set.

        This is the hook ``np.asarray`` calls, and refusing here is the whole
        point of the class: it is the difference between a stamp that survives
        and one that is dropped by a plotting call nobody reviews.
        """
        if self.is_unphysical:
            raise StampStrippedError(
                f"refusing to convert a stamped result to a bare array: "
                f"{self.provenance}. Coercion would discard the stamp, which "
                f"CLAUDE.md rule 2 forbids. If you genuinely intend to discard "
                f"provenance, take `.value` explicitly so the choice is visible "
                f"in review."
            )
        out = np.asarray(self.value, dtype=dtype) if dtype is not None else self.value
        return np.array(out, copy=True) if copy else out

    def __array_ufunc__(self, ufunc: np.ufunc, method: str, *inputs: Any, **kwargs: Any) -> Any:
        """Apply ``ufunc`` to the unwrapped values and re-stamp the result.

        Covers arithmetic, comparisons and reductions in one place, so the
        stamp survives ``a + b``, ``np.sin(a)`` and ``a.sum()`` alike.
        """
        if "out" in kwargs:
            raise StampStrippedError(
                "`out=` is not supported on a StampedResult: writing into a "
                "caller-supplied array would move the numbers somewhere the "
                "provenance cannot follow. Take the returned value instead."
            )
        raw = tuple(x.value if isinstance(x, StampedResult) else x for x in inputs)
        result = getattr(ufunc, method)(*raw, **kwargs)
        if result is NotImplemented:
            return NotImplemented
        provenance = _merge_provenance(inputs)
        if isinstance(result, tuple):
            return tuple(StampedResult(r, provenance) for r in result)
        return StampedResult(result, provenance)

    # -- container behaviour ------------------------------------------------

    def __getitem__(self, key: Any) -> StampedResult:
        return StampedResult(self.value[key], self.provenance)

    def __len__(self) -> int:
        return len(self.value)

    # -- arithmetic ---------------------------------------------------------
    #
    # Defining __array_ufunc__ alone is not enough: `stamped + 2` looks up
    # `StampedResult.__add__`, which Python does not synthesise. Each operator
    # is therefore routed explicitly back through the ufunc machinery above.

    def __add__(self, other: Any) -> Any:
        return np.add(self, other)

    def __radd__(self, other: Any) -> Any:
        return np.add(other, self)

    def __sub__(self, other: Any) -> Any:
        return np.subtract(self, other)

    def __rsub__(self, other: Any) -> Any:
        return np.subtract(other, self)

    def __mul__(self, other: Any) -> Any:
        return np.multiply(self, other)

    def __rmul__(self, other: Any) -> Any:
        return np.multiply(other, self)

    def __truediv__(self, other: Any) -> Any:
        return np.true_divide(self, other)

    def __rtruediv__(self, other: Any) -> Any:
        return np.true_divide(other, self)

    def __pow__(self, other: Any) -> Any:
        return np.power(self, other)

    def __neg__(self) -> Any:
        return np.negative(self)

    def __abs__(self) -> Any:
        return np.absolute(self)

    def __eq__(self, other: Any) -> Any:  # type: ignore[override]
        return np.equal(self, other)

    def __ne__(self, other: Any) -> Any:  # type: ignore[override]
        return np.not_equal(self, other)

    #: An array wrapper is not hashable, for the same reason ``ndarray`` is not.
    __hash__ = None  # type: ignore[assignment]


__all__ = [
    "UNPHYSICAL_STAMP",
    "ConservationReport",
    "StampStrippedError",
    "StampedResult",
    "audit",
]
