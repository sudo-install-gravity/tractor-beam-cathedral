"""Unit tests for gwtb.viz.volume.render_volume (T-7.7).

PyVista is not installed in this environment, so these tests directly
exercise the AC's "skips cleanly" clause rather than skipping themselves.
"""

from __future__ import annotations

import pytest

from gwtb.viz.volume import render_volume


def _field(position: object) -> float:
    return 1.0


def test_skips_cleanly_without_pyvista(capsys) -> None:
    """AC: skips with a clear message when PyVista is not installed."""
    try:
        import pyvista  # noqa: F401

        pytest.skip("pyvista is installed; this test exercises the absent-pyvista path")
    except ImportError:
        pass

    result = render_volume(_field, extent=10.0, resolution=4)
    assert result is None
    captured = capsys.readouterr()
    assert "pyvista" in captured.out.lower()


def test_renders_offscreen_when_pyvista_is_present() -> None:
    """AC: renders offscreen otherwise."""
    try:
        import pyvista  # noqa: F401
    except ImportError:
        pytest.skip("pyvista not installed")

    result = render_volume(_field, extent=10.0, resolution=4)
    assert result is not None


def test_rejects_non_positive_extent() -> None:
    with pytest.raises(ValueError, match="extent"):
        render_volume(_field, extent=0.0, resolution=4)


def test_rejects_too_small_resolution() -> None:
    with pytest.raises(ValueError, match="resolution"):
        render_volume(_field, extent=10.0, resolution=1)
