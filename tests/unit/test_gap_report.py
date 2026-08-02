"""Unit tests for gwtb.ledger.gap_report (T-2.6).

T-2.6 is marked **freeze**: every epic writes rows into this schema. The tests
below therefore guard the *contract* — the exact field set, the JSON
round-trip, and byte-stability of the rendered table — not merely that the
code runs.
"""

from __future__ import annotations

import json
import math
from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from gwtb.array.geometry import linear_array, planar_array
from gwtb.core.constants import AU, c
from gwtb.ledger.gap_report import GapMetric, GapReport, aperture_gap, emission_gap, impulse_gap
from gwtb.source.conservation import UNPHYSICAL_STAMP, StampedResult


def _metric(name: str = "radiated power", achieved: float = 1e-19) -> GapMetric:
    return GapMetric(
        name=name,
        achieved=achieved,
        required=1.0,
        units="W",
        source_module="gwtb.source.quadrupole",
    )


# --- the frozen field set --------------------------------------------------


def test_frozen_field_set_is_exactly_as_specified() -> None:
    """Guards the freeze: T-2.6 fixes these names, in this order.

    ``provenance`` was added 2026-07-31, the day the freeze was set, to close a
    Critical review finding: without it a stamped result had to be unwrapped to
    ``.value`` at the call site, discarding the UNPHYSICAL provenance. It
    defaults to ``None`` so five-argument construction is unaffected.
    """
    assert [f for f in GapMetric.__dataclass_fields__] == [
        "name",
        "achieved",
        "required",
        "units",
        "source_module",
        "provenance",
    ]


def test_five_argument_construction_still_works() -> None:
    """The amendment must not have broken any existing call site."""
    m = GapMetric("strain", 1e-40, 1e-21, "dimensionless", "gwtb.propagate.retarded")
    assert m.provenance is None
    assert m.is_unphysical is False


def test_constructs_positionally_in_the_frozen_order() -> None:
    m = GapMetric("strain", 1e-40, 1e-21, "dimensionless", "gwtb.propagate.retarded")
    assert m.name == "strain"
    assert m.achieved == 1e-40
    assert m.units == "dimensionless"


def test_metric_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        _metric().achieved = 5.0  # type: ignore[misc]


# --- gap arithmetic --------------------------------------------------------


def test_gap_decades_is_log10_of_the_shortfall() -> None:
    m = GapMetric("p", achieved=1e-19, required=1e0, units="W", source_module="m")
    assert m.gap_decades == pytest.approx(19.0)


def test_gap_decades_is_negative_when_requirement_is_exceeded() -> None:
    m = GapMetric("p", achieved=1e3, required=1e0, units="W", source_module="m")
    assert m.gap_decades == pytest.approx(-3.0)
    assert m.meets_requirement is True


def test_gap_decades_is_zero_when_met_exactly() -> None:
    m = GapMetric("p", achieved=2.0, required=2.0, units="W", source_module="m")
    assert m.gap_decades == pytest.approx(0.0)
    assert m.meets_requirement is True


def test_zero_achievement_is_an_infinite_gap_not_an_error() -> None:
    """A wall is a finding (CLAUDE.md rule 5) — it must stay visible."""
    m = GapMetric("p", achieved=0.0, required=1.0, units="W", source_module="m")
    assert math.isinf(m.gap_decades)
    assert m.meets_requirement is False


# --- validation ------------------------------------------------------------


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"name": ""}, "name"),
        ({"units": ""}, "units"),
        ({"source_module": ""}, "source_module"),
        ({"achieved": -1.0}, "achieved"),
        ({"achieved": math.nan}, "achieved"),
        ({"achieved": math.inf}, "achieved"),
        ({"required": 0.0}, "required"),
        ({"required": -1.0}, "required"),
        ({"required": math.inf}, "required"),
    ],
)
def test_invalid_fields_are_rejected(kwargs: dict, match: str) -> None:
    base = {
        "name": "p",
        "achieved": 1.0,
        "required": 1.0,
        "units": "W",
        "source_module": "m",
    }
    with pytest.raises(ValueError, match=match):
        GapMetric(**{**base, **kwargs})


# --- AC: the schema round-trips through JSON ------------------------------


def test_metric_round_trips_through_json() -> None:
    original = _metric()
    restored = GapMetric.from_dict(json.loads(json.dumps(original.to_dict())))
    assert restored == original


