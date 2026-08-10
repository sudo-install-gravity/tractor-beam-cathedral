# Getting started

From a fresh clone to your first accepted change. This document gets you to the point where
you can read [`PHYSICS.md`](PHYSICS.md) and [`CONTRIBUTING.md`](../CONTRIBUTING.md) with working
context; it does not restate either. `PHYSICS.md` is the argument this project makes;
`CONTRIBUTING.md` is the standard your change is held to. Read both before you write code.

**Primary host is Windows 11.** Commands below are Windows PowerShell / `cmd`-compatible paths.
If you're on Linux or macOS, the ideas carry over; use `python3` and `.venv/bin/python` instead
of the `.venv\Scripts\` paths.

---

## 1. Clone and build the environment

```
git clone https://github.com/sudo-install-gravity/tractor-beam-cathedral.git
cd tractor-beam-cathedral
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

`-e ".[dev]"` is an **editable** install: `import gwtb` resolves straight to `src/gwtb/`, so
changes take effect without reinstalling. `[dev]` pulls in `pytest`, `ruff`, `mypy` — everything
the gates below need.

⚠️ **Use the venv's own interpreter for everything** — `.venv\Scripts\python.exe`,
`.venv\Scripts\python.exe -m pytest`, `.venv\Scripts\ruff.exe`. The system Python has no numpy.

