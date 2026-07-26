"""Tests for the session scheduler.

The scheduler's job is to batch backlog tasks into as few model switches as the
dependency graph allows. Two properties matter most and are asserted hardest:

* it must never schedule a task before its dependencies, and
* it must never silently drop a task.

The second is the one that actually bit us: T-2.9 was written "1 pt" instead of
"1 pts", failed to parse, and disappeared from the plan with no signal.
"""

from __future__ import annotations

import pytest

# `tools` is on pythonpath via [tool.pytest.ini_options] in pyproject.toml.
from schedule import Task, load_tasks, plan

# --------------------------------------------------------------------------
# Parsing the real backlog
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tasks() -> dict[str, Task]:
    return load_tasks()


def test_backlog_parses(tasks: dict[str, Task]) -> None:
    assert len(tasks) > 100
    assert {"T-1.1", "T-6.5", "SPIKE-4.4", "T-2.9"} <= set(tasks)


def test_every_task_has_a_known_tier(tasks: dict[str, Task]) -> None:
    assert {t.tier for t in tasks.values()} <= {"opus", "sonnet", "sonnet-low"}


def test_unparseable_task_raises_rather_than_vanishing(tmp_path) -> None:
    """A task the parser cannot read must fail loudly.

    This is the T-2.9 regression: "1 pt" instead of "1 pts" made the header
    unmatchable, and the task silently left the schedule.
    """
    bad = tmp_path / "BACKLOG.md"
    bad.write_text(
        "## Sprint 1 — x\n\n"
        "**T-1.1 · Good · 2 pts · `sonnet-low` · deps —**\n\n"
        "**T-1.2 · Bad singular unit · 1 pt · `sonnet-low` · deps T-1.1**\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unparseable"):
        load_tasks(bad)


def test_range_dependencies_expand(tasks: dict[str, Task]) -> None:
    """`deps T-3.2–T-3.5` must expand to the four tasks, not one."""
    assert set(tasks["T-3.6"].deps) == {"T-3.2", "T-3.3", "T-3.4", "T-3.5"}


def test_deps_all_expands_to_earlier_sprints(tasks: dict[str, Task]) -> None:
    deps = tasks["T-12.4"].deps
    assert len(deps) > 50
    assert all(int(d.split("-")[1].split(".")[0]) < 12 for d in deps)


def test_external_blocker_is_recorded_not_treated_as_ready(tasks: dict[str, Task]) -> None:
    t = tasks["T-2.9"]
    assert t.external_block == "repo made public"
    assert t.deps == []


# --------------------------------------------------------------------------
# Plan correctness
# --------------------------------------------------------------------------


def test_plan_is_topologically_valid(tasks: dict[str, Task]) -> None:
    """No task may run before its dependencies — across or within sessions."""
    seen: set[str] = {t.id for t in tasks.values() if t.done}
    for session in plan(tasks):
        for t in session.tasks:
            unmet = [d for d in t.deps if d not in seen]
            assert not unmet, f"{t.id} scheduled before {unmet}"
            seen.add(t.id)


def test_sessions_are_tier_pure(tasks: dict[str, Task]) -> None:
    """An Opus session holds only heavy tasks, and vice versa."""
    for session in plan(tasks):
        for t in session.tasks:
            assert (session.model == "opus") == (t.tier == "opus")


def test_no_task_scheduled_twice(tasks: dict[str, Task]) -> None:
    ids = [t.id for s in plan(tasks) for t in s.tasks]
    assert len(ids) == len(set(ids))


def test_blocked_tasks_are_excluded(tasks: dict[str, Task]) -> None:
    scheduled = {t.id for s in plan(tasks) for t in s.tasks}
    assert "T-2.9" not in scheduled


def test_completed_tasks_are_not_rescheduled(tasks: dict[str, Task]) -> None:
    scheduled = {t.id for s in plan(tasks) for t in s.tasks}
    assert not scheduled & {t.id for t in tasks.values() if t.done}