def test_report_round_trips_through_json() -> None:
    report = GapReport(title="Sprint 2 ledger")
    report.add(_metric("radiated power", 1e-19))
    report.add(_metric("strain at 40 AU", 1e-40))

    restored = GapReport.from_json(report.to_json())

    assert restored.title == report.title
    assert restored.metrics == report.metrics


def test_round_trip_preserves_row_order() -> None:
    report = GapReport()
    for i in range(5):
        report.add(_metric(f"metric {i}", achieved=10.0**-i))
    restored = GapReport.from_json(report.to_json())
    assert [m.name for m in restored] == [f"metric {i}" for i in range(5)]


def test_round_trip_is_idempotent() -> None:
    report = GapReport()
    report.add(_metric())
    once = report.to_json()
    twice = GapReport.from_json(once).to_json()
    assert once == twice


def test_derived_quantities_are_not_serialized() -> None:
    """Recomputed on load, so a stored ledger cannot disagree with itself.

    ``provenance`` *is* stored — it is source data, not derived.
    ``is_unphysical`` is derived from it and is not.
    """
    payload = json.loads(GapReport(metrics=[_metric()]).to_json())
    assert set(payload["metrics"][0]) == {
        "name",
        "achieved",
        "required",
        "units",
        "source_module",
        "provenance",
    }


def test_unknown_key_is_rejected_rather_than_ignored() -> None:
    payload = _metric().to_dict()
    payload["gap_decades"] = 19.0
    with pytest.raises(ValueError, match="unknown"):
        GapMetric.from_dict(payload)


def test_missing_key_is_rejected() -> None:
    payload = _metric().to_dict()
    del payload["units"]
    with pytest.raises(ValueError, match="missing"):
        GapMetric.from_dict(payload)


def test_report_with_unexpected_top_level_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="schema"):
        GapReport.from_json(json.dumps({"title": "t", "metrics": [], "extra": 1}))


# --- AC: to_markdown renders a stable table -------------------------------


def test_to_markdown_is_byte_stable_across_calls() -> None:
    report = GapReport()
    report.add(_metric("radiated power", 1e-19))
    report.add(_metric("strain at 40 AU", 1e-40))
    assert report.to_markdown() == report.to_markdown()


def test_to_markdown_is_stable_across_equivalent_reports() -> None:
    def build() -> GapReport:
        r = GapReport(title="Ledger")
        r.add(_metric("radiated power", 1e-19))
        r.add(_metric("strain at 40 AU", 1e-40))
        return r

    assert build().to_markdown() == build().to_markdown()


def test_to_markdown_has_a_header_and_one_row_per_metric() -> None:
    report = GapReport()
    report.add(_metric("a", 1e-19))
    report.add(_metric("b", 1e-9))
    lines = [ln for ln in report.to_markdown().splitlines() if ln.startswith("|")]
    assert len(lines) == 4  # header, separator, two rows
    assert lines[0].startswith("| Metric | Achieved | Required | Units |")


def test_to_markdown_reports_the_gap_in_decades() -> None:
    report = GapReport()
    report.add(_metric("radiated power", 1e-19))
    assert "| 19.0 |" in report.to_markdown()


def test_to_markdown_spells_out_an_infinite_gap() -> None:
    report = GapReport()
    report.add(_metric("dead channel", achieved=0.0))
    rendered = report.to_markdown()
    assert "no achievement" in rendered
    assert "inf" not in rendered


def test_empty_report_says_so_explicitly() -> None:
    """An empty ledger must not be mistakable for one with nothing to report."""
    assert "_No metrics recorded._" in GapReport().to_markdown()


# --- add() semantics -------------------------------------------------------


def test_duplicate_name_is_rejected() -> None:
    report = GapReport()
    report.add(_metric("radiated power"))
    with pytest.raises(ValueError, match="already in this report"):
        report.add(_metric("radiated power"))


def test_duplicate_name_in_the_constructor_is_rejected() -> None:
    with pytest.raises(ValueError, match="already in this report"):
        GapReport(metrics=[_metric("p"), _metric("p")])


def test_add_rejects_a_non_metric() -> None:
    with pytest.raises(TypeError, match="GapMetric"):
        GapReport().add({"name": "p"})  # type: ignore[arg-type]


# --- the UNPHYSICAL stamp reaches the ledger (Critical review finding) ---


