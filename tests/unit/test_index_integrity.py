"""``docs/INDEX.md`` describes the codebase, so the description is asserted here.

INDEX.md's own maintenance rules say a registry row pointing at a function that no
longer exists "gets **flagged loudly**, not deleted", and that the registry must
never drift from the code. Both were policy enforced by nobody. On 2026-08-02 an
`indexer` pass found six live modules still marked "not yet implemented"; on
2026-08-03 a completeness sweep found eight public symbols absent from the module
map, including ``ledger.RunManifest`` — which the campaign runner uses and the
manuscript's Data-availability statement promises.

Every check here has one of two directions, and they fail for different reasons:

* **reference → code** (§1's ``Implemented in``/``Tested by``, §3's ``Asserted
  in``): does everything the documentation points at still exist? This direction
  was *already healthy* when the tests were written — deleting a function tends
  to break something visible, so the drift gets noticed.
* **code → reference** (§2 completeness): is everything that exists documented?
  This direction is where all eight defects were, and the reason is structural:
  **adding** a public symbol breaks nothing and announces nothing.

The second direction is therefore the one that earns its keep. It is the same
"make absence loud" rule as CLAUDE.md rule 8, applied to the index itself.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "gwtb"
INDEX = ROOT / "docs" / "INDEX.md"

#: `path.py:Symbol` or `path.py:Class.method`
_CODE_REF = re.compile(r"`([a-z_]+/[a-z_0-9]+\.py):([A-Za-z_][\w.]*)`")
#: `tests/unit/test_x.py::test_name`
_TEST_REF = re.compile(r"`(tests/[\w/]+\.py)::([A-Za-z_]\w*)`")
#: a bare `path.py` mention
_MODULE_REF = re.compile(r"`([a-z_]+/[a-z_0-9]+\.py)`")
#: a link to an architecture decision record
_ADR_LINK = re.compile(r"\((adr/\d{4}-[a-z0-9-]+\.md)\)")

#: Symbols a module defines but which the map need not name individually. Keep
#: this empty if at all possible: every entry is a hole in the completeness check.
_EXEMPT: dict[str, set[str]] = {}


def _index() -> str:
    return INDEX.read_text(encoding="utf-8")


def _section(number: int) -> str:
    text = _index()
    start = text.index(f"## {number}.")
    try:
        return text[start : text.index(f"## {number + 1}.")]
    except ValueError:
        return text[start:]


def _module_files() -> set[str]:
    return {
        str(p.relative_to(SRC)).replace("\\", "/")
        for p in SRC.rglob("*.py")
        if p.name != "__init__.py"
    }


def _module_map_rows() -> dict[str, str]:
    """Module path -> its whole row in the §2 table."""
    rows: dict[str, str] = {}
    for line in _section(2).split("\n"):
        match = re.match(r"\| `([a-z_]+/[a-z_0-9]+\.py)`", line)
        if match:
            rows[match.group(1)] = line
    return rows


def _public_symbols(relpath: str) -> set[str]:
    """Top-level public functions, classes and CONSTANTS of a module."""
    tree = ast.parse((SRC / relpath).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            if not node.name.startswith("_"):
                names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    if not target.id.startswith("_"):
                        names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id.isupper() and not node.target.id.startswith("_"):
                names.add(node.target.id)
    return names


def _defined_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


# --- direction 1: does everything the documentation points at exist? ----------


def test_every_module_map_row_points_at_a_real_module() -> None:
    """A row naming a module that no longer exists is a vanished-code finding."""
    phantom = sorted(set(_module_map_rows()) - _module_files())
    assert not phantom, f"module map rows with no such file: {phantom}"


@pytest.mark.parametrize("section", [1, 2, 3])
def test_code_references_resolve(section: int) -> None:
    """`path.py:Symbol` references in §1, §2 and §3 must resolve.

    §1's maintenance rule demands exactly this: "a registry row pointing at a
    function that no longer exists gets flagged loudly".
    """
    unresolved: list[str] = []
    for relpath, symbol in _CODE_REF.findall(_section(section)):
        path = SRC / relpath
        if not path.exists():
            unresolved.append(f"{relpath} (no such file)")
            continue
        names = _defined_names(path)
        # `Class.method` resolves if either the class or the method is defined.
        parts = symbol.split(".")
        if not (parts[0] in names or parts[-1] in names):
            unresolved.append(f"{relpath}:{symbol}")
    assert not unresolved, f"§{section} references that do not resolve: {unresolved}"


@pytest.mark.parametrize("section", [1, 3, 4])
def test_test_references_resolve(section: int) -> None:
    """`tests/...::test_name` references must name a test that exists.

    The assumption ledger cites specific tests as the evidence for a breakdown
    regime. A citation pointing at a renamed test is evidence of nothing.
    """
    unresolved: list[str] = []
    for relpath, func in _TEST_REF.findall(_section(section)):
        path = ROOT / relpath
        if not path.exists():
            unresolved.append(f"{relpath} (no such file)")
        elif func not in _defined_names(path):
            unresolved.append(f"{relpath}::{func}")
    assert not unresolved, f"§{section} test references that do not resolve: {unresolved}"


def test_adr_links_resolve() -> None:
    """Every ADR linked from the index must exist.

    ADR-0006 once cited two prototype scripts that had never been committed; that
    class of dangling reference is what this guards.
    """
    missing = sorted(
        link for link in set(_ADR_LINK.findall(_index())) if not (ROOT / "docs" / link).exists()
    )
    assert not missing, f"linked ADRs that do not exist: {missing}"


def test_bare_module_mentions_resolve() -> None:
    """A bare `pkg/module.py` mention anywhere in the index must be a real file."""
    known = _module_files()
    missing = sorted(
        {
            ref
            for ref in _MODULE_REF.findall(_index())
            if ref not in known and not (ROOT / ref).exists()
        }
    )
    assert not missing, f"module paths mentioned in INDEX.md that do not exist: {missing}"


# --- direction 2: is everything that exists documented? ----------------------


def test_every_module_has_a_module_map_row() -> None:
    """A module with no row is invisible to anyone reading the index."""
    undocumented = sorted(_module_files() - set(_module_map_rows()))
    assert not undocumented, (
        f"modules with no §2 row: {undocumented}. Add a row rather than deleting this "
        "assertion -- an undocumented module is the failure this catches."
    )


@pytest.mark.parametrize("relpath", sorted(_module_files()))
def test_every_public_symbol_is_named_in_the_module_map(relpath: str) -> None:
    """**The check that earns its place.** Every public symbol must be documented.

    This is the direction that actually drifts. Deleting a function breaks
    something visible; *adding* one announces nothing, so the module map silently
    falls behind. Eight symbols were missing when this test was written,
    including `ledger.RunManifest` and `ledger.run_manifest` -- used by
    `tools/run_campaign.py` and promised by the manuscript's Data-availability
    statement -- and the `MATERIALS` table the R3 campaign sweeps over.

    Note this cannot be satisfied by a shorthand: `core/constants.py` used to
    write `G_OVER_C4/5` for two names, and both are now spelled out.
    """
    row = _module_map_rows().get(relpath)
    assert row is not None, f"{relpath} has no §2 row"
    exempt = _EXEMPT.get(relpath, set())
    absent = sorted(s for s in _public_symbols(relpath) - exempt if f"`{s}`" not in row)
    assert not absent, (
        f"{relpath} defines public symbols absent from its §2 row: {absent}. "
        "Document them; do not add them to _EXEMPT unless there is a stated reason."
    )
