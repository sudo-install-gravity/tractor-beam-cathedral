#!/usr/bin/env python3
"""End-to-end scenario (T-12.1): a 1 km asteroid at 40 AU, an N-element
phased array, a prime-band drive -- every stage of the framework, run once,
in order, start to finish.

    .venv\\Scripts\\python.exe examples\\deflection_scenario.py

This is a **demonstration**, not a campaign: it carries no pre-registered
falsifier and reports no verdict (contrast ``tools/run_campaign.py`, which
does both for the paper's Results section). Its only job is to show that the
full pipeline -- geometry, drive, spin-2 superposition, field evaluation,
coupling, deflection, and the feasibility ledger -- composes end to end
without a break in the chain, and to leave behind the artifacts a reader can
look at: two figures and a ledger table.

Physical configuration, chosen to match the paper's own reference numbers
rather than invent new ones (docs/paper/nature-draft.md; ``tools/run_campaign.py``):

- **Target:** a 1 km, 2.6 g/cm^3 stony asteroid (~1.4e12 kg) at 40 AU
  (``TARGET_RANGE``) -- the project's standing reference scenario.
- **Array:** an 8x8 planar array, 1250 m spacing -- the same geometry every
  R2-R6 campaign uses.
- **Drive:** the first 5 primes scaled to a 1 MHz band. Below ~100 kHz this
  aperture is sub-wavelength and has no beam at all (ADR-0006 trap 1); 1 MHz
  is the frequency every campaign in this project runs at for exactly that
  reason.
- **Achieved luminosity:** 7.5e-2 W, the same figure ``campaign_r6``/``campaign_r8``
  report as this array configuration's achievable output -- reused here
  rather than re-derived, so this script's numbers agree with the paper's.

Exit codes: 0 = the pipeline ran to completion and wrote its artifacts.
Non-zero if any stage raises -- this script does not catch and continue,
since a break anywhere in the chain is the finding, not the figures.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from gwtb.array.beamform import QuadrupoleElement, superpose_tt  # noqa: E402
from gwtb.array.geometry import planar_array  # noqa: E402
from gwtb.bodies.sphere import Sphere  # noqa: E402
from gwtb.core.constants import AU, G_OVER_C4, TARGET_RANGE, c  # noqa: E402
from gwtb.kinematics.oscillators import PrimeOscillatorDrive, first_n_primes  # noqa: E402
from gwtb.ledger.gap_report import GapReport, aperture_gap, impulse_gap  # noqa: E402
from gwtb.target.coupling import channel_absorption  # noqa: E402
from gwtb.target.deflection import delta_v, miss_distance  # noqa: E402
from gwtb.viz.patterns import plot_pattern_polar  # noqa: E402
from gwtb.viz.slices import FieldSlice, extract_slice, plot_strain_slice  # noqa: E402

OUTDIR = Path("examples/output")

# --- configuration (see module docstring for why these particular numbers) ---
ASTEROID = Sphere(radius=500.0, density=2600.0)  # ~1.4e12 kg, 1 km diameter
NX, NY, SPACING = 8, 8, 1250.0
BAND_HZ = 1.0e6  # 1 MHz: below ~100 kHz this aperture has no beam (ADR-0006)
N_TONES = 5
ACHIEVED_LUMINOSITY_W = 7.5e-2  # matches campaign_r6/r8's achieved value
#: 30 days: illustrative, and short enough that miss_distance's impulsive-limit
#: guard (lead_time << the ~1-year orbital period at 1 AU) is genuinely valid,
#: not just numerically accepted.
LEAD_TIME_S = 30.0 * 24.0 * 3600.0

#: A single canonical oscillation orientation, shared by every element: a
#: linear quadrupole along x (ADR-0003's analytic case, matching
#: tools/run_campaign.py's Q_LINEAR). Deliberately **token-scale** (1 kg m^2
#: s^-2 per element, matching the campaigns' own convention of using this
#: tensor for pattern/ratio measurements, never absolute magnitude). The
#: field figures below apply the correct `2*G/(c^4 r)` strain prefactor
#: (source/quadrupole.py:strain_tt) to this token magnitude, so their units
#: are genuinely dimensionless strain -- just an illustrative, not achieved,
#: one. The array's actual achieved output is the separately-cited
#: ACHIEVED_LUMINOSITY_W figure the coupling/deflection stages below use.
Q_ORIENTATION = np.array([[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 0.0]])


def build_array() -> list[QuadrupoleElement]:
    """The 8x8 planar array, every element co-oriented (ADR-0003's analytic case)."""
    positions = planar_array(NX, NY, SPACING, SPACING)
    return [QuadrupoleElement(position=p, quadrupole=Q_ORIENTATION) for p in positions]


def build_drive() -> PrimeOscillatorDrive:
    """The first 5 primes, scaled into the 1 MHz band."""
    primes = first_n_primes(N_TONES)
    frequencies = np.array(primes, dtype=np.float64) * BAND_HZ / primes[0]
    amplitudes = np.ones(N_TONES)
    phases = np.zeros(N_TONES)
    return PrimeOscillatorDrive(frequencies, amplitudes, phases, duration=1.0)


def field_at_target(elements: list[QuadrupoleElement], drive: PrimeOscillatorDrive) -> complex:
    """Illustrative TT strain phasor at the target, summed over every drive tone.

    ``superpose_tt`` returns its sum in the units of ``QuadrupoleElement.
    quadrupole`` (kg m^2 s^-2), **not** strain -- the ``2*G/(c^4 r)`` prefactor
    (source/quadrupole.py:strain_tt) is applied here explicitly, so what this
    function returns is genuinely dimensionless strain, not a mislabeled
    quadrupole magnitude. It is illustrative, not a claim about achieved
    performance: see ``Q_ORIENTATION``'s docstring for why the element
    magnitude is a token value.
    """
    target = np.array([0.0, 0.0, TARGET_RANGE])
    total = np.zeros((3, 3), dtype=np.complex128)
    for frequency, amplitude in zip(drive.frequencies, drive.amplitudes, strict=True):
        wavelength = c / float(frequency)
        weights = np.full(len(elements), amplitude, dtype=np.complex128)
        total += superpose_tt(elements, weights, wavelength, target)
    strain_phasor = (2.0 * G_OVER_C4 / TARGET_RANGE) * total
    return complex(strain_phasor[0, 0])


def render_beam_pattern(elements: list[QuadrupoleElement], drive: PrimeOscillatorDrive) -> Path:
    """Fig: beam pattern at the drive's lowest tone."""
    geometry = np.array([e.position for e in elements])
    weights = np.ones(len(elements), dtype=np.complex128)
    wavelength = c / float(drive.frequencies[0])
    fig = plot_pattern_polar(geometry, weights, wavelength)
    out = OUTDIR / "beam_pattern.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def render_field_slice(elements: list[QuadrupoleElement], drive: PrimeOscillatorDrive) -> Path:
    """Fig: a field slice near the array, one representative tone, one snapshot in time.

    Applies the same ``2*G/(c^4 r)`` strain prefactor as :func:`field_at_target`,
    per grid point (``r`` varies across the slice), so ``plot_strain_slice``'s
    "scaled strain reference" colorbar label is honest rather than reporting
    raw quadrupole units under a strain label.
    """
    wavelength = c / float(drive.frequencies[0])
    centroid = np.array([e.position for e in elements]).mean(axis=0)
    weights = np.ones(len(elements), dtype=np.complex128)

    def field(position: np.ndarray) -> np.ndarray:
        r = float(np.linalg.norm(position - centroid))
        # Snapshot at the phasor's real part -- a fixed instant, not a time series.
        raw = np.real(superpose_tt(elements, weights, wavelength, position))
        return np.asarray((2.0 * G_OVER_C4 / r) * raw, dtype=np.float64)

    aperture = 2.0 * float(
        np.linalg.norm(np.array([e.position for e in elements]) - centroid, axis=1).max()
    )
    far_field_distance = 2.0 * aperture**2 / wavelength
    slice_distance = far_field_distance * 3.0
    # Sized to the beam's own diffraction scale at slice_distance (~wavelength *
    # distance / aperture), not a fixed guess -- a fixed extent picked without
    # reference to that scale is either a flat, structureless blob (too small)
    # or aliased noise (too large); this is what T-12.1 found when it used a
    # bare 1e3 m guess here and got a solid-color figure with no beam visible.
    spot_scale = wavelength * slice_distance / aperture
    slice_: FieldSlice = extract_slice(
        field, plane="xy", fixed_coordinate=slice_distance, extent=3.0 * spot_scale, resolution=60
    )
    fig = plot_strain_slice(slice_, component=(0, 0))
    out = OUTDIR / "field_slice.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    print(
        f"Target: {ASTEROID.mass:.3e} kg asteroid ({2.0 * ASTEROID.radius:.0f} m diameter) "
        f"at {TARGET_RANGE / AU:.0f} AU"
    )
    elements = build_array()
    print(f"Array: {len(elements)} elements, {NX}x{NY} planar, {SPACING} m spacing")
    drive = build_drive()
    print(
        f"Drive: {N_TONES} prime-ratio tones, {drive.frequencies[0]:.3e}-"
        f"{drive.frequencies[-1]:.3e} Hz"
    )

    # --- field evaluation --------------------------------------------------
    strain = field_at_target(elements, drive)
    print(f"Illustrative strain phasor at target (h_xx, token element magnitude): {strain:.3e}")

    beam_fig = render_beam_pattern(elements, drive)
    print(f"Wrote {beam_fig}")
    slice_fig = render_field_slice(elements, drive)
    print(f"Wrote {slice_fig}")

    # --- coupling: absorption channel, R6's achieved luminosity -----------
    cross_section = np.pi * ASTEROID.radius**2
    coupling = channel_absorption(ACHIEVED_LUMINOSITY_W, cross_section, TARGET_RANGE)
    assert coupling.force is not None
    print(
        f"Absorption-channel force: {coupling.force:.3e} N "
        f"(luminosity {ACHIEVED_LUMINOSITY_W:.3e} W, cross-section {cross_section:.3e} m^2)"
    )

    # --- deflection ----------------------------------------------------------
    dv = delta_v(coupling.force, LEAD_TIME_S, ASTEROID.mass)
    miss = miss_distance(dv, LEAD_TIME_S, AU)
    print(f"Delta-v over a {LEAD_TIME_S / (24 * 3600):.0f}-day lead time: {dv:.3e} m/s")
    print(f"Resulting miss distance: {miss:.3e} m")

    # --- feasibility ledger --------------------------------------------------
    geometry = np.array([e.position for e in elements])
    report = GapReport(title="End-to-end scenario: feasibility gap ledger")
    report.add(
        aperture_gap(
            geometry,
            wavelength=c / float(drive.frequencies[0]),
            range_m=TARGET_RANGE,
            spot_size=1.0e3,
        )
    )
    report.add(impulse_gap(achieved_impulse=coupling.force * LEAD_TIME_S))
    ledger_path = OUTDIR / "gap_report.md"
    ledger_path.write_text(report.to_markdown(), encoding="utf-8")
    print(f"Wrote {ledger_path}")
    print()
    print(report.to_markdown())

    return 0


if __name__ == "__main__":
    sys.exit(main())
