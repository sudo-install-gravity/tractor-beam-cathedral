"""Compute backend shim: a uniform array API dispatching to plain NumPy or a
Numba-JIT-accelerated path.

The dispatch shim itself (``Backend``, ``get_backend``) is infrastructure
(core/), not physics, so it carries no citation requirement. The kernels
built on top of it, such as :func:`field_grid`, are physics and are cited
individually.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.core.constants import G_OVER_C4
from gwtb.core.validation import as_float64

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


def _field_grid_loop(
    positions: NDArray[np.float64],
    q_ddots: NDArray[np.float64],
    field_points: NDArray[np.float64],
    g_over_c4: float,
) -> NDArray[np.float64]:
    """Retarded-field superposition over a grid of field points, using one
    already-evaluated ``q_ddot`` per source for every point in the grid.

    **This is valid only when the grid's light-crossing time is negligible
    compared to the timescale on which each source's ``q_ddot`` varies** —
    i.e. the grid extent is much smaller than ``c`` times the waveform's
    variation timescale (e.g. ``c / omega`` for an oscillating source). Under
    that condition, the per-point difference in retarded time changes
    ``q_ddot`` by a negligible amount and evaluating it once, at the grid's
    reference time, is an adequate approximation to evaluating it separately
    at each point's own retarded time. Outside that regime this function does
    **not** reproduce :func:`gwtb.propagate.retarded.field_at`/``propagate``,
    which retard per field point exactly; callers needing exact per-point
    retardation over a grid spanning a non-negligible light-crossing time must
    use those instead. See ``test_field_grid_single_slice_diverges_when_grid_
    light_crossing_time_is_not_negligible`` in ``tests/unit/test_backend.py``
    for a worked example of where this approximation breaks down.

    This is an explicit-loop reimplementation of
    ``strain_tt(q_ddots[a], r, n_hat)`` summed over sources — see
    :func:`gwtb.source.quadrupole.strain_tt` and
    :func:`gwtb.propagate.tt_projection.apply_tt` for the reference formula
    and citation. It is written with scalar loops (no NumPy fancy indexing or
    library calls) so that it is compilable as-is by both backends: the
    ``"numpy"`` backend runs it interpreted, the ``"numba"`` backend JIT-
    compiles the identical function.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 2 (per-source TT
    strain, summed here over sources for each of many field points)

    Parameters
    ----------
    positions
        Shape ``(N, 3)``, m. Source positions.
    q_ddots
        Shape ``(N, 3, 3)``, kg m^2 s^-2. Each source's quadrupole second
        derivative, already evaluated at that source's retarded time.
    field_points
        Shape ``(M, 3)``, m. Observation locations.
    g_over_c4
        ``G / c^4``, passed in rather than imported so the function has no
        module-level global lookups inside the hot loop (required for Numba
        nopython mode).

    Returns
    -------
    ndarray
        Shape ``(M, 3, 3)``, dimensionless TT strain at each field point.
    """
    n_sources = positions.shape[0]
    n_points = field_points.shape[0]
    result = np.zeros((n_points, 3, 3))
    for m in range(n_points):
        total = np.zeros((3, 3))
        for a in range(n_sources):
            dx = field_points[m, 0] - positions[a, 0]
            dy = field_points[m, 1] - positions[a, 1]
            dz = field_points[m, 2] - positions[a, 2]
            r = np.sqrt(dx * dx + dy * dy + dz * dz)
            nx = dx / r
            ny = dy / r
            nz = dz / r

            p00 = 1.0 - nx * nx
            p01 = -nx * ny
            p02 = -nx * nz
            p11 = 1.0 - ny * ny
            p12 = -ny * nz
            p22 = 1.0 - nz * nz

            q = q_ddots[a]
            p = np.array([[p00, p01, p02], [p01, p11, p12], [p02, p12, p22]])
            pqp = p @ q @ p
            # tr(P Q); p[i, j] * q[j, i] equals p[i, j] * q[i, j] here since both
            # P and Q are symmetric, matching apply_tt's einsum("ij,ji->", p, t).
            trace_pq = 0.0
            for i in range(3):
                for j in range(3):
                    trace_pq += p[i, j] * q[j, i]

            scale = 2.0 * g_over_c4 / r
            for i in range(3):
                for j in range(3):
                    total[i, j] += scale * (pqp[i, j] - 0.5 * p[i, j] * trace_pq)
        result[m] = total
    return result


def field_grid(
    positions: ArrayLike,
    q_ddots: ArrayLike,
    field_points: ArrayLike,
    backend: Backend,
) -> NDArray[np.float64]:
    """Superposed TT strain over a grid of field points, using ``backend``.

    Companion to :func:`gwtb.propagate.retarded.propagate` for the case that
    dominates cost on a large spatial grid: many field points, each source's
    quadrupole already evaluated (its retarded time need not be recomputed
    per grid point when the source waveform is evaluated once up front). The
    ``"numba"`` backend JIT-compiles the per-point loop; the ``"numpy"``
    backend runs the identical Python loop uncompiled, so the two are
    guaranteed to agree to floating-point precision.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 2 (same formula as
    :func:`gwtb.propagate.retarded.field_at`; see :func:`_field_grid_loop`)

    Parameters
    ----------
    positions
        Shape ``(N, 3)``, m. Source positions.
    q_ddots
        Shape ``(N, 3, 3)``, kg m^2 s^-2. Each source's quadrupole second
        derivative at its own retarded time.
    field_points
        Shape ``(M, 3)``, m. Observation locations.
    backend
        The compute backend to run the kernel under (see :func:`get_backend`).

    Returns
    -------
    ndarray
        Shape ``(M, 3, 3)``, dimensionless.
    """
    pos = as_float64(positions, "positions")
    if pos.ndim != 2 or pos.shape[1] != 3:
        raise ValueError(f"positions must have shape (N, 3), got {pos.shape}")
    q = as_float64(q_ddots, "q_ddots")
    if q.shape != (pos.shape[0], 3, 3):
        raise ValueError(f"q_ddots must have shape ({pos.shape[0]}, 3, 3), got {q.shape}")
    fp = as_float64(field_points, "field_points")
    if fp.ndim != 2 or fp.shape[1] != 3:
        raise ValueError(f"field_points must have shape (M, 3), got {fp.shape}")

    kernel = backend.jit(_field_grid_loop)
    # backend.jit is untyped (numba's decorator returns Any); annotate so mypy
    # narrows the result back rather than silently widening the return type.
    result: NDArray[np.float64] = kernel(pos, q, fp, float(G_OVER_C4))
    return result


@dataclass(frozen=True)
class SplitPhase:
    """A propagation phase split into an FP64 common part and an FP32-safe residual.

    Absolute propagation phase over 40 AU is ~1e10 wavelengths, i.e. ~1e11 rad.
    float32 carries ~1e-7 relative precision, so storing that phase directly
    leaves ~1e4 rad of error — the number is not merely imprecise, it is
    entirely noise. Yet the *differences* between elements of a 10 km aperture
    are of order a radian, and those are what interference depends on.

    Splitting is what makes an FP32 path possible at all: keep the large common
    term in FP64 once per field point, and carry only the small per-element
    residual in FP32, where its dynamic range is a comfortable fit.

    Attributes
    ----------
    reference
        The common-mode phase, rad, float64. Shared by every element.
    differential
        Shape ``(N,)``, rad, float32. Per-element residual about ``reference``.
    wavelength
        The wavelength the split was computed for, m. Retained so a recombined
        phase cannot be silently paired with the wrong one.
    """

    reference: float
    differential: NDArray[np.float32]
    wavelength: float

    def recombine(self) -> NDArray[np.float64]:
        """Total per-element phase in float64, rad.

        .. warning::

           **This is lossy at astronomical range, irreducibly so, and is not
           the method to build on.** Use :meth:`phasor`.

           At 40 AU and 1 kHz the reference is ~1.25e8 rad, where float64's
           spacing is ~1.5e-8 rad — some 340 times *larger* than the entire
           per-element differential (~4.4e-11 rad). Adding the two therefore
           absorbs the differential completely and this method returns a
           constant. That is not a defect in the split; it is the fact that
           motivates it. The absolute phase simply is not representable to the
           precision the differential carries, in float64 or float32.

        Retained because it is the literal quantity T-11.3's acceptance
        criterion names, and because a caller who does want the absolute phase
        should get it from a documented method rather than reinventing the
        addition and assuming it worked.
        """
        result: NDArray[np.float64] = self.reference + self.differential.astype(np.float64)
        return result

    def phasor(self) -> NDArray[np.complex128]:
        """Per-element complex phasor ``exp(i * phi_a)``, preserving the differential.

        .. code-block:: text

            exp(i phi_a) = exp(i phi_ref) * exp(i dphi_a)

        Phasors multiply, so the large and small phases never have to be
        *added* — which is what makes this exact where :meth:`recombine` cannot
        be. The reference is range-reduced modulo ``2 pi`` before exponentiation
        and contributes a common-mode error of ~1.5e-8 rad, identical for every
        element; interference depends only on element-to-element differences,
        which survive intact.

        This is the method downstream field evaluation should use.
        """
        common = np.exp(1j * (self.reference % (2.0 * np.pi)))
        result: NDArray[np.complex128] = common * np.exp(1j * self.differential.astype(np.float64))
        return result


def split_phase(
    reference_geometry: ArrayLike,
    element_offsets: ArrayLike,
    wavelength: float,
) -> SplitPhase:
    """Decompose propagation phase into an FP64 reference plus an FP32-safe residual.

    .. code-block:: text

        phi_a = (2 pi / lambda) * |s - q_a|
              = (2 pi / lambda) * |s|          <- reference, FP64
              + (2 pi / lambda) * (R_a - |s|)  <- differential, FP32-safe

    The range difference is formed by the same cancellation-free identity used
    in :func:`gwtb.array.focus._differential_range`:
    ``R_a - R_ref = (|q_a|^2 - 2 s.q_a) / (R_a + R_ref)``. Subtracting the two
    ranges directly would discard the eight most significant digits before FP32
    ever entered the picture, which would defeat the split.

    **Signature note.** BACKLOG.md T-11.3 specifies ``split_phase(reference_
    geometry, element_offsets)``. ``wavelength`` is added because a phase cannot
    be formed from geometry alone; the two named parameters keep their specified
    meaning. This is a deviation from the written spec and is recorded here
    rather than made silently.

    This module is ``core/`` infrastructure and carries no citation requirement;
    the underlying retarded-time relation is cited at
    :func:`gwtb.propagate.retarded.field_at`.

    Parameters
    ----------
    reference_geometry
        Shape ``(3,)``, m. Vector from the array reference point to the field
        point — the ``s`` above.
    element_offsets
        Shape ``(N, 3)``, m. Element positions relative to the same reference
        point — the ``q_a`` above.
    wavelength
        Radiation wavelength, m. Must be positive and finite.

    Returns
    -------
    SplitPhase
        Whose :meth:`SplitPhase.recombine` reproduces the full-FP64 phase to
        better than 1e-5 rad for a 10 km aperture at 40 AU.
    """
    s = as_float64(reference_geometry, "reference_geometry")
    if s.shape != (3,):
        raise ValueError(f"reference_geometry must have shape (3,), got {s.shape}")
    q = as_float64(element_offsets, "element_offsets")
    if q.ndim != 2 or q.shape[1] != 3:
        raise ValueError(f"element_offsets must have shape (N, 3), got {q.shape}")
    if not np.isfinite(wavelength) or wavelength <= 0.0:
        raise ValueError(f"wavelength must be positive and finite, got {wavelength!r}")

    range_ref = float(np.linalg.norm(s))
    if range_ref == 0.0:
        raise ValueError("reference_geometry is the zero vector; the field point coincides")

    range_a = np.linalg.norm(s - q, axis=1)
    delta_range = (np.einsum("ai,ai->a", q, q) - 2.0 * (q @ s)) / (range_a + range_ref)

    wavenumber = 2.0 * np.pi / wavelength
    return SplitPhase(
        reference=wavenumber * range_ref,
        differential=(wavenumber * delta_range).astype(np.float32),
        wavelength=float(wavelength),
    )


__all__ = ["Backend", "SplitPhase", "field_grid", "get_backend", "split_phase"]
