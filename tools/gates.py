#!/usr/bin/env python3
"""Run the five governance gates and report each one's status honestly.

    .venv\\Scripts\\python.exe tools\\gates.py

Every commit in this project's history is expected to pass five checks --
ruff's linter, ruff's formatter, mypy, the citation-discipline check, and
the test suite -- before it lands (mirroring ``.github/workflows/ci.yml``,
which runs the same five commands). This script exists because composing
those five commands by hand, twice, quietly stopped checking anything
(both incidents 2026-08-06, both caught by the same person who introduced
them):

1. ``.venv\\Scripts\\mypy.exe src`` exited 1 with **zero output** for an
   hour before anyone noticed -- a broken console-script shim produced a
   failure indistinguishable from silence (``docs/HANDOVER.md`` S8). The
   nonzero exit code was technically correct and effectively invisible,
   because nothing about running it made the failure loud.
2. The gates were chained as
   ``... && pytest -q 2>&1 | tail -1 && git commit``, which masked a real
   2-test failure: the pipe's exit code is ``tail``'s, always 0, so the
   chain proceeded and an unverified commit was pushed.

Both are the same defect class this project keeps finding: **a
verification that cannot fail loudly is not a verification.** This is the
single entry point that removes the chance to compose the five commands
wrongly again -- run this script, not the commands by hand.

Exit codes: 0 = all five gates passed, 1 = at least one gate failed. A
gate that could not even be launched (missing executable, etc.) or that
produced no output at all is reported as **FAILED**, never silently
skipped -- there is no third state.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Each gate: (display name, argv). Python tools are invoked via
#: ``sys.executable -m <tool>`` (never a ``<tool>.exe`` console-script
#: shim) so this always runs inside whichever interpreter is running this
#: script -- the same fix incident 1 above needed. Paths and order match
#: ``.github/workflows/ci.yml`` exactly, so this script is the local
#: equivalent of that pipeline, not an approximation of it.
GATES: list[tuple[str, list[str]]] = [
    ("ruff check", [sys.executable, "-m", "ruff", "check", "src", "tests", "tools"]),
    (
        "ruff format --check",
        [sys.executable, "-m", "ruff", "format", "--check", "src", "tests", "tools"],
    ),
    ("mypy", [sys.executable, "-m", "mypy", "src"]),
    ("citation discipline", [sys.executable, "tools/check_citations.py"]),
    ("pytest", [sys.executable, "-m", "pytest", "-q"]),
]


def run_gate(name: str, argv: list[str], cwd: Path) -> bool:
    """Run one gate, print its name/output/status, and return whether it passed.

    Never masks a gate's exit code: this invokes the subprocess directly
    (no shell, no pipe), so the returncode read here is the gate's own,
    not some downstream command's. Three ways a gate can fail: a nonzero
    return code; raising instead of returning (the executable could not
    be found or launched -- caught and reported, not left to crash this
    script); or returning 0 with **no output at all**, which is treated
    as failed rather than trusted, since a real gate always prints
    something and silence at that point is indistinguishable from the
    broken-shim incident this script exists to catch.

    Parameters
    ----------
    name
        Display name for this gate, e.g. ``"mypy"``.
    argv
        Full command, as a list -- never a shell string.
    cwd
        Working directory to run the command in.

    Returns
    -------
    bool
        Whether the gate passed.
    """
    print(f"\n=== {name} " + "=" * max(1, 68 - len(name)))
    try:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
    except OSError as exc:
        print(f"  COULD NOT RUN: {type(exc).__name__}: {exc}")
        print(f"  {name}: FAILED")
        return False

    output = (result.stdout or "") + (result.stderr or "")
    if output.strip():
        print(output.rstrip())
    else:
        print("  (no output)")

    passed = result.returncode == 0 and bool(output.strip())
    if result.returncode == 0 and not output.strip():
        print("  a gate that produces no output is reported as FAILED, not skipped")

    print(f"  {name}: {'PASSED' if passed else 'FAILED'}")
    return passed


def run_gates(gates: list[tuple[str, list[str]]], cwd: Path) -> int:
    """Run every gate in order, print a final summary, and return an exit code.

    Runs **all** gates regardless of earlier failures -- stopping early
    would itself be a "stopped checking" failure of exactly the kind this
    script exists to prevent: if gate 2 fails and the run stops there,
    nobody learns whether gates 3-5 would also have failed.

    Parameters
    ----------
    gates
        ``(name, argv)`` pairs, in the order to run them.
    cwd
        Working directory to run each command in.

    Returns
    -------
    int
        0 if every gate passed, 1 if any failed.
    """
    results = [(name, run_gate(name, argv, cwd)) for name, argv in gates]

    print("\n" + "=" * 72)
    for name, passed in results:
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")

    failed = [name for name, passed in results if not passed]
    if failed:
        print(f"\n{len(failed)} of {len(results)} gate(s) failed: {', '.join(failed)}")
        return 1

    print(f"\nAll {len(results)} gates passed.")
    return 0


def main() -> int:
    return run_gates(GATES, ROOT)


if __name__ == "__main__":
    sys.exit(main())
