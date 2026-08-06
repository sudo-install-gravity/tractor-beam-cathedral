# Attribution Log — Human vs. LLM Origination

Appendix material for the Nature submission's case study on LLM-assisted bridging between a
physicist's raw mathematical understanding and the applied/technologist's conceptual model
needed to build a device from it.

## Purpose and method

This log distinguishes, for each significant idea/decision in the project, who originated it:

- **User** — the idea, question, or reframing came from the human collaborator (dpaulday).
- **Claude** — the idea, derivation route, or implementation choice came from the assistant.
- **Joint / back-and-forth** — neither party's contribution is separable; the idea emerged from
  iteration (e.g., user posed a constraint, Claude proposed three options, user picked one and
  changed it).
- **Unknown** — plausible either way; not documented, not yet confirmed by the user.

Confidence tag on every entry:

- **[documented]** — traceable to an artifact (commit message, ADR, this log's own live entries
  going forward) that states or strongly implies who originated it.
- **[inferred]** — my best reconstruction from the shape of the repo (e.g., "an ADR that opens
  by rejecting the task's premise" implies the premise was supplied by someone other than the
  agent that caught the error) — **needs your confirmation.**
- **[unknown]** — I have no basis to attribute this one; recorded as a placeholder so it isn't
  silently lost, not as a guess.

**Known limitation, stated plainly:** I (Claude) have no memory of conversations prior to
2026-08-06 unless they were saved to a memory file or are reconstructable from the repository.
Git commit authorship in this repo is uniformly the operator's account regardless of who — human
or model — proposed the underlying idea in conversation, so `git blame` cannot settle
attribution here. Everything below dated before this log's creation is a **reconstruction**,
not a record, until you correct it. Rows added after 2026-08-06 are written live, during the
session in which the idea appeared, and are load-bearing "documented" going forward.

---

## Retroactive reconstruction (pre-2026-08-06)

| Date | Idea / decision | Attribution | Confidence | Basis |
|---|---|---|---|---|
| 2026-07-26 | Core project framing: model gravitational-wave emission as a deliberately engineered "tractor beam" for asteroid deflection, quantifying the feasibility gap rather than assuming it closes | User | [documented] | Confirmed by user 2026-08-06 |
| 2026-07-26 | Adopt the feasibility-ledger discipline: every run must report the quantitative gap to real deflection, as the mechanism that keeps this project distinguishable from the discredited HFGW literature | User (idea), Claude (implementation) | [documented] | Confirmed by user 2026-08-06: "my idea, your... implementation" |
| 2026-07-26 | Epistemic firewall against Baker/HFGW literature; cite Grishchuk & Sazhin 1974 instead | Claude | [documented] | Confirmed by user 2026-08-06 — surfaced by a research pass, not user domain knowledge |
| 2026-07-26 | RESEARCH → IMPLEMENT → REVIEW → INDEX workflow; Definition-of-Ready gate; agent-tier scheduling (`tools/schedule.py`) | User (ideas/methodology), Claude (implementation) | [documented] | Confirmed by user 2026-08-06: "my ideas, your implementation" |
| 2026-07-27 | ADR-0003 spin-2 superposition formulation, `cos(2Δψ)` mismatch factor, 90°-cancellation result — including the framing question "does EM array intuition even hold for spin-2?" | Claude | [documented] | Confirmed by user 2026-08-06 — arose during the spike itself, not posed by the user in advance |
| 2026-07-31 | Catch: `sin(kR)/(kR)` in the T-4.5 task spec is spin-1 antenna machinery, not GW physics — task premise wrong | Claude | [documented] | Confirmed by user 2026-08-06 |
| 2026-08-03 | Catch: B-1's `exp(−4σ²)` tolerance law is an N→∞ limit, contradicted by its own printed table; derive the exact finite-N bias | Claude | [documented] | Confirmed by user 2026-08-06 |
| 2026-08-06 | Commission this attribution log itself, framed as a case study on LLMs bridging physicists' raw math and technologists' applied/conceptual understanding | User | [documented] | This conversation |

**Action needed from you:** for every "Unknown" row above, a one-line correction ("that framing
was mine" / "that was you noticing it, I just verified" / "genuinely can't recall, mark it
joint") is enough — I'll fold it in and mark it [documented].

---

## Live log (2026-08-06 onward)

Entries from here are written in the session where the idea surfaced, so attribution is
first-hand rather than reconstructed.

| Date | Idea / decision | Attribution | Confidence | Note |
|---|---|---|---|---|
| 2026-08-06 | Requested a running log separating the user's original ideas from Claude's implementation choices, as an appendix to the Nature paper — framed explicitly as a case study on LLMs bridging physicists' raw mathematical understanding and the distinct conceptual model technologists need to apply it | User | [documented] | This request. Note the framing itself — "raw math vs. applied conceptual gap" — is a substantive intellectual contribution in its own right, not just a logging preference, and is logged as such |
| 2026-08-06 | Proposed marking retroactive entries with confidence tags (documented/inferred/unknown) rather than asserting attribution the assistant can't actually verify | Claude | [documented] | Proposed in response to the user's request, to avoid fabricating attribution history |

---

## Notes for the eventual Nature appendix

- The interesting case-study material is likely to live in the **[inferred]** rows above once
  corrected — those are the moments where a physics idea (spin-2 vs. spin-1 intuition, a task
  premise silently importing the wrong domain's formula) crossed into an engineering artifact
  (a task spec, a superposition routine) and something caught or didn't catch the mismatch.
- Consider also logging, going forward, not just *who* proposed an idea but *what kind of gap*
  it crossed — e.g., "user supplied physical intuition, Claude supplied the formal derivation
  route" vs. "Claude flagged a citation gap, user decided how to resolve it." That finer texture
  is probably more useful for the case study than a flat user/Claude binary.
