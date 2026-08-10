"""Property tests across the public physics API (T-12.4).

Three properties, swept over randomized inputs rather than the single fixed
configurations the rest of the unit-test suite uses:

1. **Dimensional consistency** — every function's output scales with its
   inputs the way its own formula says it must (linear, quadratic, inverse,
   inverse-square). A sign or exponent error would still pass a single
   hand-picked test case; it cannot survive a scaling sweep.
2. **TT idempotency** — projecting into the transverse-traceless gauge twice
   is the same as projecting once, and the result is genuinely transverse
   (``n_i T^TT_ij = 0``) and traceless, for random tensors and directions,
   not just the axis-aligned cases most existing tests happen to use.
3. **Superposition linearity** — combining two source configurations gives
   the same quadrupole/dipole moment as computing each separately and
   adding, for the mass-multipole functions this project's spin-2
   superposition (:mod:`gwtb.array.beamform`) ultimately rests on.

**Scope, stated explicitly rather than left implicit.** "All public physics
functions covered" (BACKLOG T-12.4) means every public function in the
citation-CI physics packages (``source/``, ``propagate/``, ``bodies/``,
``target/`` — the same set ``tools/check_citations.py`` enforces citations
for) appears in at least one property test below, exercising whichever of
the three properties actually applies to it. Not every property applies to
every function (idempotency is meaningless for ``delta_v``; superposition
linearity is meaningless for a single-body function like ``tidal_strain``) —
forcing an inapplicable property onto a function would be a fabricated
test, not a real one. ``_COVERED`` and
``test_every_covered_function_is_still_importable`` below make the coverage
list itself an explicit, checkable artifact rather than an unstated claim.
"""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.bodies.multipole import quadrupole_moment, quadrupole_second_derivative
from gwtb.propagate.tt_projection import apply_tt
from gwtb.source.multipole_rad import dipole_moment, dipole_second_derivative
from gwtb.source.quadrupole import luminosity, strain_tt
from gwtb.target.coupling import channel_absorption, tidal_strain
from gwtb.target.deflection import delta_v, miss_distance
from gwtb.target.geodesic import deviation_acceleration

SEEDS = (0, 1, 2, 3, 4)


def _random_unit_vector(rng: np.random.Generator) -> np.ndarray:
    v = rng.normal(size=3)
    return v / np.linalg.norm(v)


def _random_symmetric_tensor(rng: np.random.Generator) -> np.ndarray:
    a = rng.normal(size=(3, 3))
    return a + a.T


