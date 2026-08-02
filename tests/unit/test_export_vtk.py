"""Unit tests for gwtb.viz.export_vtk.export_field (T-7.8).

PyVista is not installed in this environment; export_field requires it
(unlike render_volume, it has no partial-degradation path, since a .vti
writer with no VTK-ecosystem library serves no purpose), so these tests
confirm the clear-failure behavior directly and skip the round-trip tests
that need PyVista actually present.
"""

from __future__ import annotations

import numpy as np
import pytest

from gwtb.viz.export_vtk import export_field


def _has_pyvista() -> bool:
    try:
        import pyvista  # noqa: F401

        return True
    except ImportError:
        return False


def test_raises_a_clear_error_without_pyvista(tmp_path) -> None:
    if _has_pyvista():
        pytest.skip("pyvista is installed; this test exercises the absent-pyvista path")

    values = np.random.default_rng(0).uniform(-1.0, 1.0, size=(4, 4, 4))
    with pytest.raises(RuntimeError, match="pyvista"):
        export_field(values, extent=10.0, path=str(tmp_path / "out.vti"))


def test_reloads_via_pyvista_read_with_matching_shape_and_values(tmp_path) -> None:
    """AC: output reloads via pyvista.read with matching shape and values to
    rtol 1e-12."""
    if not _has_pyvista():
        pytest.skip("pyvista not installed")
    import pyvista as pv

    rng = np.random.default_rng(1)
    values = rng.uniform(-5.0, 5.0, size=(6, 5, 4))
    path = str(tmp_path / "field.vti")
    export_field(values, extent=100.0, path=path)

    reloaded = pv.read(path)
    reloaded_values = np.asarray(reloaded.point_data["field"]).reshape(values.shape, order="F")
    np.testing.assert_allclose(reloaded_values, values, rtol=1e-12)


def test_rejects_wrong_dimensionality(tmp_path) -> None:
    with pytest.raises(ValueError, match=r"\(nx, ny, nz\)"):
        export_field(np.zeros((4, 4)), 10.0, str(tmp_path / "x.vti"))


def test_rejects_non_positive_extent(tmp_path) -> None:
    with pytest.raises(ValueError, match="extent"):
        export_field(np.zeros((2, 2, 2)), 0.0, str(tmp_path / "x.vti"))
