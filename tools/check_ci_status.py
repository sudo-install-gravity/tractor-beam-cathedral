#!/usr/bin/env python3
"""Check whether the newest GitHub Actions run on `main` is green for the
current commit.

    .venv\\Scripts\\python.exe tools\\check_ci_status.py

Deliberately **not** a pytest test and **not** a sixth local gate: it needs
network access and `gh` credentials, and a gate that cannot run offline would
break the local five (`tools/gates.py`). This is an on-demand check, run by
hand or in a follow-up step after pushing -- see `docs/HANDOVER.md` S8.

Why this exists: zero remote CI runs went unnoticed for 64 commits (2026-08-02
through 2026-08-09, ADR-0008) because nothing ever looked. Local tests passing
is not evidence the remote pipeline ran, let alone ran on the code currently
checked out -- the same "derive, don't assert" fix `test_architecture.py`
applies to the package graph, applied here to the CI pipeline itself.

Exit codes: 0 = the newest run on `main` is `success` and is for the current
HEAD. 1 = anything else, with a **named** reason printed -- CI has never run,
the newest run did not succeed, the newest run is still in progress, the
newest run predates the current HEAD, or `gh` itself could not be reached.
There is no "unknown, probably fine" outcome.
"""

from __future__ import annotations

import json
import subprocess
import sys

REPO = "sudo-install-gravity/tractor-beam-cathedral"


def _current_head() -> str:
    """The local repository's current commit SHA."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _latest_run_on_main() -> dict[str, object] | None:
    """The most recent `actions/runs` entry for `main`, or ``None`` if there
    has never been one.

    Raises ``RuntimeError`` (with a named reason) if `gh` cannot be reached at
    all -- a network/auth failure is not the same finding as "CI has never
    run" and must not be reported as one.
    """
    # Query params go directly in the URL: gh api's -f/-F flags submit as a
    # POST body unless the method is explicitly GET, which 404s against this
    # (GET-only) endpoint -- found while testing this script.
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{REPO}/actions/runs?branch=main&per_page=1"],
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise RuntimeError(f"could not run gh: {type(exc).__name__}: {exc}") from exc

    if result.returncode != 0:
        raise RuntimeError(f"gh api call failed: {result.stderr.strip() or '(no output)'}")

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"unexpected (non-JSON) response from GitHub API: {exc}") from exc

    runs = payload.get("workflow_runs", [])
    return runs[0] if runs else None


def main() -> int:
    try:
        head = _current_head()
    except subprocess.CalledProcessError as exc:
        print(f"FAILED: could not determine current HEAD: {exc}", file=sys.stderr)
        return 1

    try:
        run = _latest_run_on_main()
    except RuntimeError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    if run is None:
        print("FAILED: CI has never run -- actions/runs reports zero runs for main")
        return 1

    status = run.get("status")
    conclusion = run.get("conclusion")
    run_sha = run.get("head_sha")
    updated_at = run.get("updated_at")
    html_url = run.get("html_url")

    if status != "completed":
        print(
            f"FAILED: newest run on main is still in progress (status={status!r}); "
            f"commit {run_sha}, {html_url}"
        )
        return 1

    if conclusion != "success":
        print(
            f"FAILED: newest completed run on main did not succeed "
            f"(conclusion={conclusion!r}); commit {run_sha}, {html_url}"
        )
        return 1

    if run_sha != head:
        print(
            f"FAILED: newest successful run is for commit {run_sha}, not current HEAD "
            f"({head}) -- push to get a fresh run against this code; {html_url}"
        )
        return 1

    print(f"OK: newest run on main succeeded for current HEAD ({head}); completed {updated_at}")
    print(f"    {html_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
