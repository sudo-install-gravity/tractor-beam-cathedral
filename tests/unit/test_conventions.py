"""ADR-0002 convention-enforcement tests (T-2.10).

Every public function in ``bodies/``, ``propagate/``, and ``source/`` that
takes an array-like argument must reject a wrongly-shaped input and a
float32 input (rather than upcasting), per ADR-0002 §5 and §8. This module
exercises each one directly rather than relying on incidental coverage from
other test files, so a future change that accidentally routes around
``gwtb.core.validation`` is caught here specifically.

Functions taking **only scalar** arguments (no array-like parameter) have no
shape/dtype contract to enforce and are out of scope for this file by
construction — listed explicitly below rather than silently omitted, per
CLAUDE.md's "make absence loud" rule:

- ``gwtb.bodies.sphere.Sphere`` (radius, density: scalars)
- ``gwtb.bodies.sphere.Sphere.mass`` / ``.moment_of_inertia`` (no arguments)
- ``gwtb.bodies.sphere.Sphere.self_quadrupole`` / ``.degeneracy_warning`` (no arguments)
- ``gwtb.bodies.sphere.oblateness_quadrupole`` (sphere, spin_rate: scalar)
- ``gwtb.source.conservation.ConservationReport`` (plain data container, not a
  validating constructor)
"""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.bodies.multipole import (
    octupole_moment,
    quadrupole_moment,
    quadrupole_second_derivative,
    quadrupole_third_derivative,
)
from gwtb.bodies.sphere import Sphere
from gwtb.kinematics.profiles import QuinticProfile
from gwtb.propagate.retarded import PointSource, field_at
from gwtb.propagate.tt_projection import apply_tt, transverse_projector, tt_projector
from gwtb.source.conservation import audit
from gwtb.source.multipole_rad import dipole_moment, dipole_second_derivative
from gwtb.source.quadrupole import luminosity, strain_tt, waveform_from_profile

# --- Shared fixtures ---------------------------------------------------------

MASSES = np.array([1.0, 2.0])
POSITIONS = np.array([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]])
VELOCITIES = np.array([[0.0, 1.0, 0.0], [0.0, -1.0, 0.0]])
ACCELERATIONS = np.array([[0.0, 0.0, 1.0], [0.0, 0.0, -1.0]])
JERKS = np.array([[1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]])
N_HAT = np.array([0.0, 0.0, 1.0])
TENSOR = np.diag([1.0, -0.5, -0.5])
WRONG_SHAPE_VEC = np.array([1.0, 2.0])  # not (3,)
WRONG_SHAPE_TENSOR = np.eye(2)  # not (3, 3)


def _f32(arr: np.ndarray) -> np.ndarray:
    return arr.astype(np.float32)


# --- bodies/multipole.py ------------------------------------------------------


@pytest.mark.parametrize(
    "func,args",
    [
        (quadrupole_moment, (MASSES, POSITIONS)),
        (octupole_moment, (MASSES, POSITIONS)),
    ],
)
def test_bodies_multipole_two_arg_rejects_bad_shape_and_dtype(func, args) -> None:
    masses, positions = args
    with pytest.raises(ValueError):
        func(masses, WRONG_SHAPE_VEC)
    with pytest.raises(TypeError):
        func(_f32(masses), positions)


def test_quadrupole_second_derivative_rejects_bad_shape_and_dtype() -> None:
    with pytest.raises(ValueError):
        quadrupole_second_derivative(MASSES, WRONG_SHAPE_VEC, VELOCITIES, ACCELERATIONS)
    with pytest.raises(TypeError):
        quadrupole_second_derivative(_f32(MASSES), POSITIONS, VELOCITIES, ACCELERATIONS)


