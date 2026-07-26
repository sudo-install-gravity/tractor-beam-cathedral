#!/usr/bin/env python3
"""Batch backlog tasks into execution sessions, minimising model switches.

Every task in ``docs/BACKLOG.md`` carries an agent tier (``opus``, ``sonnet``,
``sonnet-low``). Naively walking the dependency graph in topological order would
switch models on almost every task. Switching to Opus costs a session boundary —
context has to be re-established — and that cost is paid *per switch*, not per
task, so 16 heavy tasks scattered through the graph would cost 16 boundaries.

This planner alternates two kinds of session:

* **OPUS** — every heavy task reachable in one batch, including chains of heavy
  tasks that depend on each other (they can run back-to-back inside one session).
* **SONNET** — everything else reachable, with per-task reasoning effort noted.
  ``sonnet`` and ``sonnet-low`` share a session because they are the same model
  at different effort, which is a cheap switch.

The look-ahead: before opening an OPUS session, the planner checks whether
running the available light work *first* would let more heavy tasks join the
batch. If so it defers. That is the difference between opening Opus for one task
and opening it for five.

Usage::

    python tools/schedule.py --plan              # full session plan
    python tools/schedule.py --next              # just the next session
    python tools/schedule.py --status            # tier and completion summary
    python tools/schedule.py --plan --done T-1.1,T-1.2
    python tools/schedule.py --plan --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

BACKLOG = Path(__file__).resolve().parent.parent / "docs" / "BACKLOG.md"

HEAVY = "opus"

# Detailed spec header:
#   **T-1.0 · Title · 2 pts · `sonnet` · deps T-0.7**
SPEC_RE = re.compile(
    r"\*\*(?P<id>T-\d+\.\d+|SPIKE-[\d.]+) · (?P<title>.+?) · (?P<pts>\d+) pts · "
    r"`(?P<tier>[a-z-]+)` · deps (?P<deps>[^*]*?)\*\*"
)
# Sprint 0 table row:
#   | T-0.1 | Title | 3 | `sonnet-low` | — | ✅ |
ROW_RE = re.compile(
    r"^\| (?P<id>T-\d+\.\d+) \| (?P<title>.+?) \| (?P<pts>\d+) \| "
    r"`(?P<tier>[a-z-]+)` \| (?P<deps>.+?) \| (?P<status>.+?) \|$",
    re.M,
)
SPRINT_RE = re.compile(r"^## Sprint (\d+)", re.M)
TASK_ID_RE = re.compile(r"(?:T-\d+\.\d+|SPIKE-[\d.]+)")


@dataclass
class Task:
    id: str
    title: str
    points: int
    tier: str
    deps: list[str]
    sprint: int
    done: bool = False
    external_block: str = ""
    unlocks: list[str] = field(default_factory=list)

    @property
    def heavy(self) -> bool:
        return self.tier == HEAVY


RANGE_RE = re.compile(r"(T-(\d+)\.(\d+))\s*[–—-]\s*(T-(\d+)\.(\d+))")


def _parse_deps(raw: str, known: set[str], sprint: int) -> tuple[list[str], str]:
    """Split a deps string into task IDs and any non-task (external) blocker.

    Handles three notations the backlog actually uses:

    * plain lists      ``T-1.3, T-1.0``
    * inclusive ranges ``T-3.2–T-3.5``  (en dash, em dash, or hyphen)
    * the literal      ``all``          — every task in an earlier sprint

    T-2.9's dependency is literally "repo made public", which is not a task.
    Those become external blockers: the task is excluded from scheduling until a
    human clears it, rather than silently treated as ready.
    """
    raw = raw.strip()
    if raw in {"—", "-", "", "none"}:
        return [], ""

    if raw.lower() == "all":
        return sorted(t for t in known if _sprint_of(t) < sprint), ""

    ids: list[str] = []
    rest = raw
    for m in RANGE_RE.finditer(raw):
        lo_major, lo_minor = int(m.group(2)), int(m.group(3))
        hi_major, hi_minor = int(m.group(5)), int(m.group(6))
        if lo_major == hi_major:
            ids += [
                f"T-{lo_major}.{n}"
                for n in range(lo_minor, hi_minor + 1)
                if f"T-{lo_major}.{n}" in known
            ]
        rest = rest.replace(m.group(0), " ")

    ids += TASK_ID_RE.findall(rest)
    leftover = TASK_ID_RE.sub("", rest).replace(",", " ")
    leftover = re.sub(r"[–—-]", " ", leftover).strip()
    external = leftover if leftover and leftover.lower() not in {"deps", "and"} else ""
    return sorted(set(ids)), external


def _sprint_of(task_id: str) -> int:
    m = re.match(r"T-(\d+)\.", task_id)
    return int(m.group(1)) if m else 99


def load_tasks(path: Path = BACKLOG) -> dict[str, Task]:
    text = path.read_text(encoding="utf-8")

    # Map character offset -> sprint number so each task knows its sprint.
    bounds = [(m.start(), int(m.group(1))) for m in SPRINT_RE.finditer(text)]

    def sprint_at(pos: int) -> int:
        n = 0
        for start, num in bounds:
            if start <= pos:
                n = num
            else:
                break
        return n

    raw: list[tuple[str, str, int, str, str, int, bool]] = []
    for m in SPEC_RE.finditer(text):
        raw.append(
            (
                m.group("id"),
                m.group("title"),
                int(m.group("pts")),
                m.group("tier"),
                m.group("deps"),
                sprint_at(m.start()),
                False,
            )
        )
    for m in ROW_RE.finditer(text):
        raw.append(
            (
                m.group("id"),
                m.group("title"),
                int(m.group("pts")),
                m.group("tier"),
                m.group("deps"),
                sprint_at(m.start()),
                "✅" in m.group("status"),
            )
        )

    known = {r[0] for r in raw}
    tasks: dict[str, Task] = {}
    for tid, title, pts, tier, deps_raw, sprint, done in raw:
        if tid in tasks:  # table row and spec for the same id — keep the first
            continue
        deps, external = _parse_deps(deps_raw, known, sprint)
        tasks[tid] = Task(
            id=tid,
            title=title.strip(),
            points=pts,
            tier=tier,
            deps=[d for d in deps if d != tid],
            sprint=sprint,
            done=done,
            external_block=external,
        )

    # A task the parser cannot read must never be silently dropped — that loses
    # work with no signal. T-2.9 was written "1 pt" rather than "1 pts" and
    # vanished from the schedule entirely until this check was added.
    declared = set(re.findall(r"\*\*((?:T-\d+\.\d+|SPIKE-[\d.]+)) · ", text))
    declared |= {m.group("id") for m in ROW_RE.finditer(text)}
    unparsed = sorted(declared - set(tasks))
    if unparsed:
        raise ValueError(
            f"{len(unparsed)} task(s) present in the backlog but unparseable: "
            f"{unparsed}\nExpected header form:\n"
            "  **T-1.1 · Title · 2 pts · `sonnet-low` · deps T-0.1**\n"
            "Check for 'pt' instead of 'pts', or a missing `tier` field."
        )

    # Drop dangling dependencies rather than deadlocking on a typo, but say so.
    for t in tasks.values():
        missing = [d for d in t.deps if d not in tasks]
        if missing:
            print(f"warning: {t.id} depends on unknown {missing}", file=sys.stderr)
            t.deps = [d for d in t.deps if d in tasks]

    for t in tasks.values():
        for d in t.deps:
            tasks[d].unlocks.append(t.id)

    return tasks


def _closure(candidates: list[Task], done: set[str]) -> list[Task]:
    """Tasks runnable in one session, allowing intra-session dependencies.

    A batch may include B depending on A when A is also in the batch — inside a
    single session they simply run in order. This is what lets one Opus session
    take a whole chain (SPIKE-4.4 -> T-6.5 -> T-6.6) instead of three.
    """
    batch: dict[str, Task] = {}
    changed = True
    while changed:
        changed = False
        for t in candidates:
            if t.id in batch or t.id in done or t.done or t.external_block:
                continue
            if all(d in done or d in batch for d in t.deps):
                batch[t.id] = t
                changed = True
    return _topo(list(batch.values()), done)


def _topo(batch: list[Task], done: set[str]) -> list[Task]:
    """Order a batch so intra-batch dependencies come first."""
    ids = {t.id for t in batch}
    out: list[Task] = []
    placed: set[str] = set()
    pool = list(batch)
    while pool:
        progressed = False
        for t in list(pool):
            if all(d in done or d in placed or d not in ids for d in t.deps):
                out.append(t)
                placed.add(t.id)
                pool.remove(t)
                progressed = True
        if not progressed:  # cycle — emit remainder in stable order
            out.extend(sorted(pool, key=lambda x: x.id))
            break
    return out


@dataclass
class Session:
    index: int
    model: str
    tasks: list[Task]
    deferred_for_batching: bool = False

    @property
    def points(self) -> int:
        return sum(t.points for t in self.tasks)

    @property
    def unlocks(self) -> set[str]:
        ids = {t.id for t in self.tasks}
        return {u for t in self.tasks for u in t.unlocks} - ids


def plan(tasks: dict[str, Task], extra_done: set[str] | None = None) -> list[Session]:
    done = {t.id for t in tasks.values() if t.done} | (extra_done or set())
    heavy = [t for t in tasks.values() if t.heavy]
    light = [t for t in tasks.values() if not t.heavy]

    sessions: list[Session] = []
    guard = 0
    while True:
        guard += 1
        if guard > 200:  # pragma: no cover - structural safety net
            raise RuntimeError("scheduler failed to converge")

        remaining = [t for t in tasks.values() if t.id not in done and not t.external_block]
        if not remaining:
            break

        heavy_now = _closure(heavy, done)
        light_now = _closure(light, done)

        if not heavy_now and not light_now:
            break  # everything left is externally blocked or cyclic

        deferred = False
        if heavy_now and light_now:
            # LOOK-AHEAD: would running the light work first grow the Opus batch?
            after = _closure(heavy, done | {t.id for t in light_now})
            if len(after) > len(heavy_now):
                deferred = True

        if heavy_now and not deferred:
            sessions.append(Session(len(sessions) + 1, "opus", heavy_now))
            done |= {t.id for t in heavy_now}
        else:
            sessions.append(
                Session(len(sessions) + 1, "sonnet", light_now, deferred_for_batching=deferred)
            )
            done |= {t.id for t in light_now}

    return sessions


def _effort(t: Task) -> str:
    return {"sonnet-low": "low", "sonnet": "standard", "opus": "high"}.get(t.tier, "low")


def render(
    sessions: list[Session],
    tasks: dict[str, Task],
    only_next: bool = False,
    extra_done: set[str] | None = None,
) -> str:
    """Format a session plan.

    ``extra_done`` must carry whatever was passed to :func:`plan` — otherwise
    tasks completed via ``--done`` are neither scheduled nor recognised as
    finished, and get misreported as unreachable.
    """
    lines: list[str] = []
    shown = sessions[:1] if only_next else sessions

    for s in shown:
        sprints = sorted({t.sprint for t in s.tasks})
        span = (
            f"sprint {sprints[0]}" if len(sprints) == 1 else f"sprints {sprints[0]}–{sprints[-1]}"
        )
        lines.append("")
        lines.append(
            f"── Session {s.index} · {s.model.upper()} · "
            f"{len(s.tasks)} tasks · {s.points} pts · {span} " + ("─" * 8)
        )
        if s.deferred_for_batching:
            lines.append("   (light work run first — this grows the next Opus batch)")
        for t in s.tasks:
            blockers = [d for d in t.deps if d in {x.id for x in s.tasks}]
            after = f"  after {','.join(blockers)}" if blockers else ""
            lines.append(f"   {t.id:<10} [{_effort(t):<8}] {t.points}pt  {t.title[:52]}{after}")
        if s.unlocks:
            lines.append(f"   → unlocks {len(s.unlocks)} downstream task(s)")

    if not only_next:
        opus = [s for s in sessions if s.model == "opus"]
        light = [s for s in sessions if s.model != "opus"]
        heavy_tasks = sum(len(s.tasks) for s in opus)
        lines.append("")
        lines.append("─" * 62)
        lines.append(
            f"{len(sessions)} sessions: {len(opus)} Opus, {len(light)} Sonnet. "
            f"{sum(s.points for s in sessions)} pts total."
        )
        if opus:
            lines.append(
                f"Opus batching: {heavy_tasks} heavy tasks in {len(opus)} session(s) "
                f"(avg {heavy_tasks / len(opus):.1f} per session; "
                f"{heavy_tasks - len(opus)} switch(es) avoided)."
            )
        blocked = [t for t in tasks.values() if t.external_block and not t.done]
        for t in blocked:
            lines.append(f"BLOCKED  {t.id}  external: {t.external_block}")

        # Anything neither done, scheduled, nor directly blocked is blocked
        # *transitively*. Reporting it matters: a one-point governance chore can
        # gate the v1.0 release through a `deps all`, and that should be visible
        # rather than showing up as tasks quietly missing from the plan.
        scheduled = {t.id for s in sessions for t in s.tasks}
        done_ids = {t.id for t in tasks.values() if t.done} | (extra_done or set())
        direct = {t.id for t in blocked}
        stranded = sorted(set(tasks) - scheduled - done_ids - direct)
        if stranded:
            lines.append("")
            lines.append(f"UNREACHABLE ({len(stranded)}) — transitively blocked:")
            for tid in stranded:
                roots = _blocking_roots(tid, tasks, set(), done_ids)
                lines.append(f"  {tid:<10} waits on {', '.join(sorted(roots)) or '?'}")
    return "\n".join(lines)


def _blocking_roots(
    tid: str, tasks: dict[str, Task], seen: set[str], done: set[str] | None = None
) -> set[str]:
    """Trace a stranded task back to the externally-blocked tasks gating it."""
    done = done or set()
    if tid in seen or tid in done:
        return set()
    seen.add(tid)
    t = tasks.get(tid)
    if t is None or t.done:
        return set()
    if t.external_block:
        return {f"{tid} ({t.external_block})"}
    roots: set[str] = set()
    for d in t.deps:
        roots |= _blocking_roots(d, tasks, seen, done)
    return roots


def status(tasks: dict[str, Task]) -> str:
    done = sum(1 for t in tasks.values() if t.done)
    pts = sum(t.points for t in tasks.values())
    out = [
        f"{len(tasks)} tasks, {pts} points, {done} complete",
        "",
        "tier         tasks   pts",
    ]
    for tier in (HEAVY, "sonnet", "sonnet-low"):
        ts = [t for t in tasks.values() if t.tier == tier]
        out.append(f"{tier:<12} {len(ts):>5}   {sum(t.points for t in ts):>3}")
    out.append("")
    out.append("heaviest fan-out (tasks that unblock the most):")
    for t in sorted(tasks.values(), key=lambda x: -len(x.unlocks))[:5]:
        out.append(f"  {t.id:<10} unlocks {len(t.unlocks):>2}  {t.title[:44]}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plan", action="store_true", help="full session plan")
    ap.add_argument("--next", action="store_true", help="next session only")
    ap.add_argument("--status", action="store_true", help="tier and completion summary")
    ap.add_argument("--done", default="", help="comma-separated task IDs to mark complete")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    tasks = load_tasks()
    extra = {s.strip() for s in args.done.split(",") if s.strip()}

    if args.status:
        print(status(tasks))
        return 0

    sessions = plan(tasks, extra)

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "session": s.index,
                        "model": s.model,
                        "points": s.points,
                        "deferred_for_batching": s.deferred_for_batching,
                        "tasks": [
                            {
                                "id": t.id,
                                "title": t.title,
                                "points": t.points,
                                "tier": t.tier,
                                "effort": _effort(t),
                                "sprint": t.sprint,
                                "deps": t.deps,
                            }
                            for t in s.tasks
                        ],
                    }
                    for s in sessions
                ],
                indent=2,
            )
        )
        return 0

    if not sessions:
        print("nothing to schedule — all tasks complete or externally blocked")
        return 0

    print(render(sessions, tasks, only_next=args.next, extra_done=extra))
    return 0


if __name__ == "__main__":
    sys.exit(main())
