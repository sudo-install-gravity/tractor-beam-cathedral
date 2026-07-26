#!/usr/bin/env python3
"""Enforce citation discipline on physics modules.

Every public function and class in the physics packages must carry a docstring
line naming its primary source and the exact equation number, e.g.::

    Source: Maggiore Vol. 1, eq. 3.72

This is the mechanical half of the project's central governance rule (see
CLAUDE.md). It checks that a citation is *present* and *specific* — it cannot
check that the citation is *correct*. That is the `researcher` agent's job
before implementation and `code-reviewer`'s during review.

"MTW ch. 36" is rejected. "MTW eq. 36.1" is accepted. A contributor auditing
this code decades from now must be able to open one page and check one line.

Exit codes: 0 = all cited, 1 = violations found.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

# Packages whose public API implements physics and therefore requires citations.
# Modules outside these are exempt: core/ is infrastructure, viz/ is rendering,
# ledger/ and target/ consume cited results rather than introducing equations.
PHYSICS_PACKAGES = ("source", "propagate", "bodies", "array")

# Requires a source AND a specific equation reference. The `eq.` token is what
# distinguishes a real citation from a hand-wave at a chapter.
CITATION_RE = re.compile(
    r"Source:\s*.+?,\s*eq\.\s*\S+",
    re.IGNORECASE,
)

# Functions that are plumbing rather than physics.
EXEMPT_NAMES = frozenset({"__init__", "__repr__", "__str__", "__eq__", "__hash__"})


class Violation:
    """A public physics definition missing a usable citation."""

    def __init__(self, path: Path, lineno: int, name: str, reason: str) -> None:
        self.path = path
        self.lineno = lineno
        self.name = name
        self.reason = reason

    def __str__(self) -> str:
        return f"{self.path}:{self.lineno}: {self.name} — {self.reason}"


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def check_source(path: Path) -> list[Violation]:
    """Return citation violations in a single module."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:  # pragma: no cover - a syntax error fails CI elsewhere
        return [Violation(path, exc.lineno or 0, "<module>", f"syntax error: {exc.msg}")]

    violations: list[Violation] = []
    targets = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

    for node in ast.walk(tree):
        if not isinstance(node, targets):
            continue
        if node.name in EXEMPT_NAMES or not _is_public(node.name):
            continue

        doc = ast.get_docstring(node)
        if not doc:
            violations.append(Violation(path, node.lineno, node.name, "no docstring"))
        elif not CITATION_RE.search(doc):
            violations.append(
                Violation(
                    path,
                    node.lineno,
                    node.name,
                    "docstring lacks 'Source: <reference>, eq. <number>'",
                )
            )

    return violations


def collect_files(root: Path) -> list[Path]:
    """Every physics module under the packages that require citations."""
    files: list[Path] = []
    for package in PHYSICS_PACKAGES:
        pkg_dir = root / "src" / "gwtb" / package
        if not pkg_dir.is_dir():
            continue
        files.extend(p for p in sorted(pkg_dir.rglob("*.py")) if p.name != "__init__.py")
    return files


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    files = collect_files(root)

    violations: list[Violation] = []
    for path in files:
        violations.extend(check_source(path))

    if violations:
        print("Citation discipline violations:\n")
        for v in violations:
            print(f"  {v}")
        print(
            f"\n{len(violations)} violation(s) in {len(files)} file(s).\n"
            "\nEvery public definition in "
            f"{'/, '.join(PHYSICS_PACKAGES)}/ needs a docstring line of the form:\n"
            "    Source: Maggiore Vol. 1, eq. 3.72\n"
            "\nA chapter reference is not enough — cite the equation. If you do not\n"
            "have one, invoke the `researcher` agent before writing the code.\n"
        )
        return 1

    print(f"Citation discipline: OK ({len(files)} physics module(s) checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
