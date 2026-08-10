# HANDOFF — Opus session: T-12.5 (Complete PHYSICS.md)

**Written 2026-08-10, supersedes the previous (now fully consumed) Sonnet-batch handoff.**
**Assume zero conversational context.** Everything needed is in the files named here.

## State of the world

The entire backlog is done except three tasks: T-12.5 (this handoff), T-12.7, T-12.8. CI
has been green and enforced since 2026-08-10 (SPIKE-13.1/ADR-0008), and **`main` is
branch-protected — direct pushes no longer work.** See "The PR workflow" below before
touching git at all; skipping it will produce a rejected push, not a landed commit.

## Recommendation: switch this session's model to Opus, in place

T-12.5 is `opus` tier — the only heavy task left in the project — because it requires
deriving physics content (claims B-3/B-4/B-5 have no existing derivation to check
against) and judging citation adequacy, not just executing a fully-specified recipe.
**Switch in place; do not start a new session.** Context here is free; re-deriving it
cold costs real tokens for no benefit (measured elsewhere in this project's own
history: ~190k tokens lost to a cold subagent dispatch that never even started writing
files). After T-12.5 closes, switch back down to Sonnet for T-12.7/T-12.8 — do that
switch explicitly too, and update this file when you do, per the project's own tier-switch
rule (`CLAUDE.md` "Which model runs a task").

## The task

**T-12.5 · Complete PHYSICS.md · 3 pts · `opus` · deps all (satisfied)**
`docs/PHYSICS.md` — replace every `[UNVERIFIED]` marker with a confirmed citation; add
derivations for claims B-1…B-5 (`docs/CLAIMS.md`), each with a reducing limit to a
Category A result. AC: no `[UNVERIFIED]` markers remain; every Category B claim has a
derivation and a reducing limit.

### The three `[UNVERIFIED]` markers, and what's already known about each

Checked this session (`grep -n UNVERIFIED docs/PHYSICS.md`) — all three look like **the
citation work is already done elsewhere in the project and PHYSICS.md just never got
updated to match**, not like open research questions. Confirm each independently before
trusting this, but start here rather than from zero:

1. **Line 191, linear GW memory** — cited as "Zel'dovich & Polnarev (1974); Braginsky &
   Thorne, *Nature* 327:123 (1987) `[UNVERIFIED]`". `docs/CLAIMS.md` A-7 (and its
   2026-07-31 change-log entry) already re-sourced this to **Favata, *Class. Quantum
   Grav.* 27:084036 (2010), arXiv:1003.3486, eq. (10k)**, open access, verified — with
   the 1987 Braginsky & Thorne letter explicitly demoted to "historical provenance only,
   no numbered equations, does not meet this project's citation bar." PHYSICS.md
   apparently never got the update. `INDEX.md` §1 (EQ near `source/memory.py`) should
   confirm the same citation is what the actual code (`source/memory.py:linear_memory`)
   uses.
