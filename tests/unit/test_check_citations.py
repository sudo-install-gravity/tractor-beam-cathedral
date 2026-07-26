"""Tests for the citation-discipline CI check.

The check is the mechanical enforcement of this project's central governance
rule, so it needs to be right about one thing in particular: a chapter
reference must not be accepted in place of an equation number.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# `tools` is on pythonpath via [tool.pytest.ini_options] in pyproject.toml.
from check_citations import check_source


def _write(tmp_path: Path, source: str) -> Path:
    path = tmp_path / "module.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_accepts_specific_equation_citation(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        '''
def strain_tt(q_ddot, r, n_hat):
    """Compute the transverse-traceless strain.

    Source: Maggiore Vol. 1, eq. 3.72
    """
    return q_ddot
''',
    )
    assert check_source(path) == []


def test_rejects_missing_citation(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        '''
def strain_tt(q_ddot, r, n_hat):
    """Compute the transverse-traceless strain."""
    return q_ddot
''',
    )
    violations = check_source(path)
    assert len(violations) == 1
    assert violations[0].name == "strain_tt"


def test_rejects_chapter_reference_without_equation_number(tmp_path: Path) -> None:
    """A chapter is not a citation.

    This is the case the check exists for: an auditor must be able to open one
    page and check one line, not read a chapter looking for the right formula.
    """
    path = _write(
        tmp_path,
        '''
def strain_tt(q_ddot, r, n_hat):
    """Compute the transverse-traceless strain.

    Source: MTW, ch. 36
    """
    return q_ddot
''',
    )
    assert len(check_source(path)) == 1


def test_rejects_missing_docstring(tmp_path: Path) -> None:
    path = _write(tmp_path, "def strain_tt(q_ddot, r, n_hat):\n    return q_ddot\n")
    violations = check_source(path)
    assert len(violations) == 1
    assert violations[0].reason == "no docstring"


def test_ignores_private_helpers(tmp_path: Path) -> None:
    path = _write(tmp_path, "def _scratch(x):\n    return x\n")
    assert check_source(path) == []


def test_checks_classes_and_methods(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        '''
class QuadrupoleSource:
    """A radiating quadrupole.

    Source: Maggiore Vol. 1, eq. 3.60
    """

    def luminosity(self):
        """Radiated power."""
        return 0.0
''',
    )
    violations = check_source(path)
    assert [v.name for v in violations] == ["luminosity"]


@pytest.mark.parametrize(
    "citation",
    [
        "Source: MTW, eq. 36.1",
        "Source: Maggiore Vol. 1, eq. 3.72",
        "Source: Poisson & Will, eq. 11.5",
        "source: balanis, eq. 6-10",
    ],
)
def test_accepts_citation_variants(tmp_path: Path, citation: str) -> None:
    path = _write(
        tmp_path,
        f'''
def f(x):
    """Does a thing.

    {citation}
    """
    return x
''',
    )
    assert check_source(path) == []
