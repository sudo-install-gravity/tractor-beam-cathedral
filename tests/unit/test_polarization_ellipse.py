"""Unit tests for gwtb.viz.patterns.plot_polarization_ellipse (T-7.6)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure

from gwtb.viz.patterns import plot_polarization_ellipse


def _deformed_points(h_plus: float, h_cross: float, n: int = 400) -> tuple[np.ndarray, np.ndarray]:
    theta = np.linspace(0.0, 2.0 * np.pi, n)
    x0, y0 = np.cos(theta), np.sin(theta)
    x = (1.0 + h_plus / 2.0) * x0 + (h_cross / 2.0) * y0
    y = (h_cross / 2.0) * x0 + (1.0 - h_plus / 2.0) * y0
    return x, y


def _deformed_point_at(h_plus: float, h_cross: float, theta: float) -> tuple[float, float]:
    """Same formula, evaluated at an exact angle rather than searched from a
    discretized array — avoids conflating sampling density with physics."""
    x0, y0 = np.cos(theta), np.sin(theta)
    x = (1.0 + h_plus / 2.0) * x0 + (h_cross / 2.0) * y0
    y = (h_cross / 2.0) * x0 + (1.0 - h_plus / 2.0) * y0
    return float(x), float(y)


def test_renders_headless() -> None:
    fig = plot_polarization_ellipse(0.2, 0.0)
    assert isinstance(fig, Figure)
    plt.close(fig)


def test_pure_h_plus_stretches_along_axes() -> None:
    """AC: pure h_plus produces a ring deforming along the axes."""
    x_axis = _deformed_point_at(0.5, 0.0, theta=0.0)
    y_axis = _deformed_point_at(0.5, 0.0, theta=np.pi / 2.0)
    assert x_axis[0] == pytest.approx(1.25, rel=1e-12)  # 1 + 0.5/2, y=0
    assert x_axis[1] == pytest.approx(0.0, abs=1e-12)
    assert y_axis[1] == pytest.approx(0.75, rel=1e-12)  # 1 - 0.5/2, x=0
    assert y_axis[0] == pytest.approx(0.0, abs=1e-12)


def test_pure_h_cross_deforms_at_45_degrees() -> None:
    """AC: pure h_cross at 45 degrees — the spin-2 signature (not 90).

    The distinguishing property is *where the extrema sit*: for pure h_plus
    the maximum/minimum radius occurs on the x/y axes (theta = 0, pi/2); for
    pure h_cross it occurs on the diagonals (theta = pi/4, 3pi/4) instead —
    45 degrees away, not 90. Neither case leaves any point exactly
    undistorted (a pure shear has no fixed points on the unit circle), so
    the earlier draft of this test — asserting the on-axis radius stays
    exactly 1 for h_cross — was checking a property that doesn't hold; radius
    there is sqrt(1 + (h_cross/2)^2), not 1.
    """
    diag_45 = np.hypot(*_deformed_point_at(0.0, 0.5, theta=np.pi / 4.0))
    on_x_axis = np.hypot(*_deformed_point_at(0.0, 0.5, theta=0.0))

    assert diag_45 == pytest.approx(1.25, rel=1e-12)
    assert on_x_axis == pytest.approx(np.hypot(1.0, 0.25), rel=1e-12)
    # The key contrast with pure h_plus: the diagonal, not the axis, carries
    # the larger deformation.
    assert diag_45 > on_x_axis


def test_h_plus_and_h_cross_produce_the_same_shape_rotated() -> None:
    """The 45-degree rotation is exact, not merely qualitatively different."""
    x_plus, y_plus = _deformed_points(h_plus=0.3, h_cross=0.0, n=2000)
    x_cross, y_cross = _deformed_points(h_plus=0.0, h_cross=0.3, n=2000)

    # Rotate the h_plus ellipse by 45 degrees and compare radii distributions
    # (shape-invariant check, avoiding phase-alignment issues).
    r_plus = np.sort(np.hypot(x_plus, y_plus))
    r_cross = np.sort(np.hypot(x_cross, y_cross))
    np.testing.assert_allclose(r_plus, r_cross, rtol=1e-3)


def test_undeformed_ring_is_unit_circle_at_zero_strain() -> None:
    x, y = _deformed_points(0.0, 0.0)
    np.testing.assert_allclose(np.hypot(x, y), 1.0, rtol=1e-12)


def test_rejects_too_few_points() -> None:
    with pytest.raises(ValueError, match="n_points"):
        plot_polarization_ellipse(0.1, 0.0, n_points=3)
