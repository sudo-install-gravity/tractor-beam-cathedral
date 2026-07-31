"""Unit tests for gwtb.source.conservation.StampedResult (T-2.2).

The acceptance criterion has two halves, and they pull in opposite directions:
the stamp must survive *ordinary* use (arithmetic, slicing, ``str()``), and it
must refuse to be dropped by ``np.asarray``. See
``docs/adr/0005-unphysical-stamp-propagation.md`` for why an ``ndarray``
subclass satisfies only the first.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from gwtb.source.conservation import (
    UNPHYSICAL_STAMP,
    StampedResult,
    StampStrippedError,
)


def _stamped() -> StampedResult:
    return StampedResult.unphysical(np.array([1.0, 2.0, 3.0]), reason="test fixture")


def _clean() -> StampedResult:
    return StampedResult.physical(np.array([1.0, 2.0, 3.0]))


# --- construction ----------------------------------------------------------


def test_physical_carries_no_stamp() -> None:
    assert _clean().is_unphysical is False
    assert _clean().provenance is None


def test_unphysical_carries_the_exact_stamp_text() -> None:
    r = _stamped()
    assert r.is_unphysical is True
    assert r.provenance is not None
    assert UNPHYSICAL_STAMP in r.provenance
    assert "test fixture" in r.provenance


def test_unphysical_without_reason_is_the_bare_stamp() -> None:
    assert StampedResult.unphysical([1.0]).provenance == UNPHYSICAL_STAMP


# --- AC: the stamp survives arithmetic ------------------------------------


@pytest.mark.parametrize(
    "op",
    [
        lambda r: r + 1.0,
        lambda r: 1.0 + r,
        lambda r: r - 1.0,
        lambda r: 1.0 - r,
        lambda r: r * 2.0,
        lambda r: 2.0 * r,
        lambda r: r / 2.0,
        lambda r: 2.0 / r,
        lambda r: r**2,
        lambda r: -r,
        lambda r: abs(r),
    ],
)
def test_stamp_survives_arithmetic(op) -> None:
    result = op(_stamped())
    assert isinstance(result, StampedResult)
    assert result.is_unphysical is True


def test_stamp_survives_ufuncs_and_reductions() -> None:
    r = _stamped()
    assert np.sin(r).is_unphysical is True
    assert np.add.reduce(r).is_unphysical is True


def test_stamp_survives_arithmetic_with_a_plain_ndarray() -> None:
    """The dangerous direction: ndarray on the left, stamped on the right.

    Without ``__array_priority__`` NumPy would broadcast into a plain ndarray
    and the wrapper — with its stamp — would simply disappear.
    """
    result = np.array([1.0, 1.0, 1.0]) + _stamped()
    assert isinstance(result, StampedResult)
    assert result.is_unphysical is True


def test_unphysicality_is_contagious_across_operands() -> None:
    """A clean operand does not launder a stamped one."""
    result = _clean() + _stamped()
    assert isinstance(result, StampedResult)
    assert result.is_unphysical is True


def test_clean_operands_stay_clean() -> None:
    result = _clean() + _clean()
    assert isinstance(result, StampedResult)
    assert result.is_unphysical is False


def test_two_distinct_provenances_are_both_named() -> None:
    a = StampedResult.unphysical([1.0], reason="source A")
    b = StampedResult.unphysical([1.0], reason="source B")
    merged = a + b
    assert merged.provenance is not None
    assert "source A" in merged.provenance
    assert "source B" in merged.provenance


# --- AC: the stamp survives slicing ---------------------------------------


def test_stamp_survives_slicing() -> None:
    sliced = _stamped()[1:]
    assert isinstance(sliced, StampedResult)
    assert sliced.is_unphysical is True
    np.testing.assert_array_equal(sliced.value, np.array([2.0, 3.0]))


def test_stamp_survives_scalar_indexing() -> None:
    assert _stamped()[0].is_unphysical is True


# --- AC: the stamp survives str() -----------------------------------------


def test_str_carries_the_stamp() -> None:
    assert UNPHYSICAL_STAMP in str(_stamped())


def test_repr_carries_the_stamp() -> None:
    assert UNPHYSICAL_STAMP in repr(_stamped())


def test_clean_result_renders_without_a_stamp() -> None:
    assert UNPHYSICAL_STAMP not in str(_clean())
    assert UNPHYSICAL_STAMP not in repr(_clean())


# --- AC: the stamp cannot be silently dropped by np.asarray ---------------


def test_np_asarray_refuses_to_strip_the_stamp() -> None:
    with pytest.raises(StampStrippedError, match="UNPHYSICAL"):
        np.asarray(_stamped())


def test_np_array_refuses_to_strip_the_stamp() -> None:
    with pytest.raises(StampStrippedError, match="UNPHYSICAL"):
        np.array(_stamped())


def test_float_coercion_refuses_to_strip_the_stamp() -> None:
    with pytest.raises(StampStrippedError):
        np.asarray(StampedResult.unphysical(np.array([1.0])))


def test_out_parameter_is_refused() -> None:
    """``out=`` would move the numbers where provenance cannot follow."""
    destination = np.empty(3)
    with pytest.raises(StampStrippedError, match="out="):
        np.add(_stamped(), 1.0, out=destination)


def test_asarray_succeeds_for_an_unstamped_result() -> None:
    """The guard is on the stamp, not on the wrapper — clean values convert."""
    arr = np.asarray(_clean())
    assert isinstance(arr, np.ndarray)
    np.testing.assert_array_equal(arr, np.array([1.0, 2.0, 3.0]))


def test_value_is_the_explicit_documented_escape_hatch() -> None:
    """Taking `.value` is allowed — it is explicit and greppable in review."""
    raw = _stamped().value
    assert isinstance(raw, np.ndarray)
    np.testing.assert_array_equal(raw, np.array([1.0, 2.0, 3.0]))


def test_there_is_no_unstamp_method() -> None:
    """A method named `unstamp` would imply removing the stamp is supported."""
    assert not hasattr(StampedResult, "unstamp")


# --- AC: serialization carries the stamp ----------------------------------


def test_to_json_carries_the_stamp() -> None:
    payload = _stamped().to_json()
    assert payload["is_unphysical"] is True
    assert UNPHYSICAL_STAMP in payload["provenance"]
    assert payload["value"] == [1.0, 2.0, 3.0]


def test_to_json_round_trips_through_the_json_module() -> None:
    text = json.dumps(_stamped().to_json())
    assert UNPHYSICAL_STAMP in text
    restored = StampedResult(json.loads(text)["value"], json.loads(text)["provenance"])
    assert restored.is_unphysical is True


def test_json_dumps_of_the_raw_object_fails_rather_than_silently_dropping() -> None:
    """`json.dumps` on the wrapper must not produce stamp-free output."""
    with pytest.raises(TypeError):
        json.dumps(_stamped())


# --- housekeeping ----------------------------------------------------------


def test_is_unhashable_like_ndarray() -> None:
    with pytest.raises(TypeError):
        hash(_stamped())


def test_len_and_getitem_delegate_to_the_value() -> None:
    assert len(_stamped()) == 3
