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
from schedule import Session, Task, _parse_deps, load_tasks, plan

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


def test_external_blocker_is_recorded_not_treated_as_ready() -> None:
    """A non-task dependency becomes an external block, not a silent pass.

    Asserted against `_parse_deps` directly rather than against whichever task
    happens to be blocked today. This test previously read T-2.9's live
    `external_block == "repo made public"` and broke on 2026-08-06 when the repo
    was made public and the blocker was cleared -- nothing was wrong, the project
    had simply moved on. That is the SIXTH time a test in this file has expired
    by asserting live backlog state (see the note on
    `test_batching_beats_naive_switching`). Decoupled permanently: the notation
    is a property of the parser, and the parser is a pure function.
    """
    known = {"T-1.1", "T-1.2"}
    deps, block = _parse_deps("repo made public", known, sprint=2)
    assert deps == []
    assert block == "repo made public"

    # A real dependency list must NOT be mistaken for an external blocker.
    deps, block = _parse_deps("T-1.1, T-1.2", known, sprint=2)
    assert deps == ["T-1.1", "T-1.2"]
    assert block == ""


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


def test_blocked_tasks_are_excluded() -> None:
    """An externally-blocked task, and anything behind it, must not be scheduled.

    Synthetic rather than live: this asserted `"T-2.9" not in scheduled` until
    2026-08-06, when T-2.9's blocker was cleared and it became legitimately
    schedulable. The planner behaviour never changed.
    """
    blocked = Task(
        id="T-9.1",
        title="blocked",
        points=1,
        tier="sonnet-low",
        deps=[],
        sprint=9,
        external_block="a human must do something",
    )
    behind = _mk("T-9.2", "sonnet-low", ["T-9.1"])
    free = _mk("T-9.3", "sonnet-low", [])
    graph = {x.id: x for x in (blocked, behind, free)}

    scheduled = {x.id for s in plan(graph) for x in s.tasks}
    assert "T-9.1" not in scheduled, "an externally-blocked task was scheduled"
    assert "T-9.2" not in scheduled, "a task stranded behind a blocker was scheduled"
    assert "T-9.3" in scheduled, "an unrelated ready task was dropped"


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


def test_batching_beats_naive_switching() -> None:
    """Heavy tasks must be batched into one session, not run one-by-one.

    **Synthetic, and permanently so.** This assertion has now expired FOUR times
    against the live backlog, each time because the project moved on rather than
    because the planner broke:

    * unconditional `heavy_scheduled > len(opus_sessions)` -> failed `0 > 0` on
      2026-07-31 when the last opus task completed;
    * guarded for the zero-session case -> failed `1 > 1` on 2026-08-06 when the
      repo went public, unblocking exactly ONE opus task, which cannot be batched
      with anything because there is nothing else to batch it with.

    Batching is a property of the PLANNER, and a planner property is provable on
    a graph we construct. Three independent opus tasks must land in one session,
    not three. Sizing an assertion against however much work happens to remain is
    what kept breaking; this cannot expire.
    """
    graph = {
        x.id: x
        for x in [
            _mk("T-1.1", "opus", []),
            _mk("T-1.2", "opus", []),
            _mk("T-1.3", "opus", []),
        ]
    }
    sessions = plan(graph)
    opus_sessions = [s for s in sessions if s.model == "opus"]
    heavy_scheduled = sum(len(s.tasks) for s in opus_sessions)

    assert heavy_scheduled == 3, "the planner dropped heavy work"
    assert len(opus_sessions) == 1, (
        f"three independent opus tasks were split across {len(opus_sessions)} "
        "sessions; each split is a model switch the batching exists to avoid"
    )


def test_live_backlog_schedules_every_reachable_heavy_task(tasks: dict[str, Task]) -> None:
    """The live-backlog half of the above: nothing reachable may be dropped.

    This is the part that must stay coupled to the real backlog, because the
    failure it guards -- the planner silently omitting reachable work -- can only
    happen there (CLAUDE.md rule 8). It is written as a SET comparison rather
    than a count, so it stays true no matter how much work is left, including
    none.

    "Reachable" means every dependency is complete. Checking a task's own
    external block is not enough: a task with `deps all` is transitively stranded
    behind any blocker while carrying none itself.
    """
    done_ids = {t.id for t in tasks.values() if t.done}
    reachable_heavy = {
        t.id
        for t in tasks.values()
        if t.tier == "opus"
        and not t.done
        and not t.external_block
        and all(d in done_ids for d in t.deps)
    }
    scheduled_heavy = {t.id for s in plan(tasks) if s.model == "opus" for t in s.tasks}
    assert reachable_heavy <= scheduled_heavy, (
        f"planner dropped reachable heavy work: {sorted(reachable_heavy - scheduled_heavy)}"
    )


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


# --------------------------------------------------------------------------
# Completion markers in the backlog
# --------------------------------------------------------------------------


def test_checkmark_marks_a_task_complete(tmp_path) -> None:
    """A trailing ✅ on a spec header means done."""
    b = tmp_path / "BACKLOG.md"
    b.write_text(
        "## Sprint 1 — x\n\n"
        "**T-1.1 · Finished · 2 pts · `sonnet-low` · deps —** ✅\n\n"
        "**T-1.2 · Not finished · 2 pts · `sonnet-low` · deps T-1.1**\n\n"
        "**T-1.3 · Finished with trailing note · 1 pts · `opus` · deps —** ✅ ⚠️ **note**\n",
        encoding="utf-8",
    )
    tasks = load_tasks(b)
    assert tasks["T-1.1"].done is True
    assert tasks["T-1.2"].done is False
    assert tasks["T-1.3"].done is True, "a ✅ followed by other markers must still count"


