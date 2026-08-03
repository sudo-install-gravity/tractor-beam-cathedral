"""Unit tests for the spin-2 extension: superpose_tt and mismatch_loss (T-6.5, T-6.6).

These guard the project's highest-risk bug class. The assertions that matter are
the ones that would pass under a spin-1 implementation and must not:

* elements 45 degrees apart are polarization-orthogonal (EM needs 90)
* elements 90 degrees apart **cancel** (EM predicts 2x power)
* the mismatch factor has period pi, not 2 pi

Predictions come from docs/adr/0003-spin2-superposition.md.
"""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.array.beamform import QuadrupoleElement, array_factor, mismatch_loss, superpose_tt

N_HAT = np.array([0.0, 0.0, 1.0])
WAVELENGTH = 1.0
FAR = np.array([0.0, 0.0, 1.0e6])


def _linear_quadrupole(psi: float) -> np.ndarray:
    """Trace-free quadrupole of a linear oscillator at angle ``psi`` in the xy-plane."""
    u = np.array([np.cos(psi), np.sin(psi), 0.0])
    return np.outer(u, u) - np.eye(3) / 3.0


def _axis(psi: float) -> np.ndarray:
    return np.array([np.cos(psi), np.sin(psi), 0.0])


def _pol(h: np.ndarray) -> np.ndarray:
    """(h_plus, h_cross) for observation along z."""
    return np.array([0.5 * (h[0, 0] - h[1, 1]), h[0, 1]])


# --- T-6.5: reduction to the scalar baseline ---------------------------------


def test_co_oriented_elements_reduce_to_scalar_array_factor() -> None:
    """AC: reduces to the scalar array factor for co-oriented elements, rtol 1e-9.

    This is the regression check ADR-0003 requires: it proves the spin-2 case is
    a controlled *departure* from the known-good scalar baseline rather than an
    unrelated rewrite.
    """
    rng = np.random.default_rng(20260727)
    q = _linear_quadrupole(0.3)
    positions = rng.normal(scale=5.0, size=(6, 3))
    # Centre the geometry: superpose_tt takes n_hat from the array CENTROID to
    # the field point, so an off-centre array tilts the observation direction
    # away from z and this comparison would be against the wrong direction.
    positions -= positions.mean(axis=0)
    weights = rng.normal(size=6) + 1j * rng.normal(size=6)

    elements = [QuadrupoleElement(position=p, quadrupole=q) for p in positions]
    total = superpose_tt(elements, weights, WAVELENGTH, FAR)

    # Co-oriented: the sum factorizes into (common TT tensor) x (scalar AF).
    from gwtb.propagate.tt_projection import apply_tt

    af = array_factor(positions, weights, WAVELENGTH, N_HAT)
    expected = apply_tt(q, N_HAT) * af
    np.testing.assert_allclose(total, expected, rtol=1e-9, atol=1e-15)


def test_result_is_symmetric_traceless_and_transverse() -> None:
    q = _linear_quadrupole(0.7)
    # Centred on the origin so the observation direction is exactly z.
    els = [
        QuadrupoleElement(position=np.array([float(i) - 1.5, 0.0, 0.0]), quadrupole=q)
        for i in range(4)
    ]
    h = superpose_tt(els, np.ones(4), WAVELENGTH, FAR)
    np.testing.assert_allclose(h, h.T, atol=1e-15)
    assert abs(np.trace(h)) < 1e-12
    assert np.abs(N_HAT @ h).max() < 1e-12


# --- T-6.5: the spin-2 departure ---------------------------------------------


def test_orthogonally_oriented_elements_give_gain_below_n_squared() -> None:
    """AC: for orthogonally-oriented elements, gain is strictly less than N^2."""
    origin = np.zeros(3)
    single = (
        np.linalg.norm(
            _pol(
                superpose_tt(
                    [QuadrupoleElement(position=origin, quadrupole=_linear_quadrupole(0.0))],
                    [1.0],
                    WAVELENGTH,
                    FAR,
                )
            )
        )
        ** 2
    )

    pair = [
        QuadrupoleElement(position=origin, quadrupole=_linear_quadrupole(0.0)),
        QuadrupoleElement(position=origin, quadrupole=_linear_quadrupole(np.pi / 4)),
    ]
    gain = np.linalg.norm(_pol(superpose_tt(pair, np.ones(2), WAVELENGTH, FAR))) ** 2 / single
    assert gain < 4.0
    assert gain == pytest.approx(2.0, abs=1e-9), "45 deg apart => orthogonal, power adds"


def test_elements_ninety_degrees_apart_cancel_completely() -> None:
    """The trap. Spin-1 intuition predicts orthogonality and 2x power here.

    An array laid out on antenna reasoning with elements at 90 degrees radiates
    NOTHING along its intended axis. Asserted explicitly so nobody "fixes" it.
    """
    origin = np.zeros(3)
    pair = [
        QuadrupoleElement(position=origin, quadrupole=_linear_quadrupole(0.0)),
        QuadrupoleElement(position=origin, quadrupole=_linear_quadrupole(np.pi / 2)),
    ]
    h = superpose_tt(pair, np.ones(2), WAVELENGTH, FAR)
    assert np.abs(h).max() < 1e-15, "90-degree elements must cancel, not add"


