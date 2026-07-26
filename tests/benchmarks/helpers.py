"""Comparison helpers for the analytic benchmark suite.

No experiment exists to validate this project against, so every benchmark
compares against an analytic limit or an independent code. These helpers exist
to make those comparisons state their tolerance explicitly — a benchmark that
passes at an unstated tolerance is not a benchmark.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

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