def test_quadrupole_third_derivative_rejects_bad_shape_and_dtype() -> None:
    with pytest.raises(ValueError):
        quadrupole_third_derivative(MASSES, WRONG_SHAPE_VEC, VELOCITIES, ACCELERATIONS, JERKS)
    with pytest.raises(TypeError):
        quadrupole_third_derivative(_f32(MASSES), POSITIONS, VELOCITIES, ACCELERATIONS, JERKS)


# --- propagate/tt_projection.py -----------------------------------------------


def test_transverse_projector_rejects_bad_shape_and_dtype() -> None:
    with pytest.raises(ValueError):
        transverse_projector(WRONG_SHAPE_VEC)
    with pytest.raises(TypeError):
        transverse_projector(_f32(N_HAT))


def test_tt_projector_rejects_bad_shape_and_dtype() -> None:
    with pytest.raises(ValueError):
        tt_projector(WRONG_SHAPE_VEC)
    with pytest.raises(TypeError):
        tt_projector(_f32(N_HAT))


def test_apply_tt_rejects_bad_shape_and_dtype() -> None:
    with pytest.raises(ValueError):
        apply_tt(WRONG_SHAPE_TENSOR, N_HAT)
    with pytest.raises(TypeError):
        apply_tt(_f32(TENSOR), N_HAT)


# --- propagate/retarded.py -----------------------------------------------------


def test_point_source_rejects_bad_position_shape() -> None:
    with pytest.raises(ValueError):
        PointSource(position=WRONG_SHAPE_VEC, q_ddot=lambda t: TENSOR)


def test_field_at_rejects_bad_shape_and_dtype() -> None:
    source = PointSource(position=np.zeros(3), q_ddot=lambda t: TENSOR)
    with pytest.raises(ValueError):
        field_at([source], WRONG_SHAPE_VEC, 0.0)
    with pytest.raises(TypeError):
        field_at([source], _f32(N_HAT * 1e10), 0.0)


# --- source/multipole_rad.py ---------------------------------------------------


def test_dipole_moment_rejects_bad_shape_and_dtype() -> None:
    with pytest.raises(ValueError):
        dipole_moment(MASSES, WRONG_SHAPE_VEC)
    with pytest.raises(TypeError):
        dipole_moment(_f32(MASSES), POSITIONS)


def test_dipole_second_derivative_rejects_bad_shape_and_dtype() -> None:
    with pytest.raises(ValueError):
        dipole_second_derivative(MASSES, WRONG_SHAPE_VEC)
    with pytest.raises(TypeError):
        dipole_second_derivative(_f32(MASSES), ACCELERATIONS)


# --- source/conservation.py -----------------------------------------------------


def test_audit_rejects_bad_shape_and_dtype() -> None:
    with pytest.raises(ValueError):
        audit(MASSES, WRONG_SHAPE_VEC)
    with pytest.raises(TypeError):
        audit(_f32(MASSES), ACCELERATIONS)


# --- source/quadrupole.py --------------------------------------------------------


def test_strain_tt_rejects_bad_shape_and_dtype() -> None:
    with pytest.raises(ValueError):
        strain_tt(WRONG_SHAPE_TENSOR, 1.0, N_HAT)
    with pytest.raises(TypeError):
        strain_tt(_f32(TENSOR), 1.0, N_HAT)


def test_luminosity_rejects_bad_shape_and_dtype() -> None:
    with pytest.raises(ValueError):
        luminosity(WRONG_SHAPE_TENSOR)
    with pytest.raises(TypeError):
        luminosity(_f32(TENSOR))


def test_waveform_from_profile_rejects_bad_shape_and_dtype() -> None:
    body = Sphere(radius=1.0, density=1000.0)
    profile = QuinticProfile(delta_v=1.0, duration=1.0)
    with pytest.raises(ValueError):
        waveform_from_profile(body, profile, r=1e10, n_hat=WRONG_SHAPE_VEC, times=[0.0])
    with pytest.raises(TypeError):
        waveform_from_profile(body, profile, r=1e10, n_hat=_f32(N_HAT), times=[0.0])