def test_near_field_raises_rather_than_degrading_quietly() -> None:
    """Superposing TT tensors needs a common direction; inside the near field
    that assumption fails, and ADR-0003 makes it a reversal condition."""
    q = _linear_quadrupole(0.0)
    els = [
        QuadrupoleElement(position=np.array([-50.0, 0.0, 0.0]), quadrupole=q),
        QuadrupoleElement(position=np.array([50.0, 0.0, 0.0]), quadrupole=q),
    ]
    with pytest.raises(ValueError, match="near field"):
        superpose_tt(els, np.ones(2), WAVELENGTH, np.array([0.0, 0.0, 100.0]))


def test_rejects_bad_inputs() -> None:
    q = _linear_quadrupole(0.0)
    el = [QuadrupoleElement(position=np.zeros(3), quadrupole=q)]
    with pytest.raises(ValueError):
        superpose_tt([], [], WAVELENGTH, FAR)
    with pytest.raises(ValueError):
        superpose_tt(el, [1.0, 2.0], WAVELENGTH, FAR)
    with pytest.raises(ValueError):
        superpose_tt(el, [1.0], -1.0, FAR)


# --- T-6.6: mismatch loss ------------------------------------------------------


@pytest.mark.parametrize(
    ("deg", "expected"),
    [(0, 1.0), (22.5, np.cos(np.pi / 4)), (30, 0.5), (45, 0.0), (60, -0.5), (90, -1.0), (180, 1.0)],
)
def test_mismatch_follows_cos_two_delta_psi(deg: float, expected: float) -> None:
    """AC: cos(2 dpsi), not cos(dpsi)."""
    got = mismatch_loss(_axis(0.0), _axis(np.radians(deg)), N_HAT)
    assert got == pytest.approx(expected, abs=1e-12)


def test_zero_loss_for_identical_orientations() -> None:
    for deg in (0, 17, 40, 88):
        u = _axis(np.radians(deg))
        assert mismatch_loss(u, u, N_HAT) == pytest.approx(1.0, abs=1e-12)


def test_maximal_mismatch_at_45_not_90() -> None:
    """The single most important assertion in this file.

    Orthogonality arrives at 45 degrees for a spin-2 field. A spin-1
    implementation puts it at 90, and every number it produces looks reasonable.
    """
    assert abs(mismatch_loss(_axis(0.0), _axis(np.pi / 4), N_HAT)) < 1e-12
    assert abs(mismatch_loss(_axis(0.0), _axis(np.pi / 2), N_HAT)) == pytest.approx(1.0, abs=1e-12)


def test_period_is_pi_not_two_pi() -> None:
    for deg in (13, 37, 61):
        base = mismatch_loss(_axis(0.0), _axis(np.radians(deg)), N_HAT)
        shifted = mismatch_loss(_axis(0.0), _axis(np.radians(deg) + np.pi), N_HAT)
        assert shifted == pytest.approx(base, abs=1e-12)


def test_mismatch_is_symmetric_and_bounded() -> None:
    rng = np.random.default_rng(7)
    for _ in range(30):
        a, b = _axis(rng.uniform(0, np.pi)), _axis(rng.uniform(0, np.pi))
        ab, ba = mismatch_loss(a, b, N_HAT), mismatch_loss(b, a, N_HAT)
        assert ab == pytest.approx(ba, abs=1e-12)
        assert -1.0 - 1e-12 <= ab <= 1.0 + 1e-12


def test_orientation_along_line_of_sight_raises() -> None:
    """A linear element radiates nothing along its own axis, so coupling is undefined."""
    with pytest.raises(ValueError, match="parallel to n_hat"):
        mismatch_loss(N_HAT, _axis(0.0), N_HAT)


_ALIGN_N = 200
_ALIGN_REALIZATIONS = 50_000
_ALIGN_SEED = 20260727
#: The tolerance is STATISTICAL, not a fixed absolute: each assertion allows
#: `_ALIGN_SIGMAS` standard errors of the estimator's own sampling distribution,
#: computed from the sample itself.
#:
#: A flat absolute tolerance was tried first and is the wrong tool here. The
#: estimator's standard error grows steeply with sigma (4.5e-6 at 2.87 deg but
#: 1.4e-4 at 20 deg, a 30x span), so any single number is either far too loose at
#: small sigma or below one standard error at large sigma. A flat abs=1e-4 sat at
#: 0.7 SE at sigma=20 deg and failed on 13 of 30 reseeds while passing on the
#: committed seed -- a coin flip dressed as a margin. Do not reintroduce one.
#:
#: At 5 SE every parametrized point still rejects the uncorrected law by 2.2-2.8x,
#: so the 1/N bias term is load-bearing at ALL four sigmas, not just the large ones.
_ALIGN_SIGMAS = 5.0


