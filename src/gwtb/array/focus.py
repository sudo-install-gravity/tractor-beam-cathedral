"""Spatiotemporal focusing: driving array elements so their radiation coincides
at one point in space *and* time.

Focusing is a statement about **propagation delay**, not about polarization. An
element's contribution arrives at the focal point delayed by ``R/c``, and the
phase law below simply inverts that delay. Nothing here depends on the radiation
being spin-2, which is why the geometry may legitimately be borrowed from the
antenna-array literature — unlike the *superposition* of what arrives, which is
tensorial and must go through :func:`gwtb.array.beamform.superpose_tt`
(``CLAUDE.md`` rule 4, ADR-0003).

**Precision is the hard part here, not the geometry.** Over 40 AU the absolute
propagation phase is ~1e10 wavelengths, so forming ``R_a / c`` and differencing
the results loses roughly eight decimal digits exactly where the answer lives:
the *differences* between elements are of order the aperture, ~1e4 m against a
range of ~1e12 m. Computing ``R_a - R_ref`` naively in float64 leaves ~1e-3 m of
error, i.e. ~1e-8 rad at 1 kHz — an order of magnitude worse than this module's
1e-9 rad requirement. :func:`focal_phases` therefore never forms that difference
directly; see :func:`_differential_range`.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray

from gwtb.array.beamform import QuadrupoleElement, array_factor, steering_phases, superpose_tt
from gwtb.core.constants import c
from gwtb.core.validation import as_body_array, as_float64
from gwtb.kinematics.oscillators import PrimeOscillatorDrive


def _as_point(a: ArrayLike, name: str) -> NDArray[np.float64]:
    """Validate a position vector: shape ``(3,)``, float64, finite."""
    v = as_float64(a, name)
    if v.shape != (3,):
        raise ValueError(f"{name} must have shape (3,), got {v.shape}")
    return v


def _differential_range(
    offsets: NDArray[np.float64],
    to_focus: NDArray[np.float64],
    range_ref: float,
) -> NDArray[np.float64]:
    """``|to_focus - offsets_a| - |to_focus|``, without catastrophic cancellation.

    Both ranges are ~1e12 m and differ by ~1e4 m, so subtracting them directly
    discards the eight most significant digits of the answer. The identity

    .. code-block:: text

        R_a - R_ref = (R_a^2 - R_ref^2) / (R_a + R_ref)
                    = (|q_a|^2 - 2 s.q_a) / (R_a + R_ref)

    with ``q_a`` the element offset from the reference and ``s`` the vector from
    the reference to the focus, is algebraically identical but numerically
    benign: the huge ``|s|^2`` term cancels *symbolically* and never enters the
    arithmetic. What remains is formed from quantities of order ``|s||q|``,
    carrying full float64 relative precision, and the division by ``R_a + R_ref``
    restores the scale.

    Parameters
    ----------
    offsets
        Shape ``(N, 3)``, m. Element positions relative to the reference point.
    to_focus
        Shape ``(3,)``, m. Vector from the reference point to the focal point.
    range_ref
        ``|to_focus|``, m, passed in to avoid recomputing it.

    Returns
    -------
    ndarray
        Shape ``(N,)``, m. Signed range differences, accurate to ~1e-15 m at
        astronomical range rather than the ~1e-3 m of the naive difference.
    """
    numerator = np.einsum("ai,ai->a", offsets, offsets) - 2.0 * (offsets @ to_focus)
    range_a = np.linalg.norm(to_focus - offsets, axis=1)
    # einsum's numpy stub returns Any; annotate so mypy narrows the result back
    # to NDArray[np.float64] rather than silently widening the return type.
    result: NDArray[np.float64] = numerator / (range_a + range_ref)
    return result


def focal_phases(
    geometry: ArrayLike,
    frequencies: ArrayLike,
    focal_point: ArrayLike,
    focal_time: float,
) -> NDArray[np.float64]:
    """Per-element, per-frequency drive phases that focus at one space-time point.

    An element at ``p_a`` driven as ``sin(2 pi f t + phi_a)`` contributes, at the
    focal point, the phase ``2 pi f (t - R_a/c) + phi_a`` with ``R_a =
    |r_focus - p_a|``. Requiring every element and every frequency to arrive at
    the same phase at ``t = focal_time`` inverts to

    .. code-block:: text

        phi_a(f) = 2 pi f (R_a / c - focal_time)

    which is this function, evaluated in the numerically stable form described
    in :func:`_differential_range` and wrapped to ``[-pi, pi)``.

    **Each element gets its own exact delay.** The array centroid appears only
    as an arithmetic reference point for the differencing identity — never as a
    single delay standing in for the whole array, which is the quiet, high-damage
    error ADR-0002 §7 exists to forbid. The two are distinguishable by test, and
    ``tests/unit/test_focus.py`` distinguishes them: element phases are checked
    against exact ``decimal``-arithmetic ranges, which a centroid approximation
    fails by many orders of magnitude.

    Absolute versus differential phase: the term common to all elements,
    ``2 pi f (R_ref/c - focal_time)``, is ~1e8 rad at 1 kHz and 40 AU and so
    carries only ~1e-8 rad of float64 absolute accuracy. That limit is real but
    does not affect focusing, which depends only on element-to-element phase
    *differences* — these are exact to ~1e-15 rad. Recovering absolute phase at
    this range is what T-11.3's split-phase scheme is for.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 2 (the retarded-time
    relation ``t_ret = t - R/c`` whose per-element inversion this is; the
    inversion itself is this project's own construction, as no external
    gravitational-wave reference gives an array focusing phase law)

    Parameters
    ----------
    geometry
        Shape ``(N, 3)``, m. Element positions, per ADR-0002 §1.
    frequencies
        Shape ``(F,)``, Hz. Strictly positive.
    focal_point
        Shape ``(3,)``, m. Where the radiation is to coincide.
    focal_time
        Coordinate time at the focal point, s, at which coincidence occurs.

    Returns
    -------
    ndarray
        Shape ``(N, F)``, rad, wrapped to ``[-pi, pi)``. Element index leads,
        per ADR-0002 §1.

    Raises
    ------
    ValueError
        If shapes are wrong, frequencies are not positive, or the focal point
        coincides with an element (where the delay is undefined).
    """
    positions = as_body_array(geometry, "geometry")
    freqs = as_float64(frequencies, "frequencies")
    target = _as_point(focal_point, "focal_point")

    if freqs.ndim != 1 or freqs.size == 0:
        raise ValueError(f"frequencies must have shape (F,), got {freqs.shape}")
    if np.any(freqs <= 0.0):
        raise ValueError("frequencies must be strictly positive")
    if not math.isfinite(focal_time):
        raise ValueError(f"focal_time must be finite, got {focal_time!r}")

    reference = positions.mean(axis=0)
    offsets = positions - reference
    to_focus = target - reference
    range_ref = float(np.linalg.norm(to_focus))

    ranges = np.linalg.norm(target - positions, axis=1)
    if np.any(ranges == 0.0):
        raise ValueError(
            "focal_point coincides with an array element; the propagation delay "
            "to that element is undefined"
        )

    delta_range = _differential_range(offsets, to_focus, range_ref)

    # Split deliberately: the differential term carries full precision, while
    # the common term is wrapped once, at its own (lower) absolute accuracy.
    # Adding them before wrapping would spread the common term's ~1e-8 rad error
    # across every element and destroy the differential accuracy.
    differential = 2.0 * np.pi * np.outer(delta_range / c, freqs)
    common = 2.0 * np.pi * freqs * (range_ref / c - focal_time)
    common_wrapped = np.remainder(common + np.pi, 2.0 * np.pi) - np.pi

    phases = differential + common_wrapped
    wrapped: NDArray[np.float64] = np.remainder(phases + np.pi, 2.0 * np.pi) - np.pi
    return wrapped


def focused_phasor(
    array: Sequence[QuadrupoleElement],
    drive: PrimeOscillatorDrive,
    field_points: ArrayLike,
    focal_point: ArrayLike,
    focal_time: float = 0.0,
) -> NDArray[np.complex128]:
    """Complex TT strain phasor per field point and drive tone.

    The frequency-domain half of :func:`focused_field`, exposed because the
    envelope is what the mode-locking acceptance criteria are stated in: a peak
    amplitude read off a sampled time series carries the sampling error of the
    peak search, which at rtol 1e-6 would dominate the quantity being measured.

    Each tone's weights are ``A_f * exp(+i (phi_a,f + drive_phase_f))``, with
    ``phi_a,f`` from :func:`focal_phases`, and the superposition is delegated
    **unchanged** to :func:`gwtb.array.beamform.superpose_tt` per ADR-0006. No
    projection logic is reimplemented here.

    Source: docs/adr/0006-focused-field-far-field-regime.md, eq. n/a (a
    composition of :func:`focal_phases` (EQ-029) with
    :func:`gwtb.array.beamform.superpose_tt`; introduces no new equation)

    Parameters
    ----------
    array
        The radiating elements. Their ``quadrupole`` tensors carry orientation
        and magnitude; the drive supplies the per-tone excitation.
    drive
        Supplies ``frequencies``, ``amplitudes`` and ``phases``.
    field_points
        Shape ``(M, 3)``, m.
    focal_point
        Shape ``(3,)``, m. Where the tones are made to coincide.
    focal_time
        Coordinate time at the focal point, s, at which they coincide.

    Returns
    -------
    ndarray
        Shape ``(M, F, 3, 3)`` complex, in the units of the elements'
        ``quadrupole``. ``F`` is the number of drive tones.

    Raises
    ------
    ValueError
        If any field point lies inside the array's Fraunhofer distance. Raised
        by :func:`~gwtb.array.beamform.superpose_tt` and **propagated
        deliberately**: near-field focusing is out of scope (ADR-0006), and a
        near-field request must fail loudly rather than degrade to a
        formulation ADR-0003 forbids.
    """
    elements = list(array)
    if not elements:
        raise ValueError("array must be non-empty")

    positions = np.array([_as_point(e.position, "position") for e in elements])
    points = as_body_array(field_points, "field_points")

    frequencies = drive.frequencies
    amplitudes = drive.amplitudes
    tone_phases = drive.phases

    phi = focal_phases(positions, frequencies, focal_point, focal_time)

    out = np.zeros((points.shape[0], frequencies.size, 3, 3), dtype=np.complex128)
    for j, frequency in enumerate(frequencies):
        wavelength = c / float(frequency)
        weights = amplitudes[j] * np.exp(1j * (phi[:, j] + tone_phases[j]))
        for m in range(points.shape[0]):
            out[m, j] = superpose_tt(elements, weights, wavelength, points[m])
    return out


def focused_field(
    array: Sequence[QuadrupoleElement],
    drive: PrimeOscillatorDrive,
    field_points: ArrayLike,
    times: ArrayLike,
    focal_point: ArrayLike,
    focal_time: float = 0.0,
) -> NDArray[np.float64]:
    """TT strain time series at each field point, with the drive focused.

    .. code-block:: text

        h_ij(x, t) = sum_f Im[ H_ij^(f)(x) * exp(i 2 pi f t) ]

    where ``H^(f)`` is :func:`focused_phasor`. The imaginary part is taken
    because :class:`~gwtb.kinematics.oscillators.PrimeOscillatorDrive` defines
    its tones as ``sin(2 pi f t + phase)``.

    **What "focused" means at engagement range.** At 40 AU the array sits some
    ``5.9e6`` Fraunhofer distances from the target, so the focal point is a
    *steering direction*, not a point of concentration: the wavefront sag across
    a 12.4 km aperture is ~3.2e-6 m. This function is a far-field construction
    and says nothing about concentrating energy at range — see ADR-0006 and the
    assumption ledger in ``docs/INDEX.md``.

    **Signature note.** BACKLOG.md T-9.6 specifies ``focused_field(array, drive,
    field_points, times)``. ``focal_point`` and ``focal_time`` are added because
    a focus cannot be formed without them; the four specified parameters keep
    their meaning. Recorded here rather than made silently, as for
    :func:`gwtb.core.backend.split_phase`.

    Source: docs/adr/0006-focused-field-far-field-regime.md, eq. n/a (see
    :func:`focused_phasor`; this adds only the time dependence)

    Parameters
    ----------
    array, drive, focal_point, focal_time
        As for :func:`focused_phasor`.
    field_points
        Shape ``(M, 3)``, m.
    times
        Shape ``(T,)``, s. Coordinate time at the field point.

    Returns
    -------
    ndarray
        Shape ``(M, T, 3, 3)``, dimensionless-scaled in the units of the
        elements' ``quadrupole``. Leading axes follow
        :func:`gwtb.propagate.retarded.propagate` (ADR-0002 §2).

    Raises
    ------
    ValueError
        Propagated from :func:`focused_phasor` for a near-field request.
    """
    t = as_float64(times, "times")
    if t.ndim != 1 or t.size == 0:
        raise ValueError(f"times must have shape (T,), got {t.shape}")

    phasors = focused_phasor(array, drive, field_points, focal_point, focal_time)
    frequencies = drive.frequencies

    # (M, F, 3, 3) x (F, T) -> (M, T, 3, 3)
    oscillation = np.exp(1j * 2.0 * np.pi * np.outer(frequencies, t))
    result: NDArray[np.float64] = np.einsum(
        "mfij,ft->mtij", phasors, oscillation, optimize=True
    ).imag
    return result


#: Half-width, in the Airy variable ``v = (pi D / lambda) sin(theta)``, at which
#: ``[2 J_1(v)/v]^2`` falls to one half. Equivalently the root of
#: ``2 J_1(x)/x = 1/sqrt(2)``.
#:
#: This number is the citation. It is reproducible in two lines with
#: ``scipy.special.j1`` and ``scipy.optimize.brentq``, so a reader in 2075 can
#: check it without access to any book — which is more than can be said for the
#: textbook page it would otherwise be sourced to.
_AIRY_HALF_MAX_ROOT = 1.616339948310703

#: Full width at half maximum of the Airy main lobe, in units of ``lambda/D``:
#: ``2 * root / pi``. **Not 1.22** — that is the Rayleigh criterion, the first
#: Airy *null*, which is a resolution limit rather than a beam width.
FWHM_COEFFICIENT = 2.0 * _AIRY_HALF_MAX_ROOT / np.pi


def spot_size(array: ArrayLike, wavelength: float, range_m: float) -> float:
    """Diffraction-limited -3 dB transverse extent of the focal spot.

    .. code-block:: text

        w = (2 x_h / pi) * lambda * r / D  =  1.0290 * lambda * r / D

    where ``x_h = 1.6163399`` solves ``2 J_1(x)/x = 1/sqrt(2)``, i.e. the
    half-maximum point of the Airy pattern ``[2 J_1(v)/v]^2``. Since
    ``10 log10(1/2) = -3.01 dB``, the -3 dB width *is* the full width at half
    maximum; no separate convention is involved.

    Source: Airy pattern for a uniformly-illuminated circular aperture,
    ``I/I_0 = [2 J_1(v)/v]^2`` with ``v = (pi D/lambda) sin(theta)``, eq. n/a —
    the standard result (Born & Wolf, *Principles of Optics* §8.5.2), cited here
    by its **reproducible root** rather than an equation number this project
    could not confirm. Corroborated by Thorne & Blandford, *Modern Classical
    Physics* ch. 8 (open-access Caltech ph136 notes), which gives
    ``rho_FWHM = 1.61633 z/(kR)``.

    **Not the Rayleigh criterion.** ``1.22 lambda/D`` locates the first null and
    is a two-source resolution limit; using it here would overstate the spot by
    19%. :data:`FWHM_COEFFICIENT` is the -3 dB width.

    **This is scalar diffraction, and that is legitimate here.** The result is
    the Fourier transform of the aperture function: it fixes the transverse
    *envelope* and is blind to what is being radiated. It is therefore safe for
    aperture geometry — but it says nothing whatever about how ``h_plus`` and
    ``h_cross`` combine, and must never be reused for polarization synthesis,
    where the spin-2 structure of ``CLAUDE.md`` rule 4 governs.

    **Assumes a uniformly-illuminated circular aperture.** The coefficient is
    geometry-specific: a uniformly-weighted *square* aperture has FWHM
    ``0.886 lambda/D`` along its axes, 14% narrower. Applying this function to a
    strongly non-circular layout silently returns the circular answer. ``D`` is
    taken as the maximum pairwise element separation.

    Parameters
    ----------
    array
        Shape ``(N, 3)``, m. Element positions, per ADR-0002 §1.
    wavelength
        Radiation wavelength, m. Must be positive and finite.
    range_m
        Distance from the aperture to the focal plane, m. Positive and finite.

    Returns
    -------
    float
        The -3 dB transverse extent, m.
    """
    positions = as_body_array(array, "array")
    if not math.isfinite(wavelength) or wavelength <= 0.0:
        raise ValueError(f"wavelength must be positive and finite, got {wavelength!r}")
    if not math.isfinite(range_m) or range_m <= 0.0:
        raise ValueError(f"range_m must be positive and finite, got {range_m!r}")

    diameter = float(np.max(np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=-1)))
    if diameter == 0.0:
        raise ValueError(
            "array has zero extent (all elements coincide); a single point has no "
            "aperture and therefore no diffraction-limited spot size"
        )

    return FWHM_COEFFICIENT * wavelength * range_m / diameter


def focus_trajectory(
    array: ArrayLike, focal_point: ArrayLike, focal_time: float, times: ArrayLike
) -> NDArray[np.float64]:
    """Instantaneous location of the mode-locked focus at each requested time.

    .. code-block:: text

        R(t) = R_focus + c * (t - focal_time)
        position(t) = reference + n_hat * R(t)

    A spatiotemporal focus is a coherent superposition of components each
    still propagating outward at exactly ``c`` (vacuum GR is non-dispersive —
    see the assumption ledger in ``docs/INDEX.md``). The engineered
    coincidence at ``(focal_point, focal_time)`` is therefore a single instant
    the wavefront passes through, not a place it settles: at any other time
    the coherent peak has moved on, radially, at ``c``, along the fixed
    direction from the array toward ``focal_point``.

    **AC: the focus moves at c and does not remain stationary.** This is a
    direct corollary of the retarded-time relation ``t_ret = t - R/c``
    already cited for :func:`focal_phases` — no new equation is introduced.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 2 (retarded-time
    propagation; corollary, see above)

    Parameters
    ----------
    array
        Shape ``(N, 3)``, m. Element positions, per ADR-0002 §1.
    focal_point
        Shape ``(3,)``, m. Where the focus was engineered to form.
    focal_time
        s. When it forms there.
    times
        Shape ``(T,)``, s. Times to evaluate the focus location at.

    Returns
    -------
    ndarray
        Shape ``(T, 3)``, m. The focus's location at each requested time.
    """
    positions = as_body_array(array, "array")
    target = _as_point(focal_point, "focal_point")
    if not math.isfinite(focal_time):
        raise ValueError(f"focal_time must be finite, got {focal_time!r}")
    t = as_float64(times, "times")
    if t.ndim != 1 or t.size == 0:
        raise ValueError(f"times must have shape (T,), got {t.shape}")

    reference = positions.mean(axis=0)
    to_focus = target - reference
    range_focus = float(np.linalg.norm(to_focus))
    if range_focus == 0.0:
        raise ValueError("focal_point coincides with the array reference point")
    n_hat = to_focus / range_focus

    range_t = range_focus + c * (t - focal_time)
    result: NDArray[np.float64] = reference[None, :] + np.outer(range_t, n_hat)
    return result


def dwell_time(bandwidth: float) -> float:
    """How long the mode-locked focus persists at a point.

    .. code-block:: text

        dwell_time = 1 / bandwidth

    The Fourier time-bandwidth reciprocal relation: a coherent superposition
    of tones spanning ``bandwidth`` in frequency space constructively
    interferes only within a window of duration ``~1/bandwidth`` before the
    tones' relative phases drift apart. Elementary signal processing, not a
    citable GW-physics claim — the same category as the impulse-momentum
    relation in :func:`gwtb.target.deflection.delta_v`.

    Source: elementary Fourier time-bandwidth reciprocity, eq. n/a (not a
    GW-specific claim; see docstring)

    Parameters
    ----------
    bandwidth
        Hz. Spread of the drive's frequency content (e.g.
        ``max(frequencies) - min(frequencies)`` for a
        :class:`~gwtb.kinematics.oscillators.PrimeOscillatorDrive`). Must be
        positive and finite.

    Returns
    -------
    float
        s.
    """
    if not math.isfinite(bandwidth) or bandwidth <= 0.0:
        raise ValueError(f"bandwidth must be positive and finite, got {bandwidth!r}")
    return 1.0 / bandwidth


def peak_to_sidelobe(
    geometry: ArrayLike,
    wavelength: float,
    direction: ArrayLike,
    n_samples: int = 4000,
    seed: int = 0,
) -> float:
    """Peak-to-sidelobe amplitude ratio for an array steered toward ``direction``.

    .. code-block:: text

        peak     = |array_factor(geometry, steered weights, wavelength, direction)|
        sidelobe = RMS |array_factor(geometry, steered weights, wavelength, d)|
                   over random d away from `direction`

    The scalar array factor is legitimate here (unlike a field-strength
    result) because this is a statement about **aperture geometry and phase
    interference**, exactly the diffraction-pattern reasoning
    :func:`spot_size` already relies on — not about spin-2 polarization
    structure.

    For ``N`` elements at independent-looking (e.g. randomly-thinned)
    positions, contributions at a generic off-peak direction behave like
    ``N`` unit phasors of uncorrelated phase: ``E[|AF|^2] = N`` exactly (an
    exact combinatorial identity for independent phases, not an
    approximation — the real and cross terms of ``E[sum_k sum_l
    exp(i(phase_k - phase_l))]`` vanish for ``k != l`` and contribute exactly
    ``N`` for ``k == l``), so the RMS sidelobe level is ``sqrt(N)`` and the
    ratio to the coherent peak (``N``) is ``sqrt(N)``. A uniform, densely
    packed array's near sidelobes are instead governed by deterministic
    interference (the classical ``-13.2`` dB first sidelobe,
    :func:`gwtb.array.beamform.peak_sidelobe_level`) and need not follow this
    trend — this is precisely the open tension OQ-4 names.

    Source: this project's own construction, eq. n/a (measurement built from
    :func:`gwtb.array.beamform.array_factor`, eq. 19.4.1; the ``sqrt(N)``
    random-array scaling is the same combinatorial identity already used for
    T-9.6's background level, ADR-0006)

    Parameters
    ----------
    geometry
        Shape ``(N, 3)``, m.
    wavelength
        m. Must be positive and finite.
    direction
        Shape ``(3,)`` unit vector to steer the main lobe toward.
    n_samples
        Number of random off-peak directions to average the sidelobe level
        over. Must be a positive integer.
    seed
        Seed for the random direction sample, for reproducibility.

    Returns
    -------
    float
        Dimensionless ratio, ``peak / sidelobe_rms``.
    """
    positions = as_body_array(geometry, "geometry")
    if not math.isfinite(wavelength) or wavelength <= 0.0:
        raise ValueError(f"wavelength must be positive and finite, got {wavelength!r}")
    if n_samples < 1:
        raise ValueError(f"n_samples must be a positive integer, got {n_samples!r}")

    weights = np.exp(1j * steering_phases(positions, wavelength, direction))
    d = np.asarray(direction, dtype=np.float64)
    peak = abs(array_factor(positions, weights, wavelength, d))

    rng = np.random.default_rng(seed)
    raw = rng.normal(size=(n_samples, 3))
    sample_dirs = raw / np.linalg.norm(raw, axis=1, keepdims=True)
    # Exclude directions within a generous cone of the main lobe, so the
    # sidelobe estimate is not itself contaminated by main-lobe power.
    cos_angle = sample_dirs @ d
    off_peak = sample_dirs[cos_angle < np.cos(np.deg2rad(5.0))]
    if off_peak.shape[0] < 10:
        raise ValueError("n_samples too small to gather enough off-peak directions")

    magnitudes = np.array(
        [abs(array_factor(positions, weights, wavelength, sd)) for sd in off_peak]
    )
    sidelobe_rms = float(np.sqrt(np.mean(magnitudes**2)))
    if sidelobe_rms == 0.0:
        return math.inf
    return peak / sidelobe_rms


def band_sweep(
    frequencies: ArrayLike, luminosity_at: Callable[[float], float]
) -> NDArray[np.float64]:
    """Radiated power across a sweep of the prime-comb unit frequency scale.

    Thin wrapper: evaluates the caller-supplied ``luminosity_at(f)`` — the
    project's own quadrupole luminosity for whatever fixed source geometry is
    under study, driven at frequency ``f`` — across ``frequencies``. Kept as
    a wrapper rather than a fixed formula because "radiated power scales as
    f^6" (the acceptance criterion) is a property of the quadrupole luminosity
    formula applied to a rigid oscillator (``P ~ omega^6``, from three time
    derivatives of a sinusoidal quadrupole each contributing one power of
    ``omega``, squared), not a new equation this function introduces.

    Source: Blanchet, Living Rev. Relativ. 17:2 (2014), eq. 4 (quadrupole
    luminosity; the f^6 scaling is a corollary for a sinusoidal drive, not a
    new equation)

    Parameters
    ----------
    frequencies
        Shape ``(F,)``, Hz. Strictly positive, the unit frequency scale to
        sweep (e.g. :func:`gwtb.kinematics.oscillators.prime_frequencies`'s
        ``unit_hz``).
    luminosity_at
        Callable mapping a frequency, Hz, to radiated power, W, for the
        source geometry under study.

    Returns
    -------
    ndarray
        Shape ``(F,)``, W.
    """
    freqs = as_float64(frequencies, "frequencies")
    if freqs.ndim != 1 or freqs.size == 0:
        raise ValueError(f"frequencies must have shape (F,), got {freqs.shape}")
    if np.any(freqs <= 0.0):
        raise ValueError("frequencies must be strictly positive")

    result: NDArray[np.float64] = np.array([luminosity_at(float(f)) for f in freqs])
    return result


def trade_surface(
    frequencies: ArrayLike, range_m: float, target_spot_size: float
) -> NDArray[np.float64]:
    """Required aperture as a function of drive frequency, at fixed range and
    target spot size.

    .. code-block:: text

        D(f) = FWHM_COEFFICIENT * (c/f) * range_m / target_spot_size

    Inverts :func:`spot_size` (``w = FWHM_COEFFICIENT * lambda * r / D``) for
    ``D``, sweeping ``lambda = c/f`` over ``frequencies``.

    Source: this project's own construction, eq. n/a (algebraic inversion of
    :func:`spot_size`, EQ-033; introduces no new equation)

    Parameters
    ----------
    frequencies
        Shape ``(F,)``, Hz. Strictly positive.
    range_m
        m. Must be positive and finite.
    target_spot_size
        m. Must be positive and finite.

    Returns
    -------
    ndarray
        Shape ``(F,)``, m. Required aperture diameter at each frequency.
    """
    freqs = as_float64(frequencies, "frequencies")
    if freqs.ndim != 1 or freqs.size == 0:
        raise ValueError(f"frequencies must have shape (F,), got {freqs.shape}")
    if np.any(freqs <= 0.0):
        raise ValueError("frequencies must be strictly positive")
    if not math.isfinite(range_m) or range_m <= 0.0:
        raise ValueError(f"range_m must be positive and finite, got {range_m!r}")
    if not math.isfinite(target_spot_size) or target_spot_size <= 0.0:
        raise ValueError(f"target_spot_size must be positive and finite, got {target_spot_size!r}")

    wavelengths = c / freqs
    result: NDArray[np.float64] = FWHM_COEFFICIENT * wavelengths * range_m / target_spot_size
    return result


__all__ = [
    "FWHM_COEFFICIENT",
    "band_sweep",
    "dwell_time",
    "focal_phases",
    "focus_trajectory",
    "focused_field",
    "focused_phasor",
    "peak_to_sidelobe",
    "spot_size",
    "trade_surface",
]
