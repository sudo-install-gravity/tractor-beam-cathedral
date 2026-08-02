"""Reproduction of ADR-0006's measured figures.

**Not the original spike.** ADR-0006 (2026-07-31) cited `scratchpad/spike_9_6.py`
and `spike_9_6b.py` as its prototypes, but `scratchpad/` was untracked until
2026-08-02 (SPIKE-4.5), so neither file was ever committed. Every number in
ADR-0006's "Context" and "Four traps" sections was therefore unreproducible
from this repository -- a real defect in a cathedral project that optimizes
for auditability (CLAUDE.md).

This script regenerates each figure using the actual production code
(`gwtb.array.focus`, `gwtb.array.beamform`, `gwtb.array.geometry`) and the same
12.4 km / 8x8 / 1250 m reference geometry already pinned in
`tests/unit/test_focused_field.py` and `tests/unit/test_focus.py`, so it is not
an independent re-derivation of the physics -- ADR-0003 and T-9.5/T-9.6 already
established that -- but a reproducibility check of ADR-0006's specific
numbers, which is what was missing.

Run with `.venv\\Scripts\\python.exe scratchpad\\spike_9_6.py`. Prints
CONFIRMED or MISMATCH for each figure and an overall verdict.
"""

from __future__ import annotations

import numpy as np

from gwtb.array.beamform import QuadrupoleElement, superpose_tt
from gwtb.array.focus import focal_phases
from gwtb.array.geometry import planar_array
from gwtb.core.constants import AU, c

_R = 40.0 * AU
_Q = np.array([[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 0.0]])

_FAILURES: list[str] = []


