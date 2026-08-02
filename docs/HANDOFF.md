# Handoff — SPIKE-4.5, for a new Opus session

Generated 2026-08-02. Repo state at handoff: commit `f152ab4`, working tree
clean, pushed to `origin/main`. **835 tests passing**, 3 skipped (CuPy/PyVista
optional, absent on this host), all five sanity checks green. `schedule.py
--next` reports **"nothing to schedule"** — 106 of 117 tasks complete, and
everything remaining needs external input (this task is one of two such
items; the other, T-2.9, needs the repo made public and is out of scope here).

## Read first, in this order

1. `../CLAUDE.md` — operating rules, workflow, Definition of Ready/Done. Note
   in particular: spikes produce a decision record (an ADR) and **no
   production code** until the decision is made; rule 1 (citation discipline);
   rule 4 (spin-2, not spin-1 — the project's highest-risk bug class).
2. `HANDOVER.md` §0 and §9 — current project state and this exact task's
   status, written by the session that left this handoff.
3. `BACKLOG.md`, the **T-4.5** entry (search for it — it's in Sprint 4).
4. `INDEX.md`, **OQ-7** in the Open Questions table.

Those three (BACKLOG T-4.5, INDEX OQ-7, HANDOVER §9) currently tell the same
story and are kept in sync; if you find them disagreeing, that is itself a
finding — figure out which one is stale before proceeding.

## The task

**SPIKE-4.5**, `opus` tier, 2 pts (the spike itself; T-4.5's own 3 pts follow
once the spike closes it). Not yet a line item in `BACKLOG.md` — add one when
you start, following the `SPIKE-9.6` entry there as the formatting template
(a completed spike in this same backlog, same structure you're about to add).

**Goal:** unblock `T-4.5 · Finite-size retardation correction`, which needs
`finite_size_correction(sphere, wavelength) -> float` in
`src/gwtb/bodies/multipole.py` — the leading correction, in `R/λ`, to the
quadrupole radiation formula for a source whose size is not negligible
compared to the wavelength.

## Why this is blocked, and what's already been ruled out

A `researcher` pass (2026-07-31) searched hard and came back **UNVERIFIED**,
finding the task's own premise was wrong. Both form factors originally named
in the backlog are the wrong multipole order:

- `sin(kR)/(kR)` (leading term `1 − (kR)²/6`) is `l = 0`, **spin-1 antenna
  machinery** — exactly the borrowed-from-antennas trap CLAUDE.md rule 4
  exists to catch. It must not be used for a mass quadrupole.
- `3 j₁(kR)/(kR)` (leading term `1 − (kR)²/10`) is the correct closed-form
  Fourier transform of a uniform sphere's **density** — but that's the
  total-mass **monopole** term, not the quadrupole.

Volume-integrating `j_l(kr)` against `r^{l+2} dr` gives the general result
`1 − (kR)²(l+3)/[2(2l+3)(l+5)]`, so the `l = 2` (quadrupole) case works out to

```
1 − 5(kR)²/98
```

**This is a derivation, not yet a citation.** No numbered equation for it was
found anywhere accessible. Thorne, *Rev. Mod. Phys.* 52:299 (1980) is the
likely original primary source but is paywalled and its equation number is
unconfirmed — **do not cite it with a specific equation number unless you have
independently verified the number yourself.** Citing a guessed equation
number would be worse than citing none.

## What to actually do

1. **Verify the `1 − 5(kR)²/98` derivation independently**, don't just trust
   the sketch above. Re-derive it from the spherical Bessel expansion of the
   quadrupole moment integral yourself, on paper or in a scratch script, and
   confirm the arithmetic (`(l+3)/[2(2l+3)(l+5)]` at `l=2` is `5/98` —
   check this multiplication).
2. **Get a second, independent numerical confirmation**, the same pattern
   that resolved this session's T-12.3 energy-flux prefactor ambiguity
   (see `tests/benchmarks/test_energy_conservation.py`'s docstring for that
   precedent): numerically integrate the actual quadrupole source formula for
   a finite uniform sphere (e.g. discretize the sphere into point masses or
   integrate the exact retarded-field expression) and confirm the resulting
   `R/λ` correction converges to `1 − 5(kR)²/98` in the small-`kR` limit, to
   several digits, independent of the analytic derivation. Do not skip this —
   it is what makes the derivation trustworthy without a citable source.
3. **Optionally**, spend a *bounded* amount of time (not another open-ended
   search) checking whether Thorne 1980's exact equation number is reachable
   through a library proxy, Google Books preview, or a citing paper that
   quotes it directly with page/eq. number. If found and verified, that
   becomes the primary citation and the derivation becomes corroborating
   evidence instead of the primary source. If not found quickly, don't
   chase it further — the numerically-verified derivation is sufficient
   basis to proceed, exactly as it was for T-12.3.
4. **Write an ADR** (`docs/adr/0007-...md` — check the next free number)
   recording: the decision (`1 − 5(kR)²/98`, Category B derivation), why the
   two originally-proposed form factors are wrong (spin-1 trap / wrong
   multipole order — copy the reasoning above, it's already correct), the
   independent numerical verification and its precision, and the reversal
   condition (what would need to be found to promote this to Category A).
   Use `docs/adr/0006-focused-field-far-field-regime.md` as a structural
   template — it's the most recent spike-output ADR in this repo.
5. **Recompute the AC.** `BACKLOG.md`'s current T-4.5 acceptance criterion
   (`→ 1 as R/λ → 0`; `departs from unity by >1% when R/λ > 0.1`) was written
   against the *wrong* form factor. At `R/λ = 0.1`, `k = 2π/λ`, so
   `kR = 2πR/λ = 2π × 0.1 ≈ 0.628`, and `5(kR)²/98 ≈ 5(0.628)²/98 ≈ 0.0201` —
   about **2%, not the originally-stated threshold**. Verify this arithmetic
   yourself and correct the AC in `BACKLOG.md` to match the actual formula
   before or when you implement.
6. **Implement** `finite_size_correction(sphere, wavelength) -> float` in
   `src/gwtb/bodies/multipole.py`, citing the ADR (not a fabricated equation
   number) per the pattern other project-derivation results already use —
   see `EQ-014`, `EQ-030`, `EQ-031` in `INDEX.md`'s equation registry for
   exactly how a "this project's own derivation" citation is worded in a
   docstring, and `tools/check_citations.py` for what its regex actually
   requires (a docstring line matching `Source: ..., eq. ...` — for a
   derivation with no external equation number, the established convention
   in this codebase is `Source: <ADR path>, eq. n/a` or similar; check how
   `EQ-030`/`EQ-031`'s docstrings phrase this in `array/focus.py` and
   `core/backend.py` and match that style exactly).
7. **Test it.** Both the closed-form limits (`→ 1` as `R/λ → 0`) and the
   corrected departure threshold from step 5, plus — given rule 4's risk
   class — a regression test that would fail if someone "fixed" this back to
   `sin(kR)/(kR)` or `3j₁(kR)/(kR)`, mirroring how `ADR-0006`'s traps are
   guarded by name in `tests/unit/test_focused_field.py`.

## Gate before calling it done

```
.venv\Scripts\ruff.exe check src tests tools
.venv\Scripts\ruff.exe format --check src tests tools
.venv\Scripts\mypy.exe src
.venv\Scripts\python.exe tools\check_citations.py
.venv\Scripts\pytest.exe -q
```

All five must be green. Then:

- Mark `T-4.5` ✅ in `BACKLOG.md`, and add the `SPIKE-4.5` line item marked ✅
  (following `SPIKE-9.6`'s format).
- Run `.venv\Scripts\python.exe tools\schedule.py --next` — landing T-4.5
  unblocks `T-4.7`, `T-4.8`, `T-4.9` (transitively stranded behind it; check
  `--plan`'s "UNREACHABLE" section beforehand to confirm exactly which tasks
  free up). Those are `sonnet-low`/`sonnet` tier — hand them to a Sonnet
  session rather than implementing them yourself in this Opus session, per
  the project's own tier-matching rule (`CLAUDE.md`, "batch by tier").
- Update `INDEX.md`: add an `EQ-0NN` row for the new result, resolve `OQ-7`
  (mark it `~~OQ-7~~ RESOLVED`, same pattern as the resolved `OQ-6` entry
  already in that file), update the equation-registry validation-status table.
- Update `HANDOVER.md` §0 with a dated note (same pattern as the existing
  entries there) and correct §9's now-stale "T-4.5 is blocked" section.
- Commit and push. Use a `-F <message-file>` commit (not an inline `-m`
  string) if your message contains double quotes — inline quoting broke a
  commit in the immediately preceding session on this exact repo.

## If you get stuck

If the independent numerical verification in step 2 does **not** converge to
`1 − 5(kR)²/98` — i.e., if the derivation itself turns out to be wrong, not
just uncited — **stop and do not implement anything**. That would mean the
task needs a second spike to re-derive from scratch, not a docstring fix. Add
a finding to `INDEX.md`'s assumption ledger describing exactly where the
derivation and the numerical check disagree, and leave `T-4.5` blocked with
an updated reason. Per `CLAUDE.md` rule 5, a wall is a finding — do not paper
over a derivation that doesn't check out numerically just to close the task.

## Delete this file when done

This is a one-shot handoff, not a permanent doc. Once SPIKE-4.5 lands and the
above updates are made, delete `docs/HANDOFF.md` in the same commit — it has
served its purpose and a stale handoff sitting in the repo is worse than none
(same principle `HANDOVER.md` §0 already states about not trusting written
task counts over `schedule.py --status`).