2. **Line 213, array factor / grating-lobe / beamwidth** — cited as "Balanis, Antenna
   Theory ch. 6 `[UNVERIFIED]`" (a chapter reference — already disqualified by this
   project's own rule 1, "a chapter is not a citation"). Check `INDEX.md` §1 for
   EQ-013–EQ-019 (the scalar array-factor equations, `array/beamform.py`'s spin-1
   baseline) — those rows were verified against open sources during Sprint 6 and should
   name what to cite here instead. The paper's own reference list (`docs/paper/
   nature-draft.md`, ref. 16) cites **Orfanidis, *Electromagnetic Waves and Antennas*
   ch. 19** for the same spin-1 baseline material, labeled explicitly as "cited only for
   the scalar baseline" — worth checking whether that's the intended replacement or
   whether `INDEX.md` names something more specific with an equation number.
3. **Line 252, geodesic deviation** — cited as "MTW §37.2 `[UNVERIFIED]`" (also a chapter
   reference). `INDEX.md` §1, **EQ-045**, already reads: *"VERIFIED 2026-08-03 — read
   directly: [FH] eq. 3.11 is `d²Lⁱ/dt² = ½ (d²h^TT_ij/dt²) Lʲ`, matching the
   implementation exactly."* [FH] = Flanagan & Hughes, *New J. Phys.* 7:204 (2005). This
   one looks like a pure copy-paste fix: PHYSICS.md's own formula already matches this
   citation exactly (compare line 249's `d²ξ_i/dt² = ½ (d²h_ij^TT/dt²) ξ_j`).

### Claims B-1 through B-5: derivation + reducing-limit status (`docs/CLAIMS.md`, checked this session)

Per-claim starting point — **treat CLAIMS.md's own wording as possibly stale too**, the
same way PHYSICS.md was; cross-check against BACKLOG.md's ✅ markers for the tasks each
claim cites, since some of those tasks completed after the claim text was last edited:

- **B-1** (spin-2 array synthesis) — **already "Derived & validated"**, ADR-0003, with a
  2026-08-03 precision amendment. This one may already satisfy T-12.5's bar; check
  whether ADR-0003 itself contains a derivation with a reducing limit (to A-5/A-8) or
  whether that needs writing up in PHYSICS.md separately.
- **B-2** (mass/radius/density degeneracy) — **"Derived; all three breaking mechanisms
  now validated"** (T-4.1/4.2/4.6, T-4.3, T-4.5/B-7). Likely also close to done; same
  check as B-1.
- **B-3** (required aperture `D/λ ≳ r/w`) — **CLAIMS.md says "Not yet derived (T-10.1/10.2
  outstanding)"**, but T-10.1 and T-10.2 show ✅ in `docs/BACKLOG.md` Sprint 10 — **this
  claim's status text is stale**, not an open blocker. The independent corroboration
  CLAIMS.md already cites (`R/R_Fraunhofer ≈ 5.9×10⁹` at 40 AU / 1 kHz, focusing
  numerically degenerate with steering, `test_focus.py::
  test_focusing_is_degenerate_with_steering_at_40_au`) is real derivable content —
  writing it up properly with `array/focus.py:spot_size`'s actual formula as the
  reducing limit is probably most of this claim's remaining work.
- **B-4** (prime-frequency spatiotemporal focus) — **CLAIMS.md says "Partially derived
  ... recurrence period (T-9.8) still outstanding"**, but T-9.8 shows ✅ in
  `docs/BACKLOG.md` Sprint 9 — **also stale text**, not an open blocker. Recurrence
  period should already be verified in `tests/unit/test_focus_trajectory.py` or similar;
  find that test and cite it.
- **B-5** (radiative coupling negligible vs. near-zone) — **CLAIMS.md says "Not yet
  derived" outright**, and this one may be genuinely open. But campaign R6
  (`docs/paper/campaign/R6_channels.md`, `docs/paper/nature-draft.md` Results §"R6") has
  already **measured** exactly this: "radiative coupling is 1.3×10⁻³¹ of the near-zone
  channel," falsifier (radiative exceeding near-zone) did not fire. A measurement is not
  automatically a derivation — check whether the *mechanism* (why radiative flux must be
  smaller, from `F = P/c` momentum-flux scaling vs. Newtonian `1/r²` near-zone
  attraction) is written up anywhere as an actual derivation with a reducing limit, or
  whether that's the real remaining work for this claim specifically.

### Workflow (binding, from `CLAUDE.md`)

RESEARCH → IMPLEMENT → REVIEW → INDEX. For citation fixes, RESEARCH is mostly done above
(cross-referencing INDEX.md/CLAIMS.md) — verify it, don't skip it. For the B-1…B-5
derivations, this **is** the RESEARCH stage for whichever claims turn out to need new
content (B-5 most likely) — if a governing fact can't be verified, it becomes a spike,
not a forced derivation. Invoke `code-reviewer` before considering the task done
(physics changes get the dimensional-analysis / spin-2 checks per `CLAUDE.md`). Invoke
`indexer` after, since PHYSICS.md content changes may need `INDEX.md` cross-references
updated to point at the new derivations.

## The PR workflow (mandatory — `main` is protected)

```
git checkout -b <short-descriptive-branch-name>
...edit, commit...
git push newhome <branch-name>
gh pr create --repo sudo-install-gravity/tractor-beam-cathedral --base main --head <branch-name> --title "..." --body "..."
# wait for the three checks (test 3.10/3.11/3.12) to go green, then:
gh pr merge <number> --repo sudo-install-gravity/tractor-beam-cathedral --squash --delete-branch
# then sync local main:
git checkout main && git fetch newhome && git reset --hard newhome/main
git branch -D <short-descriptive-branch-name>   # squash-merges never show as "fully merged" locally -- expected, safe to force-delete after confirming the PR merged
git remote prune newhome
```

**Before merging, always confirm the green check run is for the PR's actual current
head** (`gh pr view <n> --repo sudo-install-gravity/tractor-beam-cathedral --json
headRefOid`) — a stale check result from an earlier push in the same PR looks identical
to a fresh one in a quick glance at `gh pr checks`.

⚠️ **`gh pr create`/`gh pr checks`/`gh pr merge` without `--repo` resolve against the
`origin` remote**, which on this checkout is a stale fork (`Thanatos7777/
tractor_beam_cathedral`), not `sudo-install-gravity/tractor-beam-cathedral` (`newhome`).
Always pass `--repo sudo-install-gravity/tractor-beam-cathedral` explicitly.

**T-2.9 changed repository settings once already (branch protection).** If T-12.5's work
somehow implies another settings-level change (it shouldn't — this is a docs-only task),
stop and ask the owner first; don't assume the earlier settings-change approval carries
forward to a new, different kind of change.

`jq` is **not installed** in this environment — use `gh pr checks <n>`'s plain-text
output (no `--json`) and grep/string-match it, not `--json`+`jq`.

## Traps

1. **`gh` identity:** active account is `sudo-install-gravity` (repo owner, admin).
   `Thanatos7777` is also stored but read-only. `gh auth status` confirms.
2. **Windows console shims are broken** — `mypy.exe`/`pytest.exe` exit 1 with no output.
   Always run `.venv\Scripts\python.exe tools\gates.py` (all five gates, honest
   reporting, never composed by hand) rather than the commands individually.
3. **`examples/` and `docs/` are covered by the gates now**, not just `src/`/`tests/`/
   `tools/` — `gates.py`'s `GATES` list and `.github/workflows/ci.yml` both check
   `examples/` for ruff+mypy as of 2026-08-10 (T-12.1). A PHYSICS.md-only change won't
   trip this, but worth knowing the coverage changed.
4. **This is a markdown-only task** (`docs/PHYSICS.md`, possibly `docs/CLAIMS.md` and
   `docs/INDEX.md` cross-references) — no `.py` files should need touching. If you find
   yourself editing `src/`, stop and reconsider whether this is really T-12.5's scope.
5. **Backlog task-header grammar is rigid** (`· 1 pts ·`, never `· 1 pt ·`); run
   `tools/schedule.py --plan` after editing headers.

## When blocked

Record the blocker under the task in `docs/BACKLOG.md` with a date, leave it un-✅'d.
Never delete a wall (rule 5); never guess a citation and mark it verified (rule 1) — an
unresolved `[UNVERIFIED]` marker honestly left in place is better than a confident wrong
one, exactly the standard this project already applied to EQ-040's near-miss.

## After T-12.5: switch back to Sonnet for T-12.7 and T-12.8

- **T-12.7** · `docs/GETTING_STARTED.md` · 2 pts · `sonnet` · deps T-12.5. From clone to
  first contribution; AC: a reader with no prior context can run the E2E scenario
  (`examples/deflection_scenario.py`, landed 2026-08-10).
- **T-12.8** · v1.0 release · 2 pts · `sonnet-low` · deps T-12.1–T-12.7. Tag, release
  notes, Zenodo DOI. AC: all 8 benchmarks pass; CI green; ledger publishes all four walls
  quantitatively. This is the project's last task.
