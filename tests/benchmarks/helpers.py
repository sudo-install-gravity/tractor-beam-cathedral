"""Comparison helpers for the analytic benchmark suite.

No experiment exists to validate this project against, so every benchmark
compares against an analytic limit or an independent code. These helpers exist
to make those comparisons state their tolerance explicitly — a benchmark that
passes at an unstated tolerance is not a benchmark.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

# Reference values, deliberately independent of gwtb.core.constants. If the
# package's constants drift, these must not drift with them — that independence
# is the whole point of a benchmark.
#
# CODATA 2018 / IAU nominal values.
_G = 6.67430e-11  # m^3 kg^-1 s^-2   CODATA 2018
_C = 299792458.0  # m s^-1           exact, SI definition
_AU = 1.495978707e11  # m            IAU 2012, exact
_M_SUN = 1.98892e30  # kg            IAU 2015 nominal


@dataclass(frozen=True)
class ReferenceConstants:
    """Independently-sourced physical constants for benchmark comparison."""

    G: float = _G
    c: float = _C
    AU: float = _AU
    M_sun: float = _M_SUN

    @property
    def G_over_c4(self) -> float:
        """Sets the scale of every strain amplitude in this project."""
        return self.G / self.c**4

    @property
    def G_over_c5(self) -> float:
        """Sets the scale of every luminosity in this project."""
        return self.G / self.c**5


def assert_relative(
    value: float,
    expected: float,
    rtol: float,
    what: str = "value",
) -> None:
    """Assert ``value`` matches ``expected`` within relative tolerance ``rtol``.

    Reports the actual relative error and ratio on failure, because when a
    physics benchmark fails the useful question is almost always "by how much?"
    A factor of 2 suggests a convention mismatch, 1e-3 a truncation order, and
    1e16 a unit error.
    """
    if expected == 0.0:
        assert abs(value) <= rtol, f"{what}: expected 0, got {value!r} (atol={rtol:g})"
        return

    rel = abs(value - expected) / abs(expected)
    assert rel <= rtol, (
        f"{what}: relative error {rel:.3e} exceeds tolerance {rtol:.3e}\n"
        f"  expected: {expected!r}\n"
        f"  actual:   {value!r}\n"
        f"  ratio:    {value / expected:.6g}"
    )


def assert_order_of_magnitude(value: float, expected: float, decades: float = 0.5) -> None:
    """Assert ``value`` is within ``decades`` orders of magnitude of ``expected``.

    For scoping checks where the physics is only meaningful to an order of
    magnitude — feasibility-gap figures, for instance — and asserting tighter
    would be false precision.
    """
    if value == 0.0 or expected == 0.0:
        raise ValueError("order-of-magnitude comparison undefined for zero")

    delta = abs(math.log10(abs(value / expected)))
    assert delta <= decades, (
        f"differs by {delta:.2f} decades (limit {decades})\n"
        f"  expected: {expected:.6g}\n"
        f"  actual:   {value:.6g}"
    )


# --- T-1.0: canonical circular-binary fixture -------------------------------
#
# Every Sprint 1 benchmark that needs "a circular binary" (T-1.4, T-1.5, T-1.8,
# T-1.9, T-1.10) shares this fixture rather than each inventing its own — see
# docs/BACKLOG.md T-1.0 and docs/adr/0002-array-conventions.md for the shape
# and unit conventions it returns.
#
# Deliberately uses this module's own ``_G`` rather than
# ``gwtb.core.constants.G``: a benchmark fixture must stay independent of the
# package it is validating.


def circular_binary(
    m1: float, m2: float, a: float, t: float
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    """Two point masses in a circular orbit about their common barycentre.

    Motion is confined to the xy-plane:

    .. code-block:: text

        M          = m1 + m2
        omega      = sqrt(G M / a^3)                              (Kepler)
        x_rel(t)   = ( a cos(omega t), a sin(omega t), 0 )
        body 1 at  +(m2/M) x_rel(t)
        body 2 at  -(m1/M) x_rel(t)

    Velocities, accelerations, and jerks are the **analytic** first, second,
    and third time derivatives of those positions — never finite-differenced,
    consistent with ``gwtb.bodies.multipole``'s own rule:

    .. code-block:: text

        v_rel(t) = a omega    ( -sin(omega t),  cos(omega t), 0 )
        a_rel(t) = a omega^2  ( -cos(omega t), -sin(omega t), 0 )
        j_rel(t) = a omega^3  (  sin(omega t), -cos(omega t), 0 )

    Parameters
    ----------
    m1, m2
        Body masses, kg. Must be positive.
    a
        Orbital separation, m. Must be positive.
    t
        Evaluation time, s.

    Returns
    -------
    tuple of ndarray
        ``(masses, positions, velocities, accelerations, jerks)`` in
        ``docs/adr/0002-array-conventions.md`` shapes: ``masses`` is
        ``(2,)``; the rest are ``(2, 3)``. SI units, float64.
    """
    M = m1 + m2
    omega = math.sqrt(_G * M / a**3)

    cos_wt = math.cos(omega * t)
    sin_wt = math.sin(omega * t)

    x_rel = a * np.array([cos_wt, sin_wt, 0.0])
    v_rel = a * omega * np.array([-sin_wt, cos_wt, 0.0])
    a_rel = a * omega**2 * np.array([-cos_wt, -sin_wt, 0.0])
    j_rel = a * omega**3 * np.array([sin_wt, -cos_wt, 0.0])

    f1 = m2 / M
    f2 = -m1 / M

    masses = np.array([m1, m2], dtype=np.float64)
    positions = np.array([f1 * x_rel, f2 * x_rel], dtype=np.float64)
    velocities = np.array([f1 * v_rel, f2 * v_rel], dtype=np.float64)
    accelerations = np.array([f1 * a_rel, f2 * a_rel], dtype=np.float64)
    jerks = np.array([f1 * j_rel, f2 * j_rel], dtype=np.float64)

    return masses, positions, velocities, accelerations, jerks


@dataclass(eq=False)
class BinarySI:
    """Canonical Sprint 1 circular-binary parameter set.

    Every Sprint 1 benchmark that needs "an equal-mass circular binary"
    (T-1.8, T-1.9, T-1.10) shares these numbers rather than each choosing its
    own. ``eq=False`` because the array fields make the default dataclass
    equality (a tuple comparison that falls through to ``ndarray.__eq__``)
    ambiguous — nothing here needs instance equality.
    """

    m1: float
    m2: float
    a: float
    r: float
    t: float
    omega: float
    masses: NDArray[np.float64]
    positions: NDArray[np.float64]
    velocities: NDArray[np.float64]
    accelerations: NDArray[np.float64]
    jerks: NDArray[np.float64]


def binary_si() -> BinarySI:
    """The canonical Sprint 1 circular-binary parameter set.

    ``m1 = m2 = 1.0e30`` kg, ``a = 1.0e9`` m, ``r = 1.0e20`` m, evaluated at
    ``t = 0.3 / omega``.

    Returns
    -------
    BinarySI
        The parameters plus ``omega`` and the fixture arrays from
        :func:`circular_binary`, so callers never have to recompute either.
    """
    m1 = m2 = 1.0e30
    a = 1.0e9
    r = 1.0e20
    M = m1 + m2
    omega = math.sqrt(_G * M / a**3)
    t = 0.3 / omega

    masses, positions, velocities, accelerations, jerks = circular_binary(m1, m2, a, t)

    return BinarySI(
        m1=m1,
        m2=m2,
        a=a,
        r=r,
        t=t,
        omega=omega,
        masses=masses,
        positions=positions,
        velocities=velocities,
        accelerations=accelerations,
        jerks=jerks,
    )