def test_from_stamped_carries_the_unphysical_provenance() -> None:
    """The gap this closes: a stamped result must not lose its stamp here."""
    stamped = StampedResult.unphysical(np.array(1e-9), reason="mass dipole, T-2.4")
    metric = GapMetric.from_stamped(
        "radiated power", stamped, 1.0, "W", "gwtb.source.multipole_rad"
    )
    assert metric.is_unphysical is True
    assert metric.provenance is not None
    assert UNPHYSICAL_STAMP in metric.provenance
    assert "mass dipole" in metric.provenance
    assert metric.achieved == pytest.approx(1e-9)


def test_from_stamped_keeps_a_physical_result_unflagged() -> None:
    metric = GapMetric.from_stamped(
        "radiated power", StampedResult.physical(np.array(1e-9)), 1.0, "W", "m"
    )
    assert metric.is_unphysical is False
    assert metric.provenance is None


def test_from_stamped_rejects_a_non_scalar() -> None:
    """A ledger row is one number."""
    with pytest.raises(ValueError, match="single number"):
        GapMetric.from_stamped("p", StampedResult.unphysical(np.array([1.0, 2.0])), 1.0, "W", "m")


def test_from_stamped_rejects_a_bare_float() -> None:
    with pytest.raises(TypeError, match="StampedResult"):
        GapMetric.from_stamped("p", 1.0, 1.0, "W", "m")  # type: ignore[arg-type]


def test_unphysical_row_is_marked_in_the_rendered_table() -> None:
    report = GapReport()
    report.add(
        GapMetric.from_stamped(
            "dipole power",
            StampedResult.unphysical(np.array(1e10), reason="no reaction mass"),
            1.0,
            "W",
            "gwtb.source.multipole_rad",
        )
    )
    rendered = report.to_markdown()
    assert "UNPHYSICAL" in rendered
    assert "no reaction mass" in rendered
    # The warning must explain *why* the row cannot be read as performance.
    assert "10^10" in rendered


def test_physical_report_renders_no_unphysical_warning() -> None:
    report = GapReport()
    report.add(_metric())
    assert "UNPHYSICAL" not in report.to_markdown()


def test_provenance_survives_the_json_round_trip() -> None:
    report = GapReport()
    report.add(
        GapMetric.from_stamped(
            "dipole power",
            StampedResult.unphysical(np.array(1e10), reason="no reaction mass"),
            1.0,
            "W",
            "m",
        )
    )
    restored = GapReport.from_json(report.to_json())
    assert restored.metrics[0].is_unphysical is True
    assert restored.metrics == report.metrics


# --- emission_gap (T-2.7) --------------------------------------------------


def _rod_luminosity() -> float:
    """The T-2.8 closed form, 10 t / 10 m / 1 kHz: P = (2/45)(G/c^5) M^2 L^4 w^6."""
    from gwtb.core.constants import G_OVER_C5

    m, length, omega = 1.0e4, 10.0, 2.0 * math.pi * 1.0e3
    return (2.0 / 45.0) * G_OVER_C5 * m**2 * length**4 * omega**6


def test_emission_gap_achieved_matches_rod_luminosity_within_half_a_decade() -> None:
    """AC: for the 10 t / 10 m / 1 kHz rod, reports a gap within 0.5 decades
    of 1e-19 W."""
    luminosity = _rod_luminosity()
    metric = emission_gap(luminosity, target_impulse=1.4e10, duration=3.15e8)
    assert metric.achieved == pytest.approx(luminosity)
    assert abs(math.log10(metric.achieved / 1e-19)) < 0.5


def test_emission_gap_required_inverts_f_equals_p_over_c() -> None:
    metric = emission_gap(1.0, target_impulse=10.0, duration=2.0)
    assert metric.required == pytest.approx((10.0 / 2.0) * c)


def test_emission_gap_has_the_frozen_row_identity() -> None:
    metric = emission_gap(1e-19, target_impulse=1.0, duration=1.0)
    assert metric.name == "emission magnitude"
    assert metric.units == "W"
    assert metric.source_module == "gwtb.source.quadrupole"


def test_emission_gap_rejects_non_positive_duration() -> None:
    with pytest.raises(ValueError, match="duration"):
        emission_gap(1.0, target_impulse=1.0, duration=0.0)


