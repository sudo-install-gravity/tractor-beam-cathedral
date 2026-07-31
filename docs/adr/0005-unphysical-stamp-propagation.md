# ADR 0005 — Propagating the UNPHYSICAL stamp through NumPy

- **Status:** Accepted
- **Date:** 2026-07-31
- **Arises from:** T-2.2 `StampedResult`

## Context

`CLAUDE.md` rule 2 says any result computed from a non-momentum-conserving source is stamped
`UNPHYSICAL: violates d_mu T^mu-nu = 0`, and that the stamp is never stripped. T-2.1 built the
*detector* (`audit`). T-2.2 must build the *carrier*: a stamp that survives being computed with.

The threat is specific. A mass-dipole artifact is roughly 10¹⁰ times the true quadrupole signal.
Unstamped, it does not look like a bug — it looks like a breakthrough. The dangerous moment is
not when the number is produced, it is three function calls later, once the number has been
through arithmetic and no longer remembers where it came from.

So the requirement is not "attach a label". It is "attach a label that ordinary NumPy use cannot
detach".

## The obvious design does not work

The natural implementation is an `np.ndarray` subclass with `__array_finalize__`. It is the
documented NumPy extension point, it is less code, and it propagates provenance through
arithmetic, slicing, ufuncs and reductions essentially for free.

It was implemented and measured first (NumPy 2.4.6):

| Operation | Subclass keeps stamp? |
|---|---|
| `a * 2` | ✅ |
| `a[1:]` | ✅ |
| `np.sin(a)` | ✅ |
| `a.sum()` | ✅ |
| **`np.asarray(a)`** | ❌ **silently returns a bare `ndarray`** |
| **`np.array(a)`** | ❌ **silently returns a bare `ndarray`** |

`np.asarray` on an `ndarray` subclass takes a fast path that returns a base-class array **without
ever calling `__array__`**. Defining `__array__` on the subclass does not help — it is not
consulted. There is no hook, and therefore no way to make the loss loud.

That single row is disqualifying. `np.asarray` is the most likely call to appear in exactly the
plotting, export and serialization code where an unstamped 10¹⁰ artifact would do its damage, and
it is the call least likely to be scrutinised in review.

## Decision

**`StampedResult` is an explicit wrapper, not an `ndarray` subclass.**

Because the wrapper is not an `ndarray`, `np.asarray` *is* obliged to call `__array__` — which is
the hook the subclass denied us. There, a stamped result raises `StampStrippedError` instead of
converting.

The cost is that arithmetic no longer comes free. It is routed back through `__array_ufunc__`,
with each Python operator (`__add__`, `__radd__`, …) delegating to the corresponding ufunc, and
`__array_priority__` set so that `ndarray + StampedResult` defers to the wrapper rather than
broadcasting the stamp away.

Three supporting rules:

- **Unphysicality is contagious.** Any result computed from a stamped operand is stamped.
  Distinct provenances are joined, so a value derived from two unphysical sources names both.
- **`out=` is refused.** Writing into a caller-supplied array would move the numbers somewhere
  the provenance cannot follow — the same laundering hole by another route.
- **There is no `unstamp()` method.** The sanctioned way to obtain raw numbers is the `.value`
  attribute: explicit, greppable, and visible in review. A method named `unstamp` would advertise
  stamp removal as a supported operation, which rule 2 says it is not.

## Verification

`tests/unit/test_stamped_result.py`, 36 tests, all passing. Each AC clause is covered
individually: survives arithmetic (11 operators, both operand orders), survives ufuncs and
reductions, survives slicing and scalar indexing, survives `str()` and `repr()`, is carried by
JSON serialization — and `np.asarray` / `np.array` / `out=` each raise rather than strip.

Two tests guard the *negative* space: an unstamped result still converts cleanly (the guard is on
the stamp, not on the wrapper), and `StampedResult` has no `unstamp` attribute.

## Consequences

**Positive.** T-2.4 (the flagged dipole radiation term) has a carrier that cannot silently lose
its flag, which is the entire reason T-2.4 is allowed to exist. The stamp now survives the code
paths that actually threatened it.

**Negative.** `StampedResult` is not an `ndarray`, so it will not drop into a function that
requires one. **This is the intended behavior, not a limitation to be worked around** — such a
function is precisely a place where the stamp would have been lost. Callers who genuinely need
raw numbers take `.value`, which leaves a reviewable trace.

Non-ufunc NumPy functions (`np.concatenate`, `np.stack`) route through `__array__` and therefore
raise on stamped input. Left deliberately unsolved: no current caller needs them, and
`__array_function__` support should be added against a real use case rather than speculatively.

## Reversal condition

If a future NumPy exposes a hook that makes subclass coercion interceptable, the subclass design
becomes viable and is materially simpler. Reversing requires demonstrating, with a test in the
shape of the table above, that `np.asarray` on the subclass **raises or warns** — not merely that
provenance survives arithmetic. Arithmetic was never the failing case.