def test_done_override_removes_tasks(tasks: dict[str, Task]) -> None:
    scheduled = {t.id for s in plan(tasks, {"T-1.1"}) for t in s.tasks}
    assert "T-1.1" not in scheduled


# --------------------------------------------------------------------------
# The look-ahead
# --------------------------------------------------------------------------


def _mk(tid: str, tier: str, deps: list[str]) -> Task:
    return Task(id=tid, title=tid, points=1, tier=tier, deps=deps, sprint=1)


def test_lookahead_defers_opus_to_grow_the_batch() -> None:
    """Running cheap work first should merge two Opus sessions into one.

    O1 is ready immediately; O2 needs light task L1. Scheduling greedily gives
    OPUS{O1}, SONNET{L1}, OPUS{O2} — two Opus boundaries. Deferring O1 by one
    session gives SONNET{L1}, OPUS{O1,O2} — one boundary, same work.
    """
    graph = {
        t.id: t
        for t in [
            _mk("T-1.1", "opus", []),
            _mk("T-1.2", "sonnet-low", []),
            _mk("T-1.3", "opus", ["T-1.2"]),
        ]
    }
    sessions = plan(graph)
    opus = [s for s in sessions if s.model == "opus"]
    assert len(opus) == 1, "look-ahead failed to merge the Opus sessions"
    assert {t.id for t in opus[0].tasks} == {"T-1.1", "T-1.3"}
    assert sessions[0].model == "sonnet"
    assert sessions[0].deferred_for_batching


def test_lookahead_does_not_stall_when_nothing_would_be_gained() -> None:
    """With no light work able to unblock more heavy work, run Opus now."""
    graph = {
        t.id: t
        for t in [
            _mk("T-1.1", "opus", []),
            _mk("T-1.2", "sonnet-low", ["T-1.1"]),
        ]
    }
    sessions = plan(graph)
    assert sessions[0].model == "opus"


def test_opus_chain_runs_in_one_session() -> None:
    """Heavy tasks depending on each other share a session, running in order."""
    graph = {
        t.id: t
        for t in [
            _mk("T-1.1", "opus", []),
            _mk("T-1.2", "opus", ["T-1.1"]),
            _mk("T-1.3", "opus", ["T-1.2"]),
        ]
    }
    sessions = plan(graph)
    assert len(sessions) == 1
    assert [t.id for t in sessions[0].tasks] == ["T-1.1", "T-1.2", "T-1.3"]


def test_batching_beats_naive_switching(tasks: dict[str, Task]) -> None:
    """On the real backlog, heavy tasks must be batched, not run one-by-one."""
    sessions = plan(tasks)
    opus_sessions = [s for s in sessions if s.model == "opus"]
    heavy_scheduled = sum(len(s.tasks) for s in opus_sessions)
    assert heavy_scheduled > len(opus_sessions), "no batching happened at all"
    assert len(opus_sessions) <= 4, "too many Opus boundaries"


def test_render_recognises_cli_completed_tasks(tasks: dict[str, Task]) -> None:
    """Tasks completed via ``--done`` must not be reported as unreachable.

    Regression: ``render`` computed completion from the parsed ``done`` flag
    alone, so anything passed through ``--done`` was neither scheduled nor
    recognised as finished, and landed in the "UNREACHABLE" list with an
    unresolvable blocking root. Same silent-misreporting class as the T-2.9
    parse bug.
    """
    from schedule import render

    done = {f"T-1.{n}" for n in range(11)}
    out = render(plan(tasks, done), tasks, extra_done=done)

    for tid in sorted(done):
        assert f"  {tid:<10} waits on" not in out, f"{tid} misreported as unreachable"
    assert "waits on ?" not in out, "a stranded task has an unresolvable blocking root"
    # The genuine external block must still be reported.
    assert "T-2.9" in out
