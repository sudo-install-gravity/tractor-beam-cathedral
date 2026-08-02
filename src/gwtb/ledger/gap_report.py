"""The feasibility ledger: what the concept achieves versus what it requires.

**This schema is frozen (T-2.6).** Every epic writes rows into it — emission
magnitude (T-2.7), body parameters (T-4.9), aperture (T-5.9), coupling and
deflection (T-8.9), focusing (T-10.8). A schema that drifted would have the
ledger chasing interface changes for the length of the project, so the field
set below is a contract rather than a convenience. See "Frozen contract" in
:class:`GapMetric`.

The ledger's job is to state gaps honestly and keep them visible. Per
``CLAUDE.md`` rule 5 a wall is a *finding*, not a bug: rows here are expected to
show shortfalls of many orders of magnitude, and a change that makes one
disappear should be suspected before it is celebrated.

This module is arithmetic and formatting over results computed elsewhere; it
introduces no physics of its own, which is why ``tools/check_citations.py``
exempts ``ledger/``. Each row instead names the module that produced it, in
``source_module``, so any number in the ledger can be traced back to cited code.

**Freeze amended 2026-07-31, same day it was set.** The original five fields had
no way to record that a row came from a source violating momentum conservation.
Since :class:`gwtb.source.conservation.StampedResult` deliberately offers only
``.value`` as an escape hatch, a caller feeding a stamped result into the ledger
was *forced* to discard the stamp at the call site — turning a dipole artifact
some 10^10 times the true quadrupole signal into a row that clears its
requirement by ten orders of magnitude and looks like a breakthrough. That is
the precise failure ``CLAUDE.md`` rule 2 exists to prevent. A sixth field,
``provenance``, closes it. The amendment was made while ``T-2.4`` and ``T-2.7``
were still unstarted and the freeze had no dependents; it defaults to ``None``,
so every five-argument call site keeps working. Widening the contract later,
once epics were writing to it, is exactly the cost the freeze was meant to
avoid.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import ArrayLike

from gwtb.core.constants import c
from gwtb.core.validation import as_body_array
from gwtb.source.conservation import UNPHYSICAL_STAMP, StampedResult

#: Rendered in place of a numeric gap when ``achieved`` is exactly zero.
#: Spelled out rather than left as ``inf`` so a reader of the rendered table
#: sees a statement, not a floating-point artifact.
_NO_ACHIEVEMENT = "no achievement"

#: Column headers for :meth:`GapReport.to_markdown`. Part of the frozen
#: contract: downstream docs link to these columns.
_COLUMNS = ("Metric", "Achieved", "Required", "Units", "Gap (decades)", "Source")

#: Fixed numeric format. Stability matters more than compactness here — a table
#: whose column widths shift with float noise produces spurious diffs in
#: ``docs/`` on every run.
_NUM_FMT = "{:.3e}"

#: Prefix marking a rendered row whose source violates momentum conservation.
_UNPHYSICAL_MARK = "⚠️ UNPHYSICAL"


@dataclass(frozen=True)
class GapMetric:
    """One row of the feasibility ledger: an achieved value against a required one.

    **Frozen contract (T-2.6).** The five constructor fields — ``name``,
    ``achieved``, ``required``, ``units``, ``source_module`` — are fixed.
    Downstream epics construct these positionally and by keyword; adding a
    required field, renaming one, or changing their meaning is a breaking
    change to every epic at once.

    The frozen schema carries one deliberate restriction: **both values are
    non-negative magnitudes in the same units**, and ``required`` is strictly
    positive. Every gap this project measures — radiated power, strain,
    impulse, deflection distance, aperture, spot size — is such a magnitude.
    A future signed or dimensionless-ratio metric must be added as a *new*
    field or a new class, never by relaxing these checks, because the meaning
    of :attr:`gap_decades` depends on them.

    Parameters
    ----------
    name
        Human-readable metric name, e.g. ``"radiated power"``. Used as the
        row's identity: :meth:`GapReport.add` rejects duplicates.
    achieved
        What the concept delivers, in ``units``. Must be finite and >= 0.
        Zero is permitted and means exactly that — see :attr:`gap_decades`.
    required
        What the mission needs, in ``units``. Must be finite and > 0.
    units
        SI unit string, e.g. ``"W"``. Both values are in these units; the
        ledger performs no unit conversion.
    source_module
        Dotted path of the module that computed ``achieved``, e.g.
        ``"gwtb.source.quadrupole"``. This is the audit trail: it points at
        cited code, which is why the ledger itself needs no citation.
    provenance
        Free text carried from :class:`gwtb.source.conservation.StampedResult`,
        or ``None`` for a result with no recorded provenance. When it contains
        :data:`gwtb.source.conservation.UNPHYSICAL_STAMP` the row is flagged in
        every rendering. Prefer :meth:`from_stamped` over setting this by hand.
    """

    name: str
    achieved: float
    required: float
    units: str
    source_module: str
    provenance: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must be a non-empty string")
        if not self.units:
            raise ValueError(f"{self.name}: units must be a non-empty string")
        if not self.source_module:
            raise ValueError(
                f"{self.name}: source_module must name the module that computed "
                f"`achieved`, so the row can be traced back to cited code"
            )
        if not math.isfinite(self.achieved) or self.achieved < 0.0:
            raise ValueError(
                f"{self.name}: achieved must be finite and non-negative, got {self.achieved!r}"
            )
        if not math.isfinite(self.required) or self.required <= 0.0:
            raise ValueError(
                f"{self.name}: required must be finite and strictly positive, got {self.required!r}"
            )

    @property
    def gap_decades(self) -> float:
        """Orders of magnitude by which ``achieved`` falls short of ``required``.

        ``log10(required / achieved)``. Positive is a shortfall, negative means
        the requirement is exceeded, zero means it is met exactly.

        Returns ``inf`` when ``achieved`` is exactly zero: a shortfall of
        infinitely many decades is the truthful answer, and returning it
        (rather than raising, or substituting a large finite number) keeps the
        wall visible in the rendered table.
        """
        if self.achieved == 0.0:
            return math.inf
        return math.log10(self.required / self.achieved)

    @property
    def meets_requirement(self) -> bool:
        """Whether ``achieved`` is at least ``required``."""
        return self.achieved >= self.required

    @property
    def is_unphysical(self) -> bool:
        """Whether this row's provenance carries the ``UNPHYSICAL`` stamp.

        Derived from :attr:`provenance` rather than stored separately, so the
        two cannot disagree.
        """
        return self.provenance is not None and UNPHYSICAL_STAMP in self.provenance

    @classmethod
    def from_stamped(
        cls,
        name: str,
        achieved: StampedResult,
        required: float,
        units: str,
        source_module: str,
    ) -> GapMetric:
        """Build a row from a :class:`~gwtb.source.conservation.StampedResult`.

        This is the path that cannot lose the stamp, and therefore the one to
        use. Taking ``.value`` and calling the plain constructor would compile
        and pass tests while silently discarding the provenance — which is the
        whole failure this method exists to make unnecessary.

        ``achieved`` must wrap a single scalar: a ledger row is one number.
        """
        if not isinstance(achieved, StampedResult):
            raise TypeError(
                f"from_stamped expects a StampedResult, got {type(achieved).__name__}; "
                f"use the plain constructor for an already-unwrapped float"
            )
        if achieved.value.size != 1:
            raise ValueError(
                f"{name}: a ledger row is a single number, but the stamped result "
                f"has shape {achieved.value.shape}. Reduce it before recording."
            )
        return cls(
            name=name,
            achieved=float(achieved.value.reshape(())),
            required=required,
            units=units,
            source_module=source_module,
            provenance=achieved.provenance,
        )

    def to_dict(self) -> dict[str, Any]:
        """JSON-compatible mapping of the five frozen fields.

        Derived quantities (:attr:`gap_decades`, :attr:`meets_requirement`) are
        deliberately **not** serialized: they are recomputed on load, so a
        stored ledger cannot disagree with itself.
        """
        return {
            "name": self.name,
            "achieved": self.achieved,
            "required": self.required,
            "units": self.units,
            "source_module": self.source_module,
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GapMetric:
        """Inverse of :meth:`to_dict`, rejecting unknown or missing keys.

        Strictness is the point: a silently-ignored key is how a schema change
        goes unnoticed until a downstream epic reads a field that was never
        written (``CLAUDE.md`` rule 8 — make absence loud).
        """
        expected = {
            "name",
            "achieved",
            "required",
            "units",
            "source_module",
            "provenance",
        }
        actual = set(data)
        if actual != expected:
            missing = sorted(expected - actual)
            unknown = sorted(actual - expected)
            raise ValueError(
                f"GapMetric payload does not match the frozen schema; "
                f"missing={missing}, unknown={unknown}"
            )
        return cls(
            name=data["name"],
            achieved=float(data["achieved"]),
            required=float(data["required"]),
            units=data["units"],
            source_module=data["source_module"],
            provenance=data["provenance"],
        )


@dataclass
class GapReport:
    """An ordered collection of :class:`GapMetric` rows, renderable and storable.

    Rows keep **insertion order**, not sorted order. The ledger is assembled
    epic by epic, and that order is itself information — it is the order in
    which the analysis proceeds. Insertion order is also what makes
    :meth:`to_markdown` stable: the same sequence of :meth:`add` calls renders
    byte-identically every time.

    Parameters
    ----------
    title
        Heading for the rendered table.
    metrics
        Optional initial rows. Duplicated names are rejected here exactly as in
        :meth:`add`.
    """

    title: str = "Feasibility gap ledger"
    metrics: list[GapMetric] = field(default_factory=list)

    def __post_init__(self) -> None:
        existing = list(self.metrics)
        self.metrics = []
        for metric in existing:
            self.add(metric)

    def __len__(self) -> int:
        return len(self.metrics)

    def __iter__(self) -> Iterator[GapMetric]:
        return iter(self.metrics)

    def add(self, metric: GapMetric) -> None:
        """Append a row, rejecting a duplicate ``name``.

        Two rows with one name means one of them is being silently shadowed in
        every reading of the ledger, so this raises instead.
        """
        if not isinstance(metric, GapMetric):
            raise TypeError(f"add() takes a GapMetric, got {type(metric).__name__}")
        if any(existing.name == metric.name for existing in self.metrics):
            raise ValueError(
                f"a metric named {metric.name!r} is already in this report; "
                f"names identify rows and must be unique"
            )
        self.metrics.append(metric)

    def to_markdown(self) -> str:
        """Render as a Markdown table.

        Stable: identical input renders identical output, with fixed numeric
        formatting and fixed column order. An empty report renders an explicit
        "no metrics recorded" line rather than a bare header, so an empty
        ledger cannot be mistaken for a ledger with nothing to report.
        """
        lines = [f"## {self.title}", ""]
        if not self.metrics:
            lines.append("_No metrics recorded._")
            lines.append("")
            return "\n".join(lines)

        lines.append("| " + " | ".join(_COLUMNS) + " |")
        lines.append("|" + "|".join(["---"] * len(_COLUMNS)) + "|")
        for m in self.metrics:
            gap = _NO_ACHIEVEMENT if math.isinf(m.gap_decades) else f"{m.gap_decades:.1f}"
            # The stamp goes in the metric name, the leftmost column, so it
            # cannot be missed by a reader skimming the table or lost to a
            # truncated render.
            name = f"{_UNPHYSICAL_MARK} {m.name}" if m.is_unphysical else m.name
            lines.append(
                "| "
                + " | ".join(
                    (
                        name,
                        _NUM_FMT.format(m.achieved),
                        _NUM_FMT.format(m.required),
                        m.units,
                        gap,
                        m.source_module,
                    )
                )
                + " |"
            )
        lines.append("")

        stamped = [m for m in self.metrics if m.is_unphysical]
        if stamped:
            lines.append(
                f"> {_UNPHYSICAL_MARK} **{len(stamped)} row(s) derived from a source that "
                f"violates `d_mu T^mu-nu = 0`.** These are artifacts, not results — a "
                f"mass-dipole term is roughly 10^10 times the true quadrupole signal. "
                f"Do not read them as achieved performance."
            )
            for m in stamped:
                lines.append(f">   - `{m.name}`: {m.provenance}")
            lines.append("")
        return "\n".join(lines)

    def to_json(self, indent: int = 2) -> str:
        """Serialize the whole report to a JSON string."""
        payload = {
            "title": self.title,
            "metrics": [m.to_dict() for m in self.metrics],
        }
        return json.dumps(payload, indent=indent, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> GapReport:
        """Inverse of :meth:`to_json`, preserving row order."""
        payload = json.loads(text)
        expected = {"title", "metrics"}
        if set(payload) != expected:
            raise ValueError(
                f"GapReport payload does not match the frozen schema; got keys "
                f"{sorted(payload)}, expected {sorted(expected)}"
            )
        return cls(
            title=payload["title"],
            metrics=[GapMetric.from_dict(d) for d in payload["metrics"]],
        )


def emission_gap(luminosity: float, target_impulse: float, duration: float) -> GapMetric:
    """Ledger row: achieved GW luminosity versus the luminosity a radiation-
    pressure-only mechanism would need to deliver ``target_impulse`` over
    ``duration``.

    ``required = (target_impulse / duration) * c``, inverting the standard
    radiation-pressure relation ``F = P / c`` (momentum flux of any field
    radiating at speed ``c`` — the same assumption underlying
    ``docs/PHYSICS.md`` §"assuming radiated power converts to thrust", and the
    one :func:`gwtb.target.coupling.channel_absorption` (T-8.4) uses
    explicitly). This is the naive best case: it assumes every watt radiated
    converts to thrust with no loss, so the reported gap is optimistic, not
    conservative.

    Parameters
    ----------
    luminosity
        Achieved GW power, W. From :func:`gwtb.source.quadrupole.luminosity`
        or a comparable source. Must be finite and non-negative.
    target_impulse
        Required momentum transfer, N s. Must be finite and positive.
    duration
        Time over which the impulse is delivered, s. Must be finite and
        positive.

    Returns
    -------
    GapMetric
        ``name="emission magnitude"``, ``units="W"``,
        ``source_module="gwtb.source.quadrupole"``.
    """
    if not math.isfinite(duration) or duration <= 0.0:
        raise ValueError(f"duration must be positive and finite, got {duration!r}")
    if not math.isfinite(target_impulse) or target_impulse <= 0.0:
        raise ValueError(f"target_impulse must be positive and finite, got {target_impulse!r}")

    required = (target_impulse / duration) * c
    return GapMetric(
        name="emission magnitude",
        achieved=luminosity,
        required=required,
        units="W",
        source_module="gwtb.source.quadrupole",
    )


def aperture_gap(
    geometry: ArrayLike, wavelength: float, range_m: float, spot_size: float
) -> GapMetric:
    """Ledger row: achieved aperture-to-wavelength ratio versus the ratio
    required to hit a target focal spot size.

    ``required = range_m / spot_size``, inverting the diffraction-limit
    scaling ``w ~ lambda r / D`` (:func:`gwtb.array.focus.spot_size`,
    ``docs/PHYSICS.md``) to ``D/lambda ~ r/w``. This is
    **frequency-independent by construction**: ``required`` involves only
    ``range_m`` and the target ``spot_size``, never ``wavelength`` — the same
    finding :func:`gwtb.array.focus.spot_size` states from the other side (a
    1 km spot at 40 AU needs ``D/lambda >~ 6e9`` regardless of drive
    frequency).

    ``achieved`` uses the same aperture definition as
    :func:`gwtb.array.focus.spot_size` (maximum pairwise element separation),
    so the two are directly comparable.

    Parameters
    ----------
    geometry
        Shape ``(N, 3)``, m. Element positions, per ADR-0002 §1.
    wavelength
        Radiation wavelength, m. Must be positive and finite.
    range_m
        Target range, m. Must be positive and finite.
    spot_size
        Target focal spot size, m. Must be positive and finite.

    Returns
    -------
    GapMetric
        ``name="aperture"``, ``units="D/lambda"``,
        ``source_module="gwtb.array.focus"``.
    """
    positions = as_body_array(geometry, "geometry")
    if not np.isfinite(wavelength) or wavelength <= 0.0:
        raise ValueError(f"wavelength must be positive and finite, got {wavelength!r}")
    if not np.isfinite(range_m) or range_m <= 0.0:
        raise ValueError(f"range_m must be positive and finite, got {range_m!r}")
    if not np.isfinite(spot_size) or spot_size <= 0.0:
        raise ValueError(f"spot_size must be positive and finite, got {spot_size!r}")

    diameter = float(np.max(np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=-1)))
    if diameter == 0.0:
        raise ValueError("geometry has zero extent (all elements coincide)")

    return GapMetric(
        name="aperture",
        achieved=diameter / wavelength,
        required=range_m / spot_size,
        units="D/lambda",
        source_module="gwtb.array.focus",
    )


def impulse_gap(
    achieved_impulse: float,
    required_impulse: float = 1.4e10,
    source_module: str = "gwtb.target.deflection",
) -> GapMetric:
    """Ledger row: achieved momentum transfer versus the requirement.

    Default ``required_impulse`` is the 1 km asteroid figure used throughout
    this project (``docs/PHYSICS.md``: ~1.4e10 N s for 0.01 m/s of Δv on a
    1.4e12 kg body). The canonical ``achieved_impulse`` to compare it against
    is DART's ~1.16e7 N s (Daly et al., *Nature* 616, 443 (2023)) — see
    :func:`gwtb.target.deflection.delta_v`.

    Parameters
    ----------
    achieved_impulse
        N s. Must be finite and non-negative.
    required_impulse
        N s. Must be positive and finite.
    source_module
        Dotted path of the module that computed ``achieved_impulse``.

    Returns
    -------
    GapMetric
        ``name="impulse"``, ``units="N s"``.
    """
    return GapMetric(
        name="impulse",
        achieved=achieved_impulse,
        required=required_impulse,
        units="N s",
        source_module=source_module,
    )


def focusing_gap(name: str, achieved: float, required: float, units: str) -> GapMetric:
    """Ledger row for a focusing metric (spot size, dwell time, peak-to-
    sidelobe ratio, or required aperture).

    A thin, explicit wrapper rather than four separate near-identical
    functions: each focusing metric already has its own computation
    (:mod:`gwtb.array.focus`) and its own natural "required" value supplied
    by the caller — this only assembles the frozen row.

    Parameters
    ----------
    name
        e.g. ``"spot size"``, ``"dwell time"``, ``"peak-to-sidelobe ratio"``,
        ``"required aperture"``.
    achieved
        In ``units``. Must be finite and non-negative.
    required
        In ``units``. Must be positive and finite.
    units
        e.g. ``"m"``, ``"s"``, ``"dimensionless"``.

    Returns
    -------
    GapMetric
        ``source_module="gwtb.array.focus"``.
    """
    return GapMetric(
        name=name,
        achieved=achieved,
        required=required,
        units=units,
        source_module="gwtb.array.focus",
    )


def _git_sha(root: str | None = None) -> str | None:
    """Best-effort current commit SHA, or ``None`` outside a git checkout."""
    import subprocess

    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None


@dataclass(frozen=True)
class RunManifest:
    """A record of exactly what produced a run's results, for reproducibility.

    Attributes
    ----------
    package_version
        ``gwtb.__version__``, or ``"unknown"`` if unavailable.
    git_sha
        Current commit hash, or ``None`` outside a git checkout.
    parameters
        The run's full parameter set, as a JSON-serializable mapping.
    seeds
        Named RNG seeds used, e.g. ``{"sparse_array": 7}``.
    """

    package_version: str
    git_sha: str | None
    parameters: dict[str, Any]
    seeds: dict[str, int]

    def to_json(self, indent: int = 2) -> str:
        """Serialize to a JSON string."""
        return json.dumps(
            {
                "package_version": self.package_version,
                "git_sha": self.git_sha,
                "parameters": self.parameters,
                "seeds": self.seeds,
            },
            indent=indent,
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, text: str) -> RunManifest:
        """Inverse of :meth:`to_json`."""
        payload = json.loads(text)
        expected = {"package_version", "git_sha", "parameters", "seeds"}
        if set(payload) != expected:
            raise ValueError(
                f"RunManifest payload does not match the schema; got keys "
                f"{sorted(payload)}, expected {sorted(expected)}"
            )
        return cls(**payload)


def run_manifest(
    parameters: dict[str, Any], seeds: dict[str, int] | None = None, root: str | None = None
) -> RunManifest:
    """Build a :class:`RunManifest` for the current package and commit.

    Parameters
    ----------
    parameters
        The run's full parameter set. Must be JSON-serializable.
    seeds
        Named RNG seeds used in the run. Defaults to empty.
    root
        Repository root to run ``git rev-parse`` in, or ``None`` for the
        current working directory.

    Returns
    -------
    RunManifest
    """
    try:
        from gwtb import __version__ as package_version
    except ImportError:
        package_version = "unknown"

    # Round-trip through JSON immediately: fails loudly here, at manifest
    # construction, rather than later when someone tries to persist it.
    json.dumps(parameters)

    return RunManifest(
        package_version=package_version,
        git_sha=_git_sha(root),
        parameters=parameters,
        seeds=dict(seeds) if seeds else {},
    )


__all__ = [
    "GapMetric",
    "GapReport",
    "RunManifest",
    "aperture_gap",
    "emission_gap",
    "focusing_gap",
    "impulse_gap",
    "run_manifest",
]
