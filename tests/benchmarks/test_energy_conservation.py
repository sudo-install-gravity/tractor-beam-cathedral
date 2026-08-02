"""Benchmark: energy conservation (T-12.3).

Radiated energy integrated over a distant sphere (the Isaacson GW energy
flux, integrated numerically over solid angle) versus the quadrupole
luminosity integral (Blanchet eq. 4, already the project's primary
luminosity formula). AC: agreement to rtol 1e-4.

.. code-block:: text

    dE/dt = (c^3 / (32 pi G)) * oint <hdot_ij^TT hdot_ij^TT> r^2 dOmega

Source: Sathyaprakash & Schutz, "Physics, Astrophysics and Cosmology with
Gravitational Waves," Living Rev. Relativ. 12:2 (2009), open access,
PMC5255530, eq. (14) `[verify: the equation is served as an embedded image in
the PMC HTML, so the exact printed prefactor could not be read as text; their
surrounding prose confirms this is the Isaacson flux expression]`.

**The prefactor (32*pi*G, not 16*pi*G) is independently confirmed here by
numerical self-consistency, which is the primary source of confidence for
this benchmark rather than the citation above.** Substituting the retarded
quadrupole strain h_ij^TT = (2G/(c^4 r)) Lambda_ijkl(n) Qddot_kl(t-r/c)
(Blanchet eq. 2, already the project's `strain_tt`) and numerically
integrating the flux over the sphere for a known Qdddot reproduces
`luminosity()` (Blanchet eq. 4, already verified) to 6 decimal places with
32*pi*G, and is off by exactly a factor of 2 with 16*pi*G — decisive between
the two candidates independent of resolving the citation's exact text.
"""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.core.constants import G, c
from gwtb.source.quadrupole import luminosity

_PREFACTOR_32PI = c**3 / (32.0 * np.pi * G)
_PREFACTOR_16PI = c**3 / (16.0 * np.pi * G)


def _random_trace_free(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    raw = rng.uniform(-1.0, 1.0, size=(3, 3))
    raw = raw + raw.T
    return raw - np.eye(3) * (np.trace(raw) / 3.0)


def _integrated_flux(
    q_dddot: np.ndarray, r: float, prefactor: float, n_theta: int = 300, n_phi: int = 600
) -> float:
    """Numerically integrate the Isaacson flux over a sphere of radius r.

    Vectorized over the whole angular grid at once (the TT projection
    ``P T P - (1/2) P tr(PT)`` applied per-direction via broadcasting,
    the same algebra :func:`gwtb.propagate.tt_projection.apply_tt` uses for a
    single direction) rather than a Python double loop, since this benchmark
    calls it many times across grids up to 3e5 points.
    """
    thetas = np.linspace(0.0, np.pi, n_theta)
    phis = np.linspace(0.0, 2.0 * np.pi, n_phi, endpoint=False)
    dtheta = thetas[1] - thetas[0]
    dphi = phis[1] - phis[0]

    sin_t = np.sin(thetas)
    cos_t = np.cos(thetas)
    cos_p = np.cos(phis)
    sin_p = np.sin(phis)

    nx = np.outer(sin_t, cos_p)  # (n_theta, n_phi)
    ny = np.outer(sin_t, sin_p)
    nz = np.outer(cos_t, np.ones_like(phis))
    n_hat = np.stack([nx, ny, nz], axis=-1)  # (n_theta, n_phi, 3)

    identity = np.eye(3)
    p = identity - np.einsum("...i,...j->...ij", n_hat, n_hat)  # (n_theta, n_phi, 3, 3)

    pt = np.einsum("...ik,kl->...il", p, q_dddot)
    ptp = np.einsum("...il,...lj->...ij", pt, p)
    trace_pt = np.einsum("...ii->...", pt)
    tt = ptp - 0.5 * p * trace_pt[..., None, None]

    hdot = (2.0 * G / (c**4 * r)) * tt
    intensity = np.einsum("...ij,...ij->...", hdot, hdot)  # (n_theta, n_phi)
    weighted = intensity * sin_t[:, None]

    flux_integral = weighted.sum() * dtheta * dphi * r**2
    return prefactor * flux_integral


def test_integrated_energy_flux_matches_the_quadrupole_luminosity() -> None:
    """AC: agreement to rtol 1e-4."""
    q3 = _random_trace_free(seed=0)
    r = 1.0e12  # arbitrary — must cancel between the flux and its 1/r^2 falloff

    measured = _integrated_flux(q3, r, _PREFACTOR_32PI)
    expected = luminosity(q3)

    assert measured == pytest.approx(expected, rel=1e-4)


def test_result_is_independent_of_the_integration_radius() -> None:
    """A genuine radiative flux is r-independent once integrated over the
    full sphere (the h ~ 1/r falloff cancels against the r^2 area element)."""
    q3 = _random_trace_free(seed=1)
    near = _integrated_flux(q3, 1.0e9, _PREFACTOR_32PI, n_theta=150, n_phi=300)
    far = _integrated_flux(q3, 1.0e15, _PREFACTOR_32PI, n_theta=150, n_phi=300)
    assert near == pytest.approx(far, rel=1e-6)


def test_16pi_prefactor_is_off_by_exactly_a_factor_of_two() -> None:
    """Documents the resolved ambiguity: 16*pi*G is wrong, decisively and by
    exactly 2x, not merely 'less good' — this is why the test above uses
    32*pi*G and not the other commonly-seen (but incorrect, for this
    normalization convention) prefactor."""
    q3 = _random_trace_free(seed=2)
    r = 1.0e10

    correct = _integrated_flux(q3, r, _PREFACTOR_32PI, n_theta=150, n_phi=300)
    wrong = _integrated_flux(q3, r, _PREFACTOR_16PI, n_theta=150, n_phi=300)
    expected = luminosity(q3)

    assert correct == pytest.approx(expected, rel=1e-3)
    assert wrong == pytest.approx(2.0 * expected, rel=1e-3)


def test_holds_for_multiple_random_quadrupole_configurations() -> None:
    for seed in range(4):
        q3 = _random_trace_free(seed=seed + 10)
        measured = _integrated_flux(q3, 1.0e11, _PREFACTOR_32PI, n_theta=150, n_phi=300)
        expected = luminosity(q3)
        assert measured == pytest.approx(expected, rel=1e-3), f"seed={seed}"
