"""2D field slices: extraction, static heatmaps, and propagation animation.

Rendering is forced headless (``Agg`` backend), matching
:mod:`gwtb.viz.patterns`. Not a physics module (``viz/`` is exempt from the
citation-CI check); the underlying strain evaluation is whatever the caller's
``field`` callable computes, which is expected to already be cited code (e.g.
:func:`gwtb.propagate.retarded.field_at`).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")

import matplotlib.animation as animation  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from numpy.typing import NDArray  # noqa: E402

_PLANE_AXES = {
    "xy": (0, 1, 2),
    "xz": (0, 2, 1),
    "yz": (1, 2, 0),
}


@dataclass(frozen=True)
class FieldSlice:
    """A 2D grid of strain values cut through a fixed-coordinate plane.

    Attributes
    ----------
    coord1, coord2
        Shape ``(resolution,)``, m. Grid coordinates along the slice's two
        in-plane axes.
    values
        Shape ``(resolution, resolution, 3, 3)``, dimensionless. The TT
        strain tensor evaluated at every grid point.
    plane
        Which coordinate plane was cut, e.g. ``"xy"``.
    fixed_coordinate
        m. The value held constant along the plane's normal axis.
    """

    coord1: NDArray[np.float64]
    coord2: NDArray[np.float64]
    values: NDArray[np.float64]
    plane: str
    fixed_coordinate: float


def extract_slice(
    field: Callable[[NDArray[np.float64]], NDArray[np.float64]],
    plane: str,
    extent: float,
    resolution: int,
    fixed_coordinate: float = 0.0,
) -> FieldSlice:
    """Evaluate a strain field over a 2D grid cut through one coordinate plane.

    ``field`` is a callable, not a precomputed 3D array — no volumetric field
    representation exists elsewhere in this codebase (:func:`gwtb.core.
    backend.field_grid` returns values at caller-supplied points, not a
    structured grid), so a slice is defined by evaluating the field's own
    computation at exactly the points the slice requires, rather than
    resampling a coarser structure that would need to exist first.

    Parameters
    ----------
    field
        Maps a shape ``(3,)`` position, m, to a shape ``(3, 3)`` TT strain
        tensor.
    plane
        One of ``"xy"``, ``"xz"``, ``"yz"`` — which two axes vary.
    extent
        m. The slice spans ``[-extent, extent]`` on each in-plane axis. Must
        be positive and finite.
    resolution
        Number of grid points per axis. Must be at least 2.
    fixed_coordinate
        m. Value held constant on the plane's normal axis.

    Returns
    -------
    FieldSlice
    """
    if plane not in _PLANE_AXES:
        raise ValueError(f"plane must be one of {sorted(_PLANE_AXES)}, got {plane!r}")
    if not np.isfinite(extent) or extent <= 0.0:
        raise ValueError(f"extent must be positive and finite, got {extent!r}")
    if resolution < 2:
        raise ValueError(f"resolution must be at least 2, got {resolution!r}")

    i1, i2, i_fixed = _PLANE_AXES[plane]
    coord1 = np.linspace(-extent, extent, resolution)
    coord2 = np.linspace(-extent, extent, resolution)

    values = np.empty((resolution, resolution, 3, 3), dtype=np.float64)
    for a, c1 in enumerate(coord1):
        for b, c2 in enumerate(coord2):
            position = np.zeros(3)
            position[i1] = c1
            position[i2] = c2
            position[i_fixed] = fixed_coordinate
            values[a, b] = field(position)

    return FieldSlice(
        coord1=coord1,
        coord2=coord2,
        values=values,
        plane=plane,
        fixed_coordinate=fixed_coordinate,
    )


def plot_strain_slice(field_slice: FieldSlice, component: tuple[int, int] = (0, 0)) -> Figure:
    """Render one strain-tensor component of a :class:`FieldSlice` as a 2D heatmap.

    Diverging colormap centered at zero, since strain is signed and zero is
    the physically meaningful reference (no strain), not the minimum of the
    data range.

    Parameters
    ----------
    field_slice
        From :func:`extract_slice`.
    component
        Which ``(i, j)`` of the ``(3, 3)`` strain tensor to plot.

    Returns
    -------
    matplotlib.figure.Figure
    """
    i, j = component
    data = field_slice.values[:, :, i, j]
    peak = float(np.max(np.abs(data))) or 1.0

    fig, ax = plt.subplots()
    im = ax.pcolormesh(
        field_slice.coord1,
        field_slice.coord2,
        data.T,
        cmap="RdBu_r",
        vmin=-peak,
        vmax=peak,
        shading="auto",
    )
    ax.set_xlabel(f"{field_slice.plane[0]} (m)")
    ax.set_ylabel(f"{field_slice.plane[1]} (m)")
    ax.set_aspect("equal")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(f"h_{{{i}{j}}}^TT (scaled strain reference)")
    return fig


def animate_propagation(
    field: Callable[[NDArray[np.float64], float], NDArray[np.float64]],
    plane: str,
    extent: float,
    resolution: int,
    times: NDArray[np.float64],
    path: str,
    component: tuple[int, int] = (0, 0),
) -> int:
    """Render an animated sequence of strain slices over time and write it to disk.

    Parameters
    ----------
    field
        Maps ``(position, t)`` to a shape ``(3, 3)`` TT strain tensor.
    plane, extent, resolution
        As for :func:`extract_slice`.
    times
        Shape ``(T,)``, s. One frame is rendered per requested time.
    path
        Output file path. The extension (``.mp4`` or ``.gif``) selects the
        writer; ``.gif`` uses Pillow (no external ``ffmpeg`` dependency),
        ``.mp4`` requires ``ffmpeg`` on ``PATH``.
    component
        Which ``(i, j)`` strain component to animate.

    Returns
    -------
    int
        Number of frames written — equal to ``len(times)``.
    """
    if times.ndim != 1 or times.size == 0:
        raise ValueError(f"times must have shape (T,), got {times.shape}")

    slices: list[FieldSlice] = []
    for t in times:

        def _snapshot(p: NDArray[np.float64], _t: float = float(t)) -> NDArray[np.float64]:
            return field(p, _t)

        slices.append(extract_slice(_snapshot, plane, extent, resolution))
    i, j = component
    peak = max(float(np.max(np.abs(s.values[:, :, i, j]))) for s in slices) or 1.0

    fig, ax = plt.subplots()
    im = ax.pcolormesh(
        slices[0].coord1,
        slices[0].coord2,
        slices[0].values[:, :, i, j].T,
        cmap="RdBu_r",
        vmin=-peak,
        vmax=peak,
        shading="auto",
    )
    ax.set_xlabel(f"{plane[0]} (m)")
    ax.set_ylabel(f"{plane[1]} (m)")
    ax.set_aspect("equal")
    fig.colorbar(im, ax=ax)

    def _update(frame: int):
        im.set_array(slices[frame].values[:, :, i, j].T.ravel())
        return (im,)

    anim = animation.FuncAnimation(fig, _update, frames=len(times), blit=True)
    writer = "pillow" if path.endswith(".gif") else "ffmpeg"
    anim.save(path, writer=writer)
    plt.close(fig)
    return len(times)


__all__ = ["FieldSlice", "animate_propagation", "extract_slice", "plot_strain_slice"]
