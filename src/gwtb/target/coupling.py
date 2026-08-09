"""Non-gravitational-wave coupling channels for comparison: the gravity
tractor (near-zone Newtonian gravitational attraction).

This module is exempt from the ``source``/``propagate``/``bodies``/``array``
citation-CI check (it consumes/compares results rather than introducing new
radiation physics), but the formula below is still cited for auditability.

Source: R. Schweickart, C. Chapman, D. Durda & P. Hut, "Threat Mitigation:
The Gravity Tractor," B612 Foundation White Paper 042, arXiv:physics/0608157
(2006), p.2 §II (unnumbered display equation; restates Lu & Love, *Nature*
438, 177 (2005), which is itself a two-page unnumbered-equation letter).
Worked example confirmed against Fig. 2 (p.9) of the same paper.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gwtb.core.constants import G, c
from gwtb.ledger.gap_report import GapMetric, GapReport


def channel_gravity_tractor(tractor_mass: float, separation: float, asteroid_mass: float) -> float:
    """Gravitational-tractor thrust: simple Newtonian two-point-mass
    attraction, treating both tractor and asteroid as point masses.

    .. code-block:: text

        F = G * tractor_mass * asteroid_mass / separation^2

    This neglects the asteroid's own finite extent and internal structure
    (it is not a point mass at the separations of interest, e.g.
    ``separation ~ 1.5 * asteroid_radius`` in the paper's own worked
    example) — an assumption the source paper itself does not quantify, and
    which this project's assumption ledger should record if this channel is
    used quantitatively (BACKLOG.md T-8.5, open question OQ-5).

    Source: Schweickart, Chapman, Durda & Hut, arXiv:physics/0608157 (2006),
    p.2, eq. n/a (unnumbered; see module docstring)

    Parameters
    ----------
    tractor_mass
        Mass of the tractor spacecraft, kg. Must be positive.
    separation
        Distance between tractor and asteroid center, m. Must be positive.
    asteroid_mass
        Mass of the target asteroid, kg. Must be positive.

    Returns
    -------
    float
        Thrust force, N.
    """
    for name, value in (
        ("tractor_mass", tractor_mass),
        ("separation", separation),
        ("asteroid_mass", asteroid_mass),
    ):
        if not np.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be positive and finite, got {value!r}")

    return G * tractor_mass * asteroid_mass / separation**2


def tidal_strain(h_amplitude: float, body_radius: float) -> float:
    """Peak relative displacement across a body from a passing GW strain.

    .. code-block:: text

        tidal_strain = (1/2) * h_amplitude * body_radius

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 3.11 (the same
    formula :func:`gwtb.target.geodesic.deviation_acceleration` implements,
    specialized to a peak scalar estimate: ``delta_xi ~ (1/2) h xi`` for a
    slowly-varying strain, the standard order-of-magnitude detector-response
    relation used throughout the GW literature)

    ⚠️ **BACKLOG.md T-8.2 describes this function's output as "dimensionless."
    It is not, and cannot be while genuinely scaling with ``body_radius``.**
    ``h_amplitude`` is the dimensionless GW strain; multiplying it by a
    length gives a length (the peak relative displacement across the body),
    not a dimensionless ratio. A dimensionless *fractional* strain would be
    ``h_amplitude / 2`` alone — independent of ``body_radius``, which
    contradicts the acceptance criterion's own "scales linearly with both
    arguments." The two clauses of that AC cannot both hold; this
    implementation keeps the one that is physically coherent (linear scaling
    with both, in metres) and documents the discrepancy rather than silently
    normalizing away the ``body_radius`` dependence the task asked for.

    Parameters
    ----------
    h_amplitude
        Dimensionless GW strain amplitude at the target's location.
    body_radius
        m. Must be positive and finite.

    Returns
    -------
    float
        m. The peak displacement of a point on the body's surface relative
        to its center, from a strain of the given amplitude.
    """
    if not np.isfinite(body_radius) or body_radius <= 0.0:
        raise ValueError(f"body_radius must be positive and finite, got {body_radius!r}")
    if not np.isfinite(h_amplitude):
        raise ValueError(f"h_amplitude must be finite, got {h_amplitude!r}")

    return 0.5 * h_amplitude * body_radius


@dataclass(frozen=True)
class CouplingResult:
    """One channel's result: exactly one of ``strain`` or ``force`` is set.

    T-8.3's acceptance criterion requires that a strain-type result "carries
    no net-force field" — enforced structurally here rather than by
    convention, so a test can assert ``result.force is None`` directly.

    Attributes
    ----------
    channel
        Name of the coupling mechanism, e.g. ``"tidal"``.
    strain
        m (peak tidal displacement, see :func:`tidal_strain`), or ``None``.
    force
        N, or ``None``.
    """

    channel: str
    strain: float | None = None
    force: float | None = None

    def __post_init__(self) -> None:
        if (self.strain is None) == (self.force is None):
            raise ValueError(
                f"{self.channel}: exactly one of strain or force must be set "
                f"(got strain={self.strain!r}, force={self.force!r})"
            )

    @property
    def magnitude(self) -> float:
        """Whichever of ``strain``/``force`` is set."""
        return self.strain if self.strain is not None else self.force  # type: ignore[return-value]


def channel_tidal(h_amplitude: float, body_radius: float) -> CouplingResult:
    """Tidal coupling channel: reports strain, never a force.

    Source: Flanagan & Hughes, New J. Phys. 7:204 (2005), eq. 3.11 (via
    :func:`tidal_strain`)

    Geodesic deviation is a statement about relative motion under curvature,
    not a net force (claim A-6, ``docs/CLAIMS.md``) — there is no coherent
    "tidal force" on a free-falling body's center of mass to report, which is
    why this channel's :class:`CouplingResult` structurally has no force.

    Parameters
    ----------
    h_amplitude
        Dimensionless GW strain amplitude at the target.
    body_radius
        m. Target body radius. Must be positive and finite.

    Returns
    -------
    CouplingResult
        ``channel="tidal"``, ``strain`` set, ``force=None``.
    """
    return CouplingResult(channel="tidal", strain=tidal_strain(h_amplitude, body_radius))


def channel_absorption(luminosity: float, cross_section: float, distance: float) -> CouplingResult:
    """Absorption-thrust coupling channel: momentum flux times absorption
    cross-section.

    .. code-block:: text

        force = (luminosity / (4 pi distance^2 c)) * cross_section

    The bracketed term is the GW momentum flux (radiation pressure of a
    field carrying power ``luminosity`` isotropically, at speed ``c`` — the
    same ``F = P/c`` relation used in :func:`gwtb.ledger.gap_report.
    emission_gap`, here applied per unit area and multiplied by the target's
    absorption cross-section). This is the naive best case: it assumes
    perfect absorption over ``cross_section`` with no re-radiation.

    Source: momentum-flux relation ``F = P/c`` (see
    :func:`gwtb.ledger.gap_report.emission_gap`); ``docs/PHYSICS.md``
    "assuming radiated power converts to thrust"

    Parameters
    ----------
    luminosity
        Isotropic GW power at the source, W. Must be finite and non-negative.
    cross_section
        Target's absorption cross-section, m^2. Must be positive and finite.
    distance
        Source-to-target distance, m. Must be positive and finite.

    Returns
    -------
    CouplingResult
        ``channel="absorption"``, ``force`` set, ``strain=None``. **The
        smallness is the finding, not hidden** (CLAUDE.md rule 5): for a
        1 km asteroid at 40 AU this is expected to fall below 1e-30 N.
    """
    if not np.isfinite(luminosity) or luminosity < 0.0:
        raise ValueError(f"luminosity must be finite and non-negative, got {luminosity!r}")
    if not np.isfinite(cross_section) or cross_section <= 0.0:
        raise ValueError(f"cross_section must be positive and finite, got {cross_section!r}")
    if not np.isfinite(distance) or distance <= 0.0:
        raise ValueError(f"distance must be positive and finite, got {distance!r}")

    flux = luminosity / (4.0 * np.pi * distance**2 * c)
    return CouplingResult(channel="absorption", force=flux * cross_section)


def required_luminosity(force: float, cross_section: float, distance: float) -> float:
    """Luminosity the absorption channel would need to deliver a given force
    -- the algebraic inverse of :func:`channel_absorption`.

    .. code-block:: text

        luminosity = force * 4 * pi * distance^2 * c / cross_section

    Source: momentum-flux relation ``F = P/c`` (see
    :func:`gwtb.ledger.gap_report.emission_gap`); ``docs/PHYSICS.md``
    "assuming radiated power converts to thrust" -- same source as
    :func:`channel_absorption`, inverted for ``luminosity``.

    Parameters
    ----------
    force
        Required magnitude of the absorption-channel force, N. Unlike
        :func:`delta_v`'s ``force`` (which may be signed), this is a
        required *magnitude* and must be positive.
    cross_section
        Target's absorption cross-section, m^2. Must be positive and finite.
    distance
        Source-to-target distance, m. Must be positive and finite.

    Returns
    -------
    float
        W. Satisfies
        ``channel_absorption(required_luminosity(F, sigma, d), sigma, d).force == F``.
    """
    if not np.isfinite(force) or force <= 0.0:
        raise ValueError(f"force must be positive and finite, got {force!r}")
    if not np.isfinite(cross_section) or cross_section <= 0.0:
        raise ValueError(f"cross_section must be positive and finite, got {cross_section!r}")
    if not np.isfinite(distance) or distance <= 0.0:
        raise ValueError(f"distance must be positive and finite, got {distance!r}")

    return force * 4.0 * np.pi * distance**2 * c / cross_section


def channel_gravity_tractor_result(
    tractor_mass: float, separation: float, asteroid_mass: float
) -> CouplingResult:
    """:func:`channel_gravity_tractor`, wrapped as a :class:`CouplingResult`
    for use alongside the other two channels in :func:`compare_channels`.
    """
    return CouplingResult(
        channel="gravity_tractor",
        force=channel_gravity_tractor(tractor_mass, separation, asteroid_mass),
    )


def compare_channels(
    tidal: CouplingResult,
    absorption: CouplingResult,
    gravity_tractor: CouplingResult,
    required_strain: float,
    required_force: float,
) -> GapReport:
    """Side-by-side comparison of all three coupling channels.

    Rows are inserted **in magnitude order** (largest first) rather than the
    call order, since :class:`gwtb.ledger.gap_report.GapReport` preserves
    insertion order rather than sorting — per its own docstring, it does not
    reorder rows itself.

    **Never sums the channels.** They are not additive mechanisms — tidal
    strain, absorption thrust, and near-zone gravitational attraction operate
    through entirely different physical processes on entirely different
    quantities (a displacement and two different forces), and reporting their
    sum would imply a combined effect none of the underlying physics supports.

    Parameters
    ----------
    tidal, absorption, gravity_tractor
        One :class:`CouplingResult` from each channel function.
    required_strain
        Reference requirement for the tidal channel, m. Must be positive.
    required_force
        Reference requirement shared by the two force channels, N. Must be
        positive.

    Returns
    -------
    GapReport
        Three rows, ``"tidal"``, ``"absorption"``, ``"gravity_tractor"``,
        ordered by descending magnitude.
    """
    rows = [
        GapMetric(
            name=tidal.channel,
            achieved=abs(tidal.magnitude),
            required=required_strain,
            units="m",
            source_module="gwtb.target.coupling",
        ),
        GapMetric(
            name=absorption.channel,
            achieved=abs(absorption.magnitude),
            required=required_force,
            units="N",
            source_module="gwtb.target.coupling",
        ),
        GapMetric(
            name=gravity_tractor.channel,
            achieved=abs(gravity_tractor.magnitude),
            required=required_force,
            units="N",
            source_module="gwtb.target.coupling",
        ),
    ]
    rows.sort(key=lambda m: m.achieved, reverse=True)

    report = GapReport(title="Coupling channel comparison")
    for row in rows:
        report.add(row)
    return report


__all__ = [
    "CouplingResult",
    "channel_absorption",
    "channel_gravity_tractor",
    "channel_gravity_tractor_result",
    "channel_tidal",
    "compare_channels",
    "required_luminosity",
    "tidal_strain",
]
