"""Benchmark: array factor against the analytic uniform-array reference (T-6.9).

**Deviation from spec, flagged per CLAUDE.md's "make absence loud" rule:** the
task calls for comparison against `arraytool` output. `arraytool` is not on
PyPI in a form installable in this environment (no pip/network access here;
see ``CLAUDE.md`` "Environment note"), so this benchmark instead compares
against the closed-form analytic array factor
``AF(psi) = sum_n w_n exp(i n psi)`` for a uniform linear array — the same
reference used to verify :func:`gwtb.array.beamform.array_factor` in
``tests/unit/test_beamform.py``, and the quantity `arraytool` itself would be
checked against. This is recorded here rather than silently substituted.
"""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.array.beamform import array_factor, taper
from gwtb.array.geometry import linear_array


def _analytic_uniform_af(n: int, d: float, wavelength: float, theta: float) -> complex:
    psi = 2.0 * np.pi / wavelength * d * np.sin(theta)
    if abs(np.sin(psi / 2.0)) < 1e-12:
        return complex(n)
    return complex(np.sin(n * psi / 2.0) / np.sin(psi / 2.0))


def _analytic_tapered_af(weights: np.ndarray, d: float, wavelength: float, theta: float) -> complex:
    n = weights.size
    indices = np.arange(n) - (n - 1) / 2.0
    psi = 2.0 * np.pi / wavelength * d * np.sin(theta)
    return complex(np.sum(weights * np.exp(1j * indices * psi)))


GEOMETRIES = [
    (4, 0.5),
    (8, 0.4),
    (16, 0.5),
    (32, 0.3),
    (64, 0.5),
]

TAPERS = ["uniform", "hann", "hamming"]


@pytest.mark.parametrize("n,d", GEOMETRIES)
def test_uniform_array_factor_matches_analytic(n: int, d: float) -> None:
    wavelength = 1.0
    geom = linear_array(n, d)
    weights = np.ones(n, dtype=complex)
    for theta in np.linspace(-1.3, 1.3, 11):
        direction = np.array([np.sin(theta), 0.0, np.cos(theta)])
        af = array_factor(geom, weights, wavelength, direction)
        expected = _analytic_uniform_af(n, d, wavelength, theta)
        assert af == pytest.approx(expected, rel=1e-9, abs=1e-9)


@pytest.mark.parametrize("kind", TAPERS)
@pytest.mark.parametrize("n,d", GEOMETRIES[:3])
def test_tapered_array_factor_matches_analytic(n: int, d: float, kind: str) -> None:
    wavelength = 1.0
    geom = linear_array(n, d)
    weights = taper(n, kind).astype(complex)
    for theta in np.linspace(-1.0, 1.0, 7):
        direction = np.array([np.sin(theta), 0.0, np.cos(theta)])
        af = array_factor(geom, weights, wavelength, direction)
        expected = _analytic_tapered_af(weights, d, wavelength, theta)
        assert af == pytest.approx(expected, rel=1e-9, abs=1e-9)