⚠️ **If the repo directory is ever renamed or moved after this install, redo it.** An editable
install pins the *absolute path* it was built from into a `.pth` file
(`.venv\Lib\site-packages\__editable__.gwtb*.pth`). If that path stops matching where the clone
actually lives, `import gwtb` fails with `ModuleNotFoundError: No module named 'gwtb'` even
though `pip show gwtb` reports it installed — pytest still works in that state (it injects
`src` onto `sys.path` itself, per `pyproject.toml`'s `pythonpath` setting), which is why the
break shows up specifically when running a script directly, e.g. `examples/deflection_scenario.py`,
and can look confusing the first time. Fix: rerun the `pip install -e ".[dev]"` line above from
the repo's current location.

---

## 2. Run the sanity check

```
.venv\Scripts\python.exe tools\gates.py
```

Runs everything CI runs — ruff check, ruff format check, mypy, citation discipline, the full
test suite — in one command, and reports a gate as failed if it produces no output at all
rather than silently passing it. Expect roughly two and a half minutes and output ending in
`All 5 gates passed.`

⚠️ **Never invoke `mypy.exe` or `pytest.exe` directly on Windows.** Both console-script shims in
`.venv\Scripts\` are broken on this host: they exit 1 with *zero output*, indistinguishable from
a hang unless you already know to expect it. `tools/gates.py` calls everything through
`sys.executable -m ...` instead, which is why it's the one command worth memorizing.

⚠️ **If any tool built into this repo prints garbled output, mojibake, or a `UnicodeEncodeError`
crash** on Windows (`tools/schedule.py` is the one most likely to hit this), the cause is the
console defaulting to the `cp1252` codepage against text containing `✅`/box-drawing characters.
Set `PYTHONIOENCODING=utf-8` in the shell first — the content was never wrong, the terminal just
couldn't print it.

---

## 3. Run the end-to-end scenario

```
.venv\Scripts\python.exe examples\deflection_scenario.py
```

This is the fastest way to see what the whole framework actually computes: a 1 km asteroid at
40 AU, an 8×8 phased array, a prime-frequency drive — geometry through spin-2 superposition,
field evaluation, coupling, deflection, and the feasibility ledger, composed once in order with
no step skipped. It takes a few seconds and writes three files to `examples\output\` (gitignored
— regenerate, don't commit):

- `beam_pattern.png`, `field_slice.png` — what the array's radiated field looks like
- `gap_report.md` — the number that matters

The gap report is a small table, and it's the project's whole point stated quantitatively:

| Metric | Achieved | Required | Gap (decades) |
|---|---|---|---|
| aperture | ~41 (`D/λ`) | ~6×10⁹ | ~8 |
| impulse | ~1×10⁻²⁴ N·s | ~1.4×10¹⁰ N·s | ~34 |

Read "gap (decades)" as powers of ten short of an actual deflection, for *this* configuration.
The point of the tool is not to close that gap — it's to state it honestly, for any
configuration you feed it, rather than let a plausible-looking number substitute for one. If a
change you make causes a gap to shrink, that's worth checking twice before celebrating: per
[`CLAUDE.md`](../CLAUDE.md) rule 5, a wall that disappears is far more likely to mean the change
broke something than that it found a breakthrough.

This script is a **demonstration**, not a measurement — it carries no pre-registered falsifier
and asserts nothing. For the version of this that *does* verify a falsifier and produces the
numbers in the paper draft, see `tools/run_campaign.py` (campaigns R2–R8,
`docs/paper/campaign/`).

---

## 4. Orient yourself before changing anything

Five documents, in the order a newcomer needs them:

| Document | What it's for |
|---|---|
| [`HANDOVER.md`](HANDOVER.md) | Where the project stands *right now* — read this first if picking up cold |
| [`PHYSICS.md`](PHYSICS.md) | The argument: why each equation is the correct tool, derived from first principles, every claim traced to a checkable source |
| [`CLAIMS.md`](CLAIMS.md) | The registry: what's established physics (A), our derived extension (B), or open conjecture (C) — and why the boundary matters here specifically |
| [`INDEX.md`](INDEX.md) | The map: every equation, which function implements it, which test validates it |
| [`BACKLOG.md`](BACKLOG.md) | What's left, tiered by how much judgment each task needs |

`CONTRIBUTING.md` covers the workflow and standard every change is held to — citation discipline,
the RESEARCH → IMPLEMENT → REVIEW → INDEX loop, the physics review checklist (spin-2 vs. spin-1,
conservation stamps, FP64, analytic derivatives, never deleting a wall), and the Definition of
Ready/Done. Read it before touching `src/`.

**Ask the scheduler what to work on, rather than reading the backlog top to bottom:**

```
.venv\Scripts\python.exe tools\schedule.py --next
```

It reads completion from the ✅ markers on task headers in `BACKLOG.md`, so it always reflects
reality — you never pass it a flag saying what's done. It also groups the batch by which model
tier each task needs (`sonnet-low` / `sonnet` / `opus`) and reports anything transitively
blocked. `--plan` shows the full run order; `--chunk N` takes a dependency-valid prefix of the
next batch, for splitting large batches deterministically instead of by judgment call.

---

## 5. Make a change

The one rule that matters most, from `CONTRIBUTING.md`: **no physics formula is ever implemented
from memory.** Before writing physics code, confirm the governing equation, its primary source,
and its exact equation number — "Blanchet ch. 3" is not a citation, "Blanchet eq. 3" is. CI
enforces the *presence* of a citation mechanically (`tools/check_citations.py`); a reviewer
checks that it's *correct*.

A task is ready to start only when it has an exact file path, an exact function signature, the
formula and citation supplied up front, exact test assertions with tolerances, and zero open
design decisions. If a task says "decide", "choose", or "figure out", it needs a spike first —
spikes produce an architecture decision record in `docs/adr/`, never production code.

Before opening a PR, run the sanity check from step 2 again and mark your task's header ✅ in
`BACKLOG.md` — the scheduler trusts nothing else.

`main` is branch-protected; every change ships as a PR:

```
git checkout -b <short-descriptive-branch-name>
...edit, commit...
git push origin <branch-name>
gh pr create --base main --head <branch-name> --title "..." --body "..."
```

Wait for the three CI checks (Python 3.10/3.11/3.12) to go green before merging.

---

## 6. If something doesn't match what this document says

This project has been burned before by a document asserting something the code had already
outgrown — see `CLAIMS.md`'s change log for several examples, each found and corrected rather
than left. If a command here fails, or a number in `PHYSICS.md`/`CLAIMS.md` disagrees with what
`INDEX.md` or the code says, that's a real finding, not a sign you did something wrong. Report
it rather than working around it silently: a mismatch that fails quietly costs far more than
one that fails loudly, which is the whole reason this project keeps `docs/ERRATA.md` and records
demotions in `CLAIMS.md`'s change log instead of quietly fixing them.