def test_completed_tasks_are_not_scheduled(tmp_path) -> None:
    b = tmp_path / "BACKLOG.md"
    b.write_text(
        "## Sprint 1 — x\n\n"
        "**T-1.1 · Done · 2 pts · `sonnet-low` · deps —** ✅\n\n"
        "**T-1.2 · Todo · 2 pts · `sonnet-low` · deps T-1.1**\n",
        encoding="utf-8",
    )
    scheduled = {t.id for s in plan(load_tasks(b)) for t in s.tasks}
    assert scheduled == {"T-1.2"}


def test_backlog_markers_agree_with_done_flag(tasks: dict[str, Task]) -> None:
    """The ✅ markers must produce the same plan as passing --done explicitly.

    The backlog is now the single record of progress. This asserts the CLI flag
    and the file cannot drift into disagreeing about what is finished.
    """
    marked = {t.id for t in tasks.values() if t.done}
    assert len(marked) >= 30, "expected Sprint 0 plus Sprint 1 core to be marked"

    from_markers = [{t.id for t in s.tasks} for s in plan(tasks)]
    # Re-plan pretending nothing is marked, supplying the same set via --done.
    for t in tasks.values():
        t.done = False
    from_flag = [{t.id for t in s.tasks} for s in plan(tasks, marked)]
    for t in tasks.values():  # restore
        t.done = t.id in marked

    assert from_markers == from_flag


# --------------------------------------------------------------------------
# Deterministic chunking
# --------------------------------------------------------------------------


def test_chunk_prefix_is_always_dependency_valid(tasks: dict[str, Task]) -> None:
    """The load-bearing property: any prefix of a batch is runnable as-is.

    ``_topo`` orders each batch so a task appears only after everything it
    depends on *within that batch*. Truncating therefore cannot orphan a
    dependency — which is what makes ``--chunk`` safe to derive mechanically
    instead of split by judgment.
    """
    from schedule import take_chunk

    done = {t.id for t in tasks.values() if t.done}
    batch = _synthetic_batch()
    for size in range(1, len(batch.tasks) + 1):
        seen = set(done)
        for t in take_chunk(batch, size).tasks:
            unmet = [d for d in t.deps if d not in seen]
            assert not unmet, f"chunk size {size}: {t.id} orphaned from {unmet}"
            seen.add(t.id)


def _synthetic_batch() -> Session:
    """An 8-task synthetic sonnet batch, independent of the live backlog's
    current contents.

    Five tests below exercise ``take_chunk`` — a pure function of a
    ``Session`` — but originally read that session from ``plan(tasks)[0]``
    against the *real*, ever-changing backlog. That worked only as long as
    some batch was always non-empty; once the real backlog reached "nothing
    to schedule" (2026-08-02, the last task landed), ``plan(tasks)`` returned
    ``[]`` and ``[0]`` raised ``IndexError`` in all five — not a bug in
    ``take_chunk``, but a test-fixture coupling to live data the tests never
    actually needed. A synthetic batch removes that coupling permanently
    rather than resizing against whatever the backlog happens to contain
    today, which is the same class of fix as the ``min(5, len(batch.tasks))``
    and "size against the batch" repairs elsewhere in this file — but those
    still assumed *some* live batch existed. This one doesn't.
    """
    graph = {t.id: t for t in [_mk(f"T-x.{i}", "sonnet-low", []) for i in range(8)]}
    return plan(graph)[0]


def test_chunk_is_deterministic() -> None:
    """Same batch, same chunk — no judgment call to forget or disagree about."""
    from schedule import take_chunk

    batch = _synthetic_batch()
    a = [t.id for t in take_chunk(batch, 5).tasks]
    b = [t.id for t in take_chunk(batch, 5).tasks]
    assert a == b
    assert len(a) == 5


def test_chunk_larger_than_batch_returns_batch_unchanged() -> None:
    from schedule import take_chunk

    batch = _synthetic_batch()
    for size in (len(batch.tasks), len(batch.tasks) + 10, 0, -1):
        out = take_chunk(batch, size)
        assert [t.id for t in out.tasks] == [t.id for t in batch.tasks]
        assert out.chunk_note == "", "an untruncated batch must not claim to be a chunk"


def test_chunk_preserves_tier_purity() -> None:
    from schedule import take_chunk

    batch = _synthetic_batch()
    chunk = take_chunk(batch, 3)
    assert chunk.model == batch.model
    for t in chunk.tasks:
        assert (chunk.model == "opus") == (t.tier == "opus")


def test_chunk_announces_itself() -> None:
    """A truncated batch must say so, or the reader assumes it is the whole batch."""
    from schedule import take_chunk

    batch = _synthetic_batch()
    size = len(batch.tasks) - 1
    chunk = take_chunk(batch, size)
    assert chunk.chunk_note
    assert f"{size}/{len(batch.tasks)}" in chunk.chunk_note


def test_real_backlog_may_have_nothing_left_to_schedule(tasks: dict[str, Task]) -> None:
    """Guards the state ``_synthetic_batch`` was introduced to stop depending
    on: an empty plan is a legitimate, expected outcome once every reachable
    task is done, not a crash condition. ``plan(tasks)`` returning ``[]`` and
    ``schedule.py --next`` printing "nothing to schedule" are the correct
    behavior here, not a bug — this test exists so a future change that makes
    ``plan`` misbehave on an empty backlog (e.g. raising instead of returning
    ``[]``) fails loudly (CLAUDE.md rule 8) rather than only surfacing as
    confusing downstream failures in unrelated tests, the way it did here.
    """
    result = plan(tasks)
    assert isinstance(result, list)
