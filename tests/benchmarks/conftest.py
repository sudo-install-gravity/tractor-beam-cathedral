"""Shared fixtures for the analytic benchmark suite.

Comparison helpers live in ``helpers.py`` so tests can import them directly;
this module provides only fixtures.
"""

from __future__ import annotations

import pytest

from tests.benchmarks.helpers import ReferenceConstants


@pytest.fixture(scope="session")
def ref() -> ReferenceConstants:
    """Independently-sourced physical constants."""
    return ReferenceConstants()


@pytest.fixture(scope="session")
def target_range(ref: ReferenceConstants) -> float:
    """The project's nominal engagement range: 40 AU, in metres."""
    return 40.0 * ref.AU