def rule(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def check(label: str, got: float, expected: float, rtol: float) -> None:
    ok = abs(got - expected) <= rtol * abs(expected)
    tag = "OK" if ok else "MISMATCH"
    print(f"  {label:<55} got={got:<16.6e} expected={expected:<12.4e} {tag}")
    if not ok:
        _FAILURES.append(f"{label}: got {got:.6e}, expected {expected:.4e} (rtol {rtol:.0e})")


def positions() -> np.ndarray:
    return planar_array(8, 8, 1250.0, 1250.0)


def elements() -> list[QuadrupoleElement]:
    return [QuadrupoleElement(position=p, quadrupole=_Q) for p in positions()]


# ---------------------------------------------------------------------------
# Geometry and the per-element angular spread ADR-0006 measures against
# ADR-0003's common-n_hat premise.
# ---------------------------------------------------------------------------


def check_geometry_and_angular_spread() -> None:
    rule("1. Reference geometry, per-element angular spread, and the margin")
    p = positions()
    centroid = p.mean(axis=0)
    max_offset = float(np.linalg.norm(p - centroid, axis=1).max())
    diameter = 2.0 * max_offset

    check("aperture diameter D (m)", diameter, 12374.4, rtol=1e-4)

    # ADR-0006: "max angle between per-element n_hat_a and the common n_hat"
    # at range R, i.e. arctan(max lateral offset / R).
    max_angle = float(np.arctan(max_offset / _R))
    check("max per-element angular spread (rad)", max_angle, 1.034e-9, rtol=1e-3)

    spin2_error = 2.0 * max_angle
    check("spin-2 polarization error 2*dtheta (rad)", spin2_error, 2.068e-9, rtol=1e-3)

    # ADR-0003's alignment budget for 1% gain loss.
    sigma_budget = 5.009e-2
    margin = sigma_budget / spin2_error
    check("margin vs ADR-0003's 5.009e-2 rad budget", margin, 2.4e7, rtol=2e-2)


# ---------------------------------------------------------------------------
# Trap 1: the reference aperture is sub-wavelength at the nominal drive freq.
# ---------------------------------------------------------------------------


def check_trap1_aperture_table() -> None:
    rule("2. Trap 1 -- D/lambda across frequency (sub-wavelength at 1 kHz)")
    p = positions()
    diameter = 2.0 * float(np.linalg.norm(p - p.mean(axis=0), axis=1).max())

    # ADR-0006 quotes these to 2-3 significant figures; 100 Hz (0.004) is
    # quoted to only 1 sig fig, so it needs a looser tolerance than the rest.
    table = {
        100.0: (0.004, 5e-2),
        1.0e3: (0.041, 2e-2),
        1.0e4: (0.413, 2e-2),
        1.0e5: (4.13, 2e-2),
        1.0e6: (41.3, 2e-2),
    }
    for freq, (expected, rtol) in table.items():
        wavelength = c / freq
        check(f"D/lambda at f={freq:.0e} Hz", diameter / wavelength, expected, rtol=rtol)

    # The vacuous-test demonstration: at 1 kHz every weighting returns N.
    els = elements()
    n = len(els)
    focal = np.array([0.0, 0.0, _R])
    wavelength_1khz = c / 1.0e3

    weights_uniform = np.ones(n, dtype=complex)
    weights_steered = np.exp(1j * focal_phases(positions(), np.array([1.0e3]), focal, 0.0)[:, 0])

    peak_uniform = float(np.abs(superpose_tt(els, weights_uniform, wavelength_1khz, focal)).max())
    peak_steered = float(np.abs(superpose_tt(els, weights_steered, wavelength_1khz, focal)).max())
    single = float(
        np.abs(superpose_tt([els[0]], np.array([1.0 + 0j]), wavelength_1khz, focal)).max()
    )

    print(
        f"\n  At 1 kHz: uniform weights give {peak_uniform / single:.3f}*A, "
        f"steered give {peak_steered / single:.3f}*A -- both ~= N={n} "
        "(vacuous, as ADR-0006 states)"
    )
    check(
        "uniform peak / single at 1kHz (== N, vacuous)", peak_uniform / single, float(n), rtol=1e-6
    )
    check(
        "steered peak / single at 1kHz (== N, vacuous)", peak_steered / single, float(n), rtol=1e-6
    )


# ---------------------------------------------------------------------------
# Trap 2: the sign convention table at 0 / 5 / 50 beamwidths off-axis.
# ---------------------------------------------------------------------------


def check_trap2_sign_convention_table() -> None:
    rule("3. Trap 2 -- exp(+i*phi) vs exp(-i*phi) at 0/5/50 beamwidths off-axis")
    els = elements()
    n = len(els)
    freq = 1.0e6  # ADR-0006's test frequency, D/lambda = 41.3
    wavelength = c / freq
    p = positions()
    diameter = 2.0 * float(np.linalg.norm(p - p.mean(axis=0), axis=1).max())
    beamwidth = wavelength / diameter  # rad

    single = float(
        np.abs(superpose_tt([els[0]], np.array([1.0 + 0j]), wavelength, [0, 0, _R])).max()
    )

    expected = {
        0.0: (64.000, 64.000, 64.000),
        5.0: (63.537, 63.485, 0.282),
        50.0: (44.969, 5.677, 6.851),
    }
    print(f"  {'beamwidths':>10} {'exp(+i phi)':>14} {'exp(-i phi)':>14} {'unsteered':>12}")
    for bw, (exp_plus, exp_minus, exp_unsteered) in expected.items():
        offset = bw * beamwidth * _R
        focal = np.array([offset, 0.0, _R])

        phi = focal_phases(p, np.array([freq]), focal, 0.0)[:, 0]
        plus = float(np.abs(superpose_tt(els, np.exp(1j * phi), wavelength, focal)).max()) / single
        minus = (
            float(np.abs(superpose_tt(els, np.exp(-1j * phi), wavelength, focal)).max()) / single
        )
        unsteered = (
            float(np.abs(superpose_tt(els, np.ones(n, dtype=complex), wavelength, focal)).max())
            / single
        )

        print(f"  {bw:>10.0f} {plus:>14.3f} {minus:>14.3f} {unsteered:>12.3f}")
        check(f"  exp(+i phi) at {bw:.0f} bw", plus, exp_plus, rtol=2e-3)
        check(f"  exp(-i phi) at {bw:.0f} bw", minus, exp_minus, rtol=2e-3)
        check(f"  unsteered at {bw:.0f} bw", unsteered, exp_unsteered, rtol=5e-2)

    print(
        "\n  confirms: exp(+i phi) matches superpose_tt's exp(+i k.r_n) convention; "
        "the two signs are indistinguishable near broadside and diverge only at "
        "tens of beamwidths off-axis"
    )


# ---------------------------------------------------------------------------
# Trap 4: the random-phase background is Rayleigh(sqrt(N*pi)/2), not sqrt(N).
# ---------------------------------------------------------------------------


def check_trap4_rayleigh_background() -> None:
    rule("4. Trap 4 -- random-phase background is sqrt(N*pi)/2, not sqrt(N)")
    els = elements()
    n = len(els)
    freq = 1.0e6
    wavelength = c / freq
    focal = np.array([0.0, 0.0, _R])
    single = float(np.abs(superpose_tt([els[0]], np.array([1.0 + 0j]), wavelength, focal)).max())

    peak = (
        float(np.abs(superpose_tt(els, np.ones(n, dtype=complex), wavelength, focal)).max())
        / single
    )
    # Peak with all elements in phase, unsteered at broadside -- should be N.
    check("peak (unsteered, broadside) / single (== N)", peak, float(n), rtol=1e-9)

    rng = np.random.default_rng(0)
    trials = 2000
    background = np.array(
        [
            float(
                np.abs(
                    superpose_tt(els, np.exp(1j * rng.uniform(0, 2 * np.pi, n)), wavelength, focal)
                ).max()
            )
            / single
            for _ in range(trials)
        ]
    ).mean()

    rayleigh = np.sqrt(n * np.pi) / 2.0
    naive = np.sqrt(n)
    print(f"\n  measured background mean over {trials} trials: {background:.4f}")
    print(f"  sqrt(N*pi)/2 = {rayleigh:.4f}   naive sqrt(N) = {naive:.4f}")
    check("background mean vs Rayleigh sqrt(N*pi)/2", background, rayleigh, rtol=0.03)

    ratio = peak / background
    # ADR-0006 itself distinguishes "close to sqrt(N)" from its own measured
    # value: "measured 8.75 vs 8.00" naive. Check against the ADR's own figure,
    # not the naive sqrt(N) -- that distinction IS trap 4's point.
    check("peak-to-background ratio (ADR measured 8.75)", ratio, 8.75, rtol=0.1)
    print(f"  (naive sqrt(N) = {naive:.3f}; ratio does scale as sqrt(N), not equal it)")


# ---------------------------------------------------------------------------
# Fraunhofer margin at 40 AU / 1 MHz.
# ---------------------------------------------------------------------------


def check_fraunhofer_margin() -> None:
    rule("5. Far-field margin at 40 AU, 1 MHz")
    p = positions()
    diameter = 2.0 * float(np.linalg.norm(p - p.mean(axis=0), axis=1).max())
    freq = 1.0e6
    wavelength = c / freq
    r_fraunhofer = 2.0 * diameter**2 / wavelength
    check("Fraunhofer distance (m)", r_fraunhofer, 1.0e6, rtol=5e-2)
    check("R / R_Fraunhofer at 40 AU", _R / r_fraunhofer, 5.9e6, rtol=2e-2)

    wavefront_sag = diameter**2 / (8.0 * _R)  # standard parabolic sag ~ D^2/(8R)
    print(f"\n  wavefront sag D^2/(8R) = {wavefront_sag:.3e} m  (ADR-0006 says ~3.20e-6 m)")
    check("wavefront sag (m)", wavefront_sag, 3.20e-6, rtol=0.5)


if __name__ == "__main__":
    check_geometry_and_angular_spread()
    check_trap1_aperture_table()
    check_trap2_sign_convention_table()
    check_trap4_rayleigh_background()
    check_fraunhofer_margin()

    rule("VERDICT")
    if _FAILURES:
        print(f"  MISMATCH -- {len(_FAILURES)} figure(s) did not reproduce:")
        for f in _FAILURES:
            print(f"    - {f}")
        print(
            "\n  Per CLAUDE.md rule 8, do not adjust ADR-0006's numbers to match. "
            "Record the discrepancy in docs/INDEX.md's assumption ledger and "
            "annotate the ADR instead."
        )
    else:
        print("  CONFIRMED -- every ADR-0006 figure checked here reproduces from")
        print("  the current production code within its stated tolerance.")
