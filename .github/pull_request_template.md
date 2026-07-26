## What this changes

<!-- One or two sentences. Link the task ID from docs/BACKLOG.md if there is one. -->

## Definition of Done

- [ ] Citation present in the docstring and verified against a primary source
      (`Source: <reference>, eq. <number>` — a chapter reference is not enough)
- [ ] Unit tests pass; a benchmark test is added if this change is physics
- [ ] Dimensional-consistency test passes
- [ ] Review complete; all Critical findings resolved
- [ ] `docs/INDEX.md` updated — equation registry, module map, assumption ledger
- [ ] Feasibility ledger updated if this change affects a gap metric

## Physics checklist

Skip this section if the change touches no physics.

- [ ] **Spin-2, not spin-1** — polarization rotates as e^(2iψ); h₊ and h× are 45° apart;
      superposition acts on the TT-projected tensor `h_ij`, not scalar amplitudes.
      *Any logic adapted from antenna, radar, or acoustics references is spin-1.*
- [ ] **Conservation stamp intact** — non-momentum-conserving results still carry
      `UNPHYSICAL`
- [ ] **FP64 for phase accumulation** — no float32 outside an authorized split-phase kernel
- [ ] **Analytic derivatives** — no finite differencing of the quadrupole moment
- [ ] **No wall removed** — diffraction, coupling, and magnitude limits are findings,
      not bugs

## Claims

<!-- Does this add or change an assertion? If so, which docs/CLAIMS.md category:
     A (established physics), B (our derived extension), or C (open conjecture)? -->

## Notes for reviewers

<!-- Anything you are unsure about, conventions you had to choose, or assumptions
     that deserve a second opinion. Uncertainty stated up front is cheaper than
     uncertainty discovered in Sprint 9. -->