def test_emission_gap_rejects_non_positive_target_impulse() -> None:
    with pytest.raises(ValueError, match="target_impulse"):
        emission_gap(1.0, target_impulse=-1.0, duration=1.0)


def test_emission_gap_fits_in_a_report() -> None:
    report = GapReport()
    report.add(emission_gap(_rod_luminosity(), target_impulse=1.4e10, duration=3.15e8))
    assert "emission magnitude" in report.to_markdown()


# --- aperture_gap (T-5.9) ---------------------------------------------------


def test_aperture_gap_required_matches_6e9_for_a_1km_spot_at_40au() -> None:
    """AC: within 0.5 decades of 6e9, at any frequency."""
    geometry = linear_array(2, 1.0e4)
    for wavelength in (3.0e6, 3.0e5, 3.0e2, 3.0e-2):  # 100 Hz .. 1e10 Hz
        metric = aperture_gap(geometry, wavelength, range_m=40.0 * AU, spot_size=1.0e3)
        assert abs(math.log10(metric.required / 6.0e9)) < 0.5, wavelength


def test_aperture_gap_required_is_independent_of_wavelength() -> None:
    """The frequency-independence is the assertion (BACKLOG.md T-5.9)."""
    geometry = linear_array(2, 1.0e4)
    required_values = {
        aperture_gap(geometry, wl, range_m=40.0 * AU, spot_size=1.0e3).required
        for wl in (1.0, 100.0, 1.0e6)
    }
    assert len(required_values) == 1


def test_aperture_gap_achieved_is_diameter_over_wavelength() -> None:
    geometry = planar_array(4, 4, 100.0, 100.0)
    diameter = float(np.max(np.linalg.norm(geometry[:, None, :] - geometry[None, :, :], axis=-1)))
    metric = aperture_gap(geometry, wavelength=10.0, range_m=1.0e9, spot_size=1.0)
    assert metric.achieved == pytest.approx(diameter / 10.0, rel=1e-12)


def test_aperture_gap_row_identity() -> None:
    metric = aperture_gap(linear_array(2, 10.0), 1.0, 1.0e9, 1.0)
    assert metric.name == "aperture"
    assert metric.units == "D/lambda"
    assert metric.source_module == "gwtb.array.focus"


def test_aperture_gap_rejects_zero_extent_array() -> None:
    with pytest.raises(ValueError, match="zero extent"):
        aperture_gap(np.zeros((4, 3)), 1.0, 1.0e9, 1.0)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"wavelength": 0.0}, "wavelength"),
        ({"wavelength": -1.0}, "wavelength"),
        ({"range_m": 0.0}, "range_m"),
        ({"spot_size": 0.0}, "spot_size"),
    ],
)
def test_aperture_gap_rejects_invalid_scalars(kwargs: dict, match: str) -> None:
    base = {
        "geometry": linear_array(2, 10.0),
        "wavelength": 1.0,
        "range_m": 1.0e9,
        "spot_size": 1.0,
    }
    with pytest.raises(ValueError, match=match):
        aperture_gap(**{**base, **kwargs})


# --- impulse_gap (T-8.9) ----------------------------------------------------


def test_impulse_gap_default_matches_the_1km_asteroid_requirement() -> None:
    metric = impulse_gap(achieved_impulse=1.16e7)
    assert metric.required == pytest.approx(1.4e10)


def test_impulse_gap_dart_achieved_is_seven_decades_short() -> None:
    """AC: benchmarked against DART (1.16e7 N s) and the 1 km requirement
    (1.4e10 N s)."""
    metric = impulse_gap(achieved_impulse=1.16e7)
    assert metric.gap_decades == pytest.approx(math.log10(1.4e10 / 1.16e7), rel=1e-9)
    assert 2.5 < metric.gap_decades < 3.5


def test_impulse_gap_row_identity() -> None:
    metric = impulse_gap(achieved_impulse=1.16e7)
    assert metric.name == "impulse"
    assert metric.units == "N s"


def test_impulse_gap_custom_requirement() -> None:
    metric = impulse_gap(achieved_impulse=100.0, required_impulse=1000.0)
    assert metric.required == 1000.0
    assert metric.gap_decades == pytest.approx(1.0)


def test_len_and_iteration() -> None:
    report = GapReport()
    report.add(_metric("a"))
    report.add(_metric("b"))
    assert len(report) == 2
    assert [m.name for m in report] == ["a", "b"]
