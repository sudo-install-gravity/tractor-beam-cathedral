"""Tests for tools/gates.py (T-13.8).

Never shells out to real ruff/mypy/pytest -- that would make this test
recursive (pytest testing itself) and slow. Instead `subprocess.run` is
monkeypatched to return canned results, so the tests exercise gates.py's
own reporting logic: what counts as a pass, what counts as a failure, and
that a failing gate never stops the remaining ones from running.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

# `tools` is on pythonpath via [tool.pytest.ini_options] in pyproject.toml.
from gates import run_gate, run_gates


def _completed(
    returncode: int, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["x"], returncode=returncode, stdout=stdout, stderr=stderr
    )


def test_run_gate_passes_on_zero_exit_with_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _completed(0, stdout="All checks passed!\n")
    )
    assert run_gate("ruff check", ["ruff", "check"], tmp_path) is True


def test_run_gate_fails_on_nonzero_exit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(1, stdout="1 error found\n"))
    assert run_gate("mypy", ["mypy", "src"], tmp_path) is False


def test_run_gate_fails_when_executable_cannot_be_launched(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The broken-console-shim incident (T-13.8's motivation): a gate that
    cannot even be launched must be reported as failed, not crash the script."""

    def _raise(*_a: Any, **_k: Any) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("no such file")

    monkeypatch.setattr(subprocess, "run", _raise)
    assert run_gate("mypy", ["mypy", "src"], tmp_path) is False


def test_run_gate_fails_on_zero_exit_with_no_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC: a gate that produces no output is reported as failed, not skipped --
    even if its exit code happened to be 0."""
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(0, stdout="", stderr=""))
    assert run_gate("mystery gate", ["true"], tmp_path) is False


def test_run_gate_fails_on_zero_exit_with_whitespace_only_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(0, stdout="   \n  \n"))
    assert run_gate("mystery gate", ["true"], tmp_path) is False


def test_run_gate_never_shells_out(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Never masks a gate's exit code behind a pipe: subprocess.run must be
    called with the argv list directly, with shell not enabled."""
    captured: dict[str, Any] = {}

    def _capture(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["argv"] = argv
        captured["shell"] = kwargs.get("shell", False)
        return _completed(0, stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", _capture)
    run_gate("pytest", ["pytest", "-q"], tmp_path)
    assert captured["argv"] == ["pytest", "-q"]
    assert not captured["shell"]


# --- run_gates: aggregation, exit codes, and "never stop early" ----------------


def test_run_gates_returns_zero_when_all_pass(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(0, stdout="ok\n"))
    gates = [("a", ["a"]), ("b", ["b"]), ("c", ["c"])]
    assert run_gates(gates, tmp_path) == 0


def test_run_gates_returns_one_when_any_gate_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def _fake(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return _completed(1 if argv == ["b"] else 0, stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", _fake)
    gates = [("a", ["a"]), ("b", ["b"]), ("c", ["c"])]
    assert run_gates(gates, tmp_path) == 1


def test_run_gates_runs_every_gate_even_after_an_earlier_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The T-13.8 AC's whole point: stopping early would itself be a
    'stopped checking' failure. All gates must run regardless of order."""
    called: list[str] = []

    def _fake(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        called.append(argv[0])
        return _completed(1 if argv == ["a"] else 0, stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", _fake)
    gates = [("a", ["a"]), ("b", ["b"]), ("c", ["c"])]
    run_gates(gates, tmp_path)
    assert called == ["a", "b", "c"]


def test_run_gates_names_the_failed_gates_in_the_summary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def _fake(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return _completed(1 if argv[0] in ("b", "c") else 0, stdout="ok\n")

    monkeypatch.setattr(subprocess, "run", _fake)
    gates = [("alpha", ["a"]), ("beta", ["b"]), ("gamma", ["c"])]
    run_gates(gates, tmp_path)
    out = capsys.readouterr().out
    assert "beta" in out
    assert "gamma" in out
    assert "2 of 3 gate(s) failed" in out