def _asymptotic_law(sigma_rad: float) -> float:
    """ADR-0003's alignment law -- the N -> infinity limit."""
    return float(np.exp(-4 * sigma_rad**2))


def _finite_n_prediction(sigma_rad: float, n_elements: int) -> float:
    """ADR-0003 as amended 2026-08-03: the law plus its exact finite-N bias.

    E[gain/N^2] = exp(-4 sigma^2) + (1 - exp(-4 sigma^2)) / N

    The second term is the |z|^2 = 1 self-term of |sum_n exp(2 i psi_n)|^2. It
    cannot vanish, and divided by N^2 it leaves a positive 1/N floor.
    """
    asymptotic = _asymptotic_law(sigma_rad)
    return asymptotic + (1.0 - asymptotic) / n_elements


def _measure_gain_fraction(
    sigma_deg: float, n_elements: int, n_real: int, seed: int
) -> tuple[float, float]:
    """Mean gain fraction, and the standard error of that mean.

    Returning the standard error is what lets every assertion below size its own
    tolerance from the estimator's actual sampling distribution instead of from a
    hardcoded number that happens to suit one seed.
    """
    rng = np.random.default_rng(seed)
    psi = rng.normal(0.0, np.radians(sigma_deg), size=(n_real, n_elements))
    c = np.cos(2 * psi).sum(axis=1)
    d = np.sin(2 * psi).sum(axis=1)
    gains = (c * c + d * d) / n_elements**2
    return float(gains.mean()), float(gains.std(ddof=1) / np.sqrt(n_real))


@pytest.mark.parametrize("sigma_deg", [2.87, 5.0, 10.0, 20.0])
def test_alignment_tolerance_matches_adr_prediction(sigma_deg: float) -> None:
    """ADR-0003 (amended 2026-08-03): gain/N^2 = exp(-4 sigma^2) + (1-exp(-4 sigma^2))/N.

    The bare exp(-4 sigma^2) is the N -> infinity limit. Asserting it directly at
    finite N forces a tolerance loose enough to swallow the bias -- which is what
    the previous abs=2e-3 was doing, and why it could not be tightened to the
    figure ADR-0003 originally claimed. Against the bias-corrected prediction the
    residual is pure sampling noise, so the tolerance can be stated in standard
    errors and the 1/N term becomes load-bearing (see the positive control below).
    """
    measured, sem = _measure_gain_fraction(sigma_deg, _ALIGN_N, _ALIGN_REALIZATIONS, _ALIGN_SEED)
    expected = _finite_n_prediction(np.radians(sigma_deg), _ALIGN_N)
    assert measured == pytest.approx(expected, abs=_ALIGN_SIGMAS * sem)


@pytest.mark.parametrize("sigma_deg", [2.87, 5.0, 10.0, 20.0])
def test_uncorrected_asymptotic_law_is_rejected_at_finite_n(sigma_deg: float) -> None:
    """Positive control: the 1/N bias term must be load-bearing, not decorative.

    Dropping it puts the prediction 2.2-2.8x outside the tolerance at EVERY sigma
    tested -- the whole point of sizing the tolerance in standard errors rather
    than absolutely, since the bias and the noise both scale with sigma and a flat
    tolerance loses discrimination at exactly one end or the other.

    This is what stops a future contributor "simplifying" `_finite_n_prediction`
    back to the bare law.
    """
    measured, sem = _measure_gain_fraction(sigma_deg, _ALIGN_N, _ALIGN_REALIZATIONS, _ALIGN_SEED)
    bare_law = _asymptotic_law(np.radians(sigma_deg))
    tol = _ALIGN_SIGMAS * sem

    assert abs(measured - bare_law) > tol, (
        f"the uncorrected law must be rejected at sigma={sigma_deg} deg, "
        "or the 1/N bias term is untested here"
    )
    # And the departure IS the predicted bias, not an arbitrary disagreement.
    predicted_bias = (1.0 - bare_law) / _ALIGN_N
    assert (measured - bare_law) == pytest.approx(predicted_bias, abs=tol)


def test_one_percent_loss_at_2_87_degrees_is_an_asymptotic_statement() -> None:
    """Guard the headline engineering number against silent drift.

    NOTE: this pins a closed-form identity, not a simulation -- it validates no
    new numerics and should not be credited as physics evidence. Its job is to
    make 2.87 deg (and the spin-1 5.73 deg it is exactly 2x tighter than) fail
    loudly if anyone edits the law, since those two numbers are quoted in
    ADR-0003, CLAIMS.md B-1 and the paper draft.

    Stated for the asymptotic law deliberately: at finite N the measured loss is
    smaller, because the bias works in the optimistic direction.
    """
    assert _asymptotic_law(np.radians(2.87)) == pytest.approx(0.99, abs=5e-5)
    # Spin-1 would be exp(-sigma^2); 1% loss there needs 5.73 deg, twice as loose.
    assert float(np.exp(-(np.radians(5.73) ** 2))) == pytest.approx(0.99, abs=5e-5)
