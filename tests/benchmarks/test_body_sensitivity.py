"""T-4.8: sensitivity of radiation to (R, rho) at fixed total mass M.

This is the direct numerical demonstration of claim B-2's two halves
(``docs/CLAIMS.md``):

* the **rigid** model's radiative signature depends on mass and trajectory
  only — :meth:`gwtb.bodies.sphere.Sphere.self_quadrupole` is identically
  zero for *any* ``(R, rho)`` pair at fixed ``M`` (T-4.2);
* the **elastic** model breaks that degeneracy — the tidally-induced
  quadrupole (T-4.3) scales as ``R^5`` and its Love number depends on density
  through self-gravity, so at fixed ``M`` a sweep over ``R`` changes it by
  orders of magnitude, not merely detectably.

Unlike ``tests/unit/test_sphere.py``'s and ``tests/unit/test_elastic.py``'s
two-point contrasts, this sweeps five ``(R, rho)`` pairs spanning two orders
of magnitude in ``R`` at exactly the same ``M``, and states the sensitivity
as a single relative-variation number for each model — a benchmark, not a
unit test, in the sense used elsewhere in this directory.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from gwtb.bodies.elastic import MATERIALS, induced_quadrupole
from gwtb.bodies.multipole import quadrupole_moment
from gwtb.bodies.sphere import Sphere

#: Fixed total mass, kg, held constant across every sweep point.
_M = 1.0e15

#: Radii spanning two orders of magnitude; density is set at each point to
#: hold M fixed, per M = (4/3) pi R^3 rho.
_RADII = np.array([10.0, 31.6, 100.0, 316.0, 1000.0])

#: A representative external tidal field, s^-2 (trace-free already), of the
#: same order used in tests/unit/test_elastic.py.
_TIDAL_FIELD = np.diag([2.0e-14, -1.0e-14, -1.0e-14])


def _sweep_spheres() -> list[Sphere]:
    """Spheres at each radius in ``_RADII``, density set to hold M = ``_M`` fixed."""
    return [Sphere(radius=r, density=_M / ((4.0 / 3.0) * math.pi * r**3)) for r in _RADII]


def test_sweep_fixture_actually_holds_mass_fixed() -> None:
    """Guard for the guard: if this drifts, both ACs below are vacuous."""
    masses = [s.mass for s in _sweep_spheres()]
    for m in masses:
        assert m == pytest.approx(_M, rel=1e-9)
    # And radius/density must actually vary — otherwise there is no sweep.
    densities = [s.density for s in _sweep_spheres()]
    assert max(densities) / min(densities) > 100.0


# --- AC: rigid model is invariant (< 1e-12 relative) ------------------------


def test_rigid_model_radiation_is_invariant_across_the_sweep() -> None:
    """Claim B-2: self_quadrupole is identically zero for every (R, rho).

    "Relative variation" of an identically-zero quantity is compared against
    an absolute floor rather than a ratio (0/0 is undefined) — this is the
    same convention ``tests/unit/test_sphere.py`` already uses. The floor,
    1e-15, is tighter than the AC's 1e-12 by three orders of magnitude, so a
    stray R- or rho-dependent term reintroduced into
    :meth:`~gwtb.bodies.sphere.Sphere.self_quadrupole` would be caught long
    before it reached the AC's own threshold.
    """
    magnitudes = [float(np.max(np.abs(s.self_quadrupole()))) for s in _sweep_spheres()]
    for m in magnitudes:
        assert m <= 1e-15, "rigid-model radiation is not exactly invariant"

    # State the AC's own threshold explicitly too, in relative-variation
    # terms, using the fixed-M trajectory quadrupole as the invariant
    # baseline: gwtb.bodies.multipole.quadrupole_moment depends only on mass
    # and position, never on the sphere's own R or rho, so recomputing it at
    # each sweep point (same trajectory, only the *body* changes) must return
    # bit-identical results to relative variation far under 1e-12.
    positions = np.array([[100.0, 0.0, 0.0], [-100.0, 0.0, 0.0]])
    trajectory_magnitudes = []
    for _sphere in _sweep_spheres():
        # The point-mass trajectory model never reads sphere.radius or
        # sphere.density; only sphere.mass, held fixed by construction above.
        masses = np.array([_sphere.mass / 2.0, _sphere.mass / 2.0])
        q = quadrupole_moment(masses, positions)
        trajectory_magnitudes.append(float(np.max(np.abs(q))))
    trajectory_magnitudes_arr = np.array(trajectory_magnitudes)
    relative_variation = (
        trajectory_magnitudes_arr.max() - trajectory_magnitudes_arr.min()
    ) / trajectory_magnitudes_arr.min()
    assert relative_variation < 1e-12


# --- AC: elastic model varies (> 1e-3 relative, realistic rigidity) --------


@pytest.mark.parametrize("material_name", ["steel", "tungsten", "osmium"])
def test_elastic_model_radiation_varies_across_the_sweep(material_name: str) -> None:
    """T-4.3: induced quadrupole depends on R and rho independently.

    Held fixed across the sweep: total mass M, the material's own rigidity
    (an intensive property — the same "steel" regardless of how large the
    body built from it is), and the external tidal field. Only R (and hence
    rho, and hence surface gravity and the Love number) vary.
    """
    material = MATERIALS[material_name]
    magnitudes = [
        float(np.max(np.abs(induced_quadrupole(s, _TIDAL_FIELD, rigidity=material.rigidity))))
        for s in _sweep_spheres()
    ]
    magnitudes_arr = np.array(magnitudes)

    assert np.all(magnitudes_arr > 0.0), "a real material must deform at all under a tidal field"
    relative_variation = (magnitudes_arr.max() - magnitudes_arr.min()) / magnitudes_arr.min()
    assert relative_variation > 1e-3

    # The AC says ">1e-3", but the true sensitivity is dramatically larger.
    # R^5 alone would span (1000/10)^5 = 1e10 across this sweep; the Love
    # number's own saturation toward the fluid limit (k2 -> 3/2) at large R
    # partially offsets that (measured ~7.6e4 to ~1.0e5 across the three
    # materials here), but it is still eight orders of magnitude above the
    # AC's threshold. Pinned at 1e4 — comfortably below the measured floor,
    # comfortably above ">1e-3" — so a change that accidentally weakens the
    # R-dependence (e.g. a wrong exponent) still fails even though it would
    # pass the AC's own, much looser bound.
    assert relative_variation > 1.0e4


def test_elastic_variation_is_dominated_by_r_to_the_fifth() -> None:
    """Isolate the R^5 scaling from the Love number's own rho-dependence.

    At fixed Love number (``love_k2=`` instead of ``rigidity=``), only the
    explicit ``R^5`` prefactor can vary the result — this is exactly
    ``tests/unit/test_elastic.py::test_radius_dependence_is_fifth_power_at_fixed_love_number``,
    reused here as the mechanism that makes the realistic-rigidity case above
    vary by far more than the AC's own threshold.
    """
    k2 = 0.3
    magnitudes = [
        float(np.max(np.abs(induced_quadrupole(s, _TIDAL_FIELD, love_k2=k2))))
        for s in _sweep_spheres()
    ]
    ratios = np.array(magnitudes[1:]) / np.array(magnitudes[:-1])
    radius_ratios = _RADII[1:] / _RADII[:-1]
    np.testing.assert_allclose(ratios, radius_ratios**5, rtol=1e-9)


def test_density_alone_moves_the_elastic_result_at_fixed_radius() -> None:
    """The other half of B-2's break: rho enters even when R does not.

    Mirrors ``tests/unit/test_elastic.py::test_density_changes_the_response_at_fixed_radius``,
    stated here as part of the same sensitivity study rather than a separate
    two-point check.
    """
    steel = MATERIALS["steel"]
    radius = 100.0
    densities = np.array([500.0, 1000.0, 4000.0, 8000.0, 16000.0])
    magnitudes = [
        float(
            np.max(
                np.abs(
                    induced_quadrupole(
                        Sphere(radius=radius, density=rho),
                        _TIDAL_FIELD,
                        rigidity=steel.rigidity,
                    )
                )
            )
        )
        for rho in densities
    ]
    magnitudes_arr = np.array(magnitudes)
    relative_variation = (magnitudes_arr.max() - magnitudes_arr.min()) / magnitudes_arr.min()
    assert relative_variation > 1e-3
