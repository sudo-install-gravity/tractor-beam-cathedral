"""The package dependency graph is a documented claim, so it is asserted here.

``docs/paper/nature-draft.md`` Methods prints a table of packages with a depth and
an ``imports`` column, and Fig. 1 draws the same graph. Both said "nine packages in
dependency order" until 2026-08-03, when extracting the graph showed three things
wrong with that: ``source`` and ``propagate`` import each other, ``ledger`` is
upstream of ``target`` rather than a final reporting stage, and ``viz`` imports
nothing at all.

That was a documentation defect with no runtime symptom, which is exactly the kind
this project keeps producing and exactly the kind a test can prevent recurring. So
the graph is extracted from the import statements here and pinned.

**The most valuable assertion in this file is the cycle one.** It does not merely
tolerate the known ``source`` <-> ``propagate`` cycle -- it asserts that cycle is
the *only* one. A contributor introducing a second would fail this test with a
message naming it, rather than silently deepening a tangle nobody re-measures.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "gwtb"

#: The one cycle that exists, and the reason it is tolerated: at *module*
#: granularity the graph is a clean DAG (asserted below), so this is a naming/
#: layering wart rather than a circular import. Do not add to this set without
#: recording why in the manuscript's Methods table -- the table and this set are
#: the same claim written twice.
KNOWN_CYCLES = {("propagate", "source")}

#: Package -> the packages it imports. Pinned against the Methods table.
EXPECTED_IMPORTS = {
    "core": set(),
    "viz": set(),
    "bodies": {"core"},
    "kinematics": {"core"},
    "source": {"bodies", "core", "kinematics", "propagate"},
    "propagate": {"core", "source"},
    "array": {"core", "kinematics", "propagate"},
    "ledger": {"core", "source"},
    "target": {"core", "ledger"},
}


def _packages() -> list[str]:
    return sorted(p.name for p in SRC.iterdir() if p.is_dir() and not p.name.startswith("__"))


def _package_graph() -> dict[str, set[str]]:
    """Package -> packages it imports, read from the AST rather than from docs."""
    pkgs = set(_packages())
    edges: dict[str, set[str]] = defaultdict(set)
    for path in SRC.rglob("*.py"):
        rel = path.relative_to(SRC).parts
        if len(rel) < 2:  # a module directly under gwtb/, not in a package
            continue
        pkg = rel[0]
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            module = node.module if isinstance(node, ast.ImportFrom) and node.module else None
            if module and module.startswith("gwtb."):
                dep = module.split(".")[1]
                if dep != pkg and dep in pkgs:
                    edges[pkg].add(dep)
    return {p: edges[p] for p in sorted(pkgs)}


def _module_graph() -> dict[str, set[str]]:
    """Module -> modules it imports, for the finer-grained acyclicity check."""
    edges: dict[str, set[str]] = defaultdict(set)
    for path in SRC.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        name = ".".join(path.relative_to(SRC).with_suffix("").parts)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            module = node.module if isinstance(node, ast.ImportFrom) and node.module else None
            if module and module.startswith("gwtb."):
                edges[name].add(module[len("gwtb.") :])
    return edges


def _cycles(edges: dict[str, set[str]]) -> set[tuple[str, ...]]:
    """Strongly-connected components of size > 1, as sorted tuples."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    found: set[tuple[str, ...]] = set()
    counter = [0]

    def strongconnect(v: str) -> None:
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on_stack.add(v)
        for w in edges.get(v, ()):
            if w not in index:
                strongconnect(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            component = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                component.append(w)
                if w == v:
                    break
            if len(component) > 1:
                found.add(tuple(sorted(component)))

    for node in list(edges):
        if node not in index:
            strongconnect(node)
    return found


def test_package_import_graph_matches_the_documented_table() -> None:
    """The Methods table's `imports` column, asserted rather than described."""
    assert _package_graph() == EXPECTED_IMPORTS


def test_the_source_propagate_cycle_is_the_only_one() -> None:
    """A NEW package cycle must fail here, naming itself.

    The existing one is tolerated and documented. The failure mode this guards is
    a second cycle appearing and nobody noticing, because nobody re-derives the
    graph by hand -- which is precisely how the original claim went stale.
    """
    cycles = _cycles(_package_graph())
    assert cycles == KNOWN_CYCLES, (
        f"package cycles changed: {sorted(cycles)}. If this is intentional, update "
        "KNOWN_CYCLES *and* the Methods table and Fig. 1 in docs/paper/nature-draft.md "
        "-- they are the same claim written three times."
    )


def test_module_graph_has_no_cycles_at_all() -> None:
    """The package cycle must stay a layering wart, not become a circular import.

    This is what makes the documented cycle tolerable. If it ever fails, the
    package-level finding has become a runtime one.
    """
    assert _cycles(_module_graph()) == set()


@pytest.mark.parametrize(
    ("package", "depth"),
    [
        ("core", 0),
        ("viz", 0),
        ("bodies", 1),
        ("kinematics", 1),
        ("source", 2),
        ("propagate", 2),
        ("array", 3),
        ("ledger", 3),
        ("target", 4),
    ],
)
def test_documented_depth_is_what_the_imports_imply(package: str, depth: int) -> None:
    """Depths in the Methods table, with the known cycle collapsed to one tier.

    `source` and `propagate` are mutually dependent, so neither is below the other;
    both are depth 2. Computing this with the cycle *not* collapsed would put them
    at different depths and quietly contradict the table.
    """
    edges = _package_graph()
    groups: dict[str, frozenset[str]] = {}
    for component in _cycles(edges) | {(p,) for p in edges}:
        for member in component:
            groups.setdefault(member, frozenset())
            if len(component) > len(groups[member]):
                groups[member] = frozenset(component)

    cache: dict[frozenset[str], int] = {}

    def depth_of(group: frozenset[str]) -> int:
        if group in cache:
            return cache[group]
        cache[group] = 0  # guard against re-entry
        outside = {groups[d] for m in group for d in edges[m] if groups[d] != group}
        cache[group] = 0 if not outside else 1 + max(depth_of(g) for g in outside)
        return cache[group]

    assert depth_of(groups[package]) == depth