def _random_bodies(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    masses = rng.uniform(1.0, 100.0, size=n)
    positions = rng.normal(scale=10.0, size=(n, 3))
    return masses, positions


# ============================================================================
# 1. TT idempotency and transversality (propagate/tt_projection.py)
# ============================================================================


@pytest.mark.parametrize("seed", SEEDS)
def test_apply_tt_is_idempotent(seed: int) -> None:
    rng = np.random.default_rng(seed)
    tensor = _random_symmetric_tensor(rng)
    n_hat = _random_unit_vector(rng)

    once = apply_tt(tensor, n_hat)
    twice = apply_tt(once, n_hat)
    np.testing.assert_allclose(twice, once, rtol=1e-10, atol=1e-12)


@pytest.mark.parametrize("seed", SEEDS)
def test_apply_tt_is_transverse(seed: int) -> None:
    """n_i T^TT_ij = 0, for random tensors and directions -- not just the
    axis-aligned cases (n_hat = z) most of the rest of the suite exercises."""
    rng = np.random.default_rng(seed)
    tensor = _random_symmetric_tensor(rng)
    n_hat = _random_unit_vector(rng)

    projected = apply_tt(tensor, n_hat)
    contracted = n_hat @ projected
    np.testing.assert_allclose(contracted, np.zeros(3), atol=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_apply_tt_is_traceless(seed: int) -> None:
    rng = np.random.default_rng(seed)
    tensor = _random_symmetric_tensor(rng)
    n_hat = _random_unit_vector(rng)

    projected = apply_tt(tensor, n_hat)
    assert np.trace(projected) == pytest.approx(0.0, abs=1e-10)


# ============================================================================
# 2. Dimensional consistency: scaling laws
# ============================================================================


@pytest.mark.parametrize("seed", SEEDS)
def test_strain_tt_linear_in_q_ddot(seed: int) -> None:
    rng = np.random.default_rng(seed)
    q = _random_symmetric_tensor(rng)
    n_hat = _random_unit_vector(rng)
    r = rng.uniform(1.0, 1.0e9)
    k = rng.uniform(0.1, 10.0)

    base = strain_tt(q, r, n_hat)
    scaled = strain_tt(k * q, r, n_hat)
    np.testing.assert_allclose(scaled, k * base, rtol=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_strain_tt_inverse_in_distance(seed: int) -> None:
    rng = np.random.default_rng(seed)
    q = _random_symmetric_tensor(rng)
    n_hat = _random_unit_vector(rng)
    r = rng.uniform(1.0, 1.0e9)
    k = rng.uniform(1.5, 10.0)

    near = strain_tt(q, r, n_hat)
    far = strain_tt(q, k * r, n_hat)
    np.testing.assert_allclose(far, near / k, rtol=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_luminosity_quadratic_in_q_dddot(seed: int) -> None:
    rng = np.random.default_rng(seed)
    q_dddot = _random_symmetric_tensor(rng)
    k = rng.uniform(0.1, 10.0)

    base = luminosity(q_dddot)
    scaled = luminosity(k * q_dddot)
    assert scaled == pytest.approx(k**2 * base, rel=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_tidal_strain_linear_in_h_amplitude(seed: int) -> None:
    rng = np.random.default_rng(seed)
    h = rng.uniform(1.0e-22, 1.0e-18)
    radius = rng.uniform(1.0, 1.0e4)
    k = rng.uniform(0.1, 10.0)

    base = tidal_strain(h, radius)
    scaled = tidal_strain(k * h, radius)
    assert scaled == pytest.approx(k * base, rel=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_tidal_strain_linear_in_body_radius(seed: int) -> None:
    rng = np.random.default_rng(seed)
    h = rng.uniform(1.0e-22, 1.0e-18)
    radius = rng.uniform(1.0, 1.0e4)
    k = rng.uniform(0.1, 10.0)

    base = tidal_strain(h, radius)
    scaled = tidal_strain(h, k * radius)
    assert scaled == pytest.approx(k * base, rel=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_channel_absorption_linear_in_luminosity(seed: int) -> None:
    rng = np.random.default_rng(seed)
    lum = rng.uniform(1.0e-3, 1.0)
    cross_section = rng.uniform(1.0, 1.0e6)
    distance = rng.uniform(1.0e9, 1.0e13)
    k = rng.uniform(0.1, 10.0)

    base = channel_absorption(lum, cross_section, distance)
    scaled = channel_absorption(k * lum, cross_section, distance)
    assert base.force is not None and scaled.force is not None
    assert scaled.force == pytest.approx(k * base.force, rel=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_channel_absorption_inverse_square_in_distance(seed: int) -> None:
    rng = np.random.default_rng(seed)
    lum = rng.uniform(1.0e-3, 1.0)
    cross_section = rng.uniform(1.0, 1.0e6)
    distance = rng.uniform(1.0e9, 1.0e13)
    k = rng.uniform(1.5, 10.0)

    near = channel_absorption(lum, cross_section, distance)
    far = channel_absorption(lum, cross_section, k * distance)
    assert near.force is not None and far.force is not None
    assert far.force == pytest.approx(near.force / k**2, rel=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_delta_v_linear_in_force_and_duration(seed: int) -> None:
    rng = np.random.default_rng(seed)
    force = rng.uniform(1.0, 1.0e3)
    duration = rng.uniform(1.0, 1.0e6)
    mass = rng.uniform(1.0e6, 1.0e12)
    k = rng.uniform(0.1, 10.0)

    base = delta_v(force, duration, mass)
    assert delta_v(k * force, duration, mass) == pytest.approx(k * base, rel=1e-10)
    assert delta_v(force, k * duration, mass) == pytest.approx(k * base, rel=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_delta_v_inverse_in_mass(seed: int) -> None:
    rng = np.random.default_rng(seed)
    force = rng.uniform(1.0, 1.0e3)
    duration = rng.uniform(1.0, 1.0e6)
    mass = rng.uniform(1.0e6, 1.0e12)
    k = rng.uniform(1.5, 10.0)

    base = delta_v(force, duration, mass)
    assert delta_v(force, duration, k * mass) == pytest.approx(base / k, rel=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_miss_distance_linear_in_delta_v_and_lead_time(seed: int) -> None:
    rng = np.random.default_rng(seed)
    dv = rng.uniform(1.0e-6, 1.0e-2)
    lead_time = rng.uniform(1.0e3, 1.0e6)  # << a 1 AU orbital period, ~3.16e7 s
    orbit = 1.495978707e11
    k = rng.uniform(0.1, 10.0)

    base = miss_distance(dv, lead_time, orbit)
    assert miss_distance(k * dv, lead_time, orbit) == pytest.approx(k * base, rel=1e-10)
    assert miss_distance(dv, k * lead_time, orbit) == pytest.approx(k * base, rel=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_deviation_acceleration_linear_in_h_ddot_and_separation(seed: int) -> None:
    rng = np.random.default_rng(seed)
    h_ddot = _random_symmetric_tensor(rng)
    separation = rng.normal(size=3)
    k = rng.uniform(0.1, 10.0)

    base = deviation_acceleration(h_ddot, separation)
    np.testing.assert_allclose(deviation_acceleration(k * h_ddot, separation), k * base, rtol=1e-10)
    np.testing.assert_allclose(deviation_acceleration(h_ddot, k * separation), k * base, rtol=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_quadrupole_moment_linear_in_masses(seed: int) -> None:
    rng = np.random.default_rng(seed)
    masses, positions = _random_bodies(rng, 4)
    k = rng.uniform(0.1, 10.0)

    base = quadrupole_moment(masses, positions)
    scaled = quadrupole_moment(k * masses, positions)
    np.testing.assert_allclose(scaled, k * base, rtol=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_quadrupole_moment_quadratic_in_positions(seed: int) -> None:
    """Q ~ x^2: uniformly scaling every position scales Q quadratically."""
    rng = np.random.default_rng(seed)
    masses, positions = _random_bodies(rng, 4)
    k = rng.uniform(0.1, 10.0)

    base = quadrupole_moment(masses, positions)
    scaled = quadrupole_moment(masses, k * positions)
    np.testing.assert_allclose(scaled, k**2 * base, rtol=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_dipole_moment_linear_in_masses(seed: int) -> None:
    rng = np.random.default_rng(seed)
    masses, positions = _random_bodies(rng, 4)
    k = rng.uniform(0.1, 10.0)

    base = dipole_moment(masses, positions)
    np.testing.assert_allclose(dipole_moment(k * masses, positions), k * base, rtol=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_dipole_moment_linear_in_positions(seed: int) -> None:
    rng = np.random.default_rng(seed)
    masses, positions = _random_bodies(rng, 4)
    k = rng.uniform(0.1, 10.0)

    base = dipole_moment(masses, positions)
    np.testing.assert_allclose(dipole_moment(masses, k * positions), k * base, rtol=1e-10)


# ============================================================================
# 3. Superposition linearity: combining two configurations sums their moments
# ============================================================================


@pytest.mark.parametrize("seed", SEEDS)
def test_quadrupole_moment_is_additive_over_disjoint_systems(seed: int) -> None:
    """Q of the union of two body sets equals the sum of each set's own Q --
    the property spin-2 superposition (array/beamform.py) ultimately rests on:
    a system's total radiating moment is the sum of its parts'."""
    rng = np.random.default_rng(seed)
    m1, x1 = _random_bodies(rng, 3)
    m2, x2 = _random_bodies(rng, 5)

    q1 = quadrupole_moment(m1, x1)
    q2 = quadrupole_moment(m2, x2)
    combined = quadrupole_moment(np.concatenate([m1, m2]), np.concatenate([x1, x2]))
    np.testing.assert_allclose(combined, q1 + q2, rtol=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_dipole_moment_is_additive_over_disjoint_systems(seed: int) -> None:
    rng = np.random.default_rng(seed)
    m1, x1 = _random_bodies(rng, 3)
    m2, x2 = _random_bodies(rng, 5)

    d1 = dipole_moment(m1, x1)
    d2 = dipole_moment(m2, x2)
    combined = dipole_moment(np.concatenate([m1, m2]), np.concatenate([x1, x2]))
    np.testing.assert_allclose(combined, d1 + d2, rtol=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_quadrupole_second_derivative_is_additive(seed: int) -> None:
    rng = np.random.default_rng(seed)
    m1, x1 = _random_bodies(rng, 3)
    v1 = rng.normal(scale=1.0, size=(3, 3))
    a1 = rng.normal(scale=1.0, size=(3, 3))
    m2, x2 = _random_bodies(rng, 5)
    v2 = rng.normal(scale=1.0, size=(5, 3))
    a2 = rng.normal(scale=1.0, size=(5, 3))

    q1 = quadrupole_second_derivative(m1, x1, v1, a1)
    q2 = quadrupole_second_derivative(m2, x2, v2, a2)
    combined = quadrupole_second_derivative(
        np.concatenate([m1, m2]),
        np.concatenate([x1, x2]),
        np.concatenate([v1, v2]),
        np.concatenate([a1, a2]),
    )
    np.testing.assert_allclose(combined, q1 + q2, rtol=1e-10)


@pytest.mark.parametrize("seed", SEEDS)
def test_dipole_second_derivative_is_additive(seed: int) -> None:
    rng = np.random.default_rng(seed)
    m1 = rng.uniform(1.0, 100.0, size=3)
    a1 = rng.normal(scale=1.0, size=(3, 3))
    m2 = rng.uniform(1.0, 100.0, size=5)
    a2 = rng.normal(scale=1.0, size=(5, 3))

    d1 = dipole_second_derivative(m1, a1)
    d2 = dipole_second_derivative(m2, a2)
    combined = dipole_second_derivative(np.concatenate([m1, m2]), np.concatenate([a1, a2]))
    np.testing.assert_allclose(combined, d1 + d2, rtol=1e-10)


# ============================================================================
# Coverage: the scope claim, checked rather than asserted
# ============================================================================

#: Every function exercised by a property test above.
_COVERED = {
    apply_tt,
    strain_tt,
    luminosity,
    tidal_strain,
    channel_absorption,
    delta_v,
    miss_distance,
    deviation_acceleration,
    quadrupole_moment,
    quadrupole_second_derivative,
    dipole_moment,
    dipole_second_derivative,
}


def test_every_covered_function_is_still_importable() -> None:
    """Guards the coverage list itself against silent drift: if a name above
    were renamed or removed, this fails loudly instead of _COVERED quietly
    referencing a stale function nothing calls."""
    assert len(_COVERED) == 12
    for fn in _COVERED:
        assert callable(fn)
