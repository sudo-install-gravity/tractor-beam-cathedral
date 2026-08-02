"""ParaView/VTK export of a field slice or volume, via the optional PyVista
dependency (the same optional dependency as :mod:`gwtb.viz.volume`).

Not a physics module (``viz/`` is exempt from the citation-CI check).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def _pyvista_module() -> object:
    """Import PyVista, or raise a clear error if it is not installed."""
    try:
        import pyvista as pv
    except ImportError as exc:
        raise RuntimeError(
            "export_field requires the optional 'pyvista' dependency, which "
            "is not installed (BACKLOG.md T-7.8). Install it with `pip "
            "install pyvista` to write .vti files."
        ) from exc
    return pv


def export_field(values: NDArray[np.float64], extent: float, path: str) -> None:
    """Write a scalar field grid to a ParaView-readable ``.vti`` file.

    Parameters
    ----------
    values
        Shape ``(nx, ny, nz)``, the scalar field on a uniform grid spanning
        ``[-extent, extent]`` on each axis.
    extent
        m. Must be positive and finite.
    path
        Output file path, conventionally ending in ``.vti``.

    Raises
    ------
    RuntimeError
        If PyVista is not installed.
    """
    if values.ndim != 3:
        raise ValueError(f"values must have shape (nx, ny, nz), got {values.shape}")
    if not np.isfinite(extent) or extent <= 0.0:
        raise ValueError(f"extent must be positive and finite, got {extent!r}")

    pv = _pyvista_module()
    nx, ny, nz = values.shape
    spacing = (
        2.0 * extent / max(nx - 1, 1),
        2.0 * extent / max(ny - 1, 1),
        2.0 * extent / max(nz - 1, 1),
    )
    grid = pv.ImageData(  # type: ignore[attr-defined]
        dimensions=values.shape,
        spacing=spacing,
        origin=(-extent, -extent, -extent),
    )
    grid.point_data["field"] = values.flatten(order="F")
    grid.save(path)


__all__ = ["export_field"]
