"""Benchmark: mass-dipole cancellation for momentum-conserving sources (T-1.10).

The mass dipole's second derivative equals the net external force on the
system (``sum_A m_A a_A = dP/dt``). For an isolated, momentum-conserving
configuration this vanishes identically, which is why the leading radiative
multipole is the quadrupole rather than the dipole — see docs/PHYSICS.md §2
and CLAUDE.md rule 2 (conservation auditing). Pulled forward from Sprint 2
because discovering a dipole surprise late is the expensive failure mode.
"""

from __future__ import annotations

import numpy as np

_N_CONFIGS = 20
_N_BODIES = 5


def _dipole_second_derivative(masses: np.ndarray, accelerations: np.ndarray) -> np.ndarray:
    """``ddd_i = sum_A m_A a_i`` — equals dP/dt, the net external force."""
    return np.einsum("a,ai->i", masses, accelerations)


def test_dipole_vanishes_for_momentum_conserving_configurations() -> None:
    rng = np.random.default_rng(20260726)

    for _ in range(_N_CONFIGS):
        masses = rng.uniform(1.0, 100.0, size=_N_BODIES)
        accelerations = rng.uniform(-10.0, 10.0, size=(_N_BODIES, 3))

        # Subtract the mass-weighted mean acceleration so sum_A m_A a_A = 0
        # exactly (up to floating-point roundoff): this is what "momentum
        # conserving" means for a set of point accelerations.
        mean_acc = np.einsum("a,ai->i", masses, accelerations) / np.sum(masses)
        accelerations = accelerations - mean_acc

        ddd = _dipole_second_derivative(masses, accelerations)
        a_char = np.max(np.linalg.norm(accelerations, axis=1))
        m_total = np.sum(masses)

        ratio = np.linalg.norm(ddd) / (m_total * a_char)
        assert ratio < 1e-12, f"dipole did not cancel: ratio={ratio:.3e}"


def test_dipole_positive_control_unbalanced_configuration_exceeds_threshold() -> None:
    """A deliberately unbalanced (non-momentum-conserving) configuration must
    NOT pass the cancellation check — otherwise the check above would be
    vacuous (e.g. satisfied by any sufficiently loose tolerance)."""
    rng = np.random.default_rng(99)
    masses = rng.uniform(1.0, 100.0, size=_N_BODIES)
    accelerations = rng.uniform(-10.0, 10.0, size=(_N_BODIES, 3))
    # Deliberately do NOT enforce momentum conservation here.

    ddd = _dipole_second_derivative(masses, accelerations)
    a_char = np.max(np.linalg.norm(accelerations, axis=1))
    m_total = np.sum(masses)

    ratio = np.linalg.norm(ddd) / (m_total * a_char)
    assert ratio > 1e-3, f"positive control should exceed 1e-3, got {ratio:.3e}"
