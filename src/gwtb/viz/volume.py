"""3D volumetric field rendering, via the optional PyVista dependency.

Not a physics module (``viz/`` is exempt from the citation-CI check).
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray


def _pyvista_module() -> object:
    """Import PyVista, or raise a clear error if it is not installed."""
    try:
        import pyvista as pv
    except ImportError as exc:
        raise RuntimeError(
            "render_volume requires the optional 'pyvista' dependency, which "
            "is not installed (BACKLOG.md T-7.7). Install it with `pip install "
            "pyvista` to render volumetric fields."
        ) from exc
    return pv


def render_volume(
    field: Callable[[NDArray[np.float64]], float],
    extent: float,
    resolution: int,
    path: str | None = None,
) -> object | None:
    """Render a scalar field as a 3D volume, offscreen.

    Skips cleanly (returns ``None`` with a clear message) if PyVista is not
    installed, rather than raising or silently producing nothing — the
    caller's script can check for ``None`` and continue.

    Parameters
    ----------
    field
        Maps a shape ``(3,)`` position, m, to a scalar (e.g. one strain
        component, or its magnitude).
    extent
        m. The cubic volume spans ``[-extent, extent]`` on each axis. Must be
        positive and finite.
    resolution
        Number of grid points per axis. Must be at least 2.
    path
        If given, the rendered image is saved offscreen to this path.

    Returns
    -------
    object or None
        The PyVista plotter object if PyVista is installed and rendering
        succeeded, else ``None``.
    """
    if not np.isfinite(extent) or extent <= 0.0:
        raise ValueError(f"extent must be positive and finite, got {extent!r}")
    if resolution < 2:
        raise ValueError(f"resolution must be at least 2, got {resolution!r}")

    try:
        pv = _pyvista_module()
    except RuntimeError as exc:
        print(f"render_volume: skipping — {exc}")
        return None

    axis = np.linspace(-extent, extent, resolution)
    gx, gy, gz = np.meshgrid(axis, axis, axis, indexing="ij")
    values = np.empty((resolution, resolution, resolution), dtype=np.float64)
    for i in range(resolution):
        for j in range(resolution):
            for k in range(resolution):
                values[i, j, k] = field(np.array([gx[i, j, k], gy[i, j, k], gz[i, j, k]]))

    grid = pv.ImageData(  # type: ignore[attr-defined]
        dimensions=values.shape,
        spacing=(axis[1] - axis[0],) * 3,
        origin=(-extent, -extent, -extent),
    )
    grid.point_data["field"] = values.flatten(order="F")

    plotter = pv.Plotter(off_screen=True)  # type: ignore[attr-defined]
    plotter.add_volume(grid, scalars="field")
    if path is not None:
        plotter.screenshot(path)
    result: object = plotter
    return result


__all__ = ["render_volume"]
