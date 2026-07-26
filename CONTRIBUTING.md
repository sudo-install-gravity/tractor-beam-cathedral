# Contributing to Tractor Beam Cathedral

This project is expected to span more than one human lifetime. That single fact drives every
rule below.

The goal is not to move fast. It is to ensure that a contributor arriving decades from now can
open any file, trace every equation to a primary source, and determine what we knew, what we
derived, and what we merely guessed. **Optimize for auditability over speed.**

---

## The one rule that matters most

**No physics formula is ever implemented from memory.**

Before writing physics code, confirm the governing equation, its primary source, and its
**exact equation number**. "MTW ch. 36" is not a citation. "MTW eq. 36.1" is — an auditor must
be able to open one page and check one line.

Every public function in `src/gwtb/source/`, `propagate/`, `bodies/`, and `array/` carries:

```python
def strain_tt(q_ddot, r, n_hat):
    """Transverse-traceless strain from a source quadrupole.

    Source: Maggiore Vol. 1, eq. 3.72
    """
```

CI enforces this mechanically (`tools/check_citations.py`). CI can only check that a citation
is *present and specific* — reviewers check that it is *correct*.

---

## Workflow

Every change follows **RESEARCH → IMPLEMENT → REVIEW → INDEX**.

| Stage | What happens | Gate to proceed |
|---|---|---|
| **RESEARCH** | Confirm equation, source, exact equation number, and validity domain | Citation verified. If not verifiable, **stop** — the work becomes a spike, not an implementation |
| **IMPLEMENT** | Write code and tests together | Tests pass; citation in docstring |
| **REVIEW** | Quality review plus the physics pass (dimensions, indices, spin-2, precision) | No unresolved Critical findings |
| **INDEX** | Update `docs/INDEX.md` — equation registry, module map, assumption ledger | Index reflects the change |

Contributors using AI assistants: this repo ships agent definitions in `.claude/agents/` that
implement these stages (`researcher`, `code-reviewer`, `indexer`). See [`CLAUDE.md`](CLAUDE.md).

---

## Definition of Ready

Do not start work on a task that lacks any of:

- An exact file path
- An exact function signature
- The formula and its citation, supplied up front
- Exact test assertions, with tolerances
- **Zero open design decisions**

If a task says "decide", "choose", or "figure out", it is not ready. It needs a spike first,
and spikes produce an architecture decision record in `docs/adr/` — never production code.

## Definition of Done

- [ ] Citation present in docstring and verified
- [ ] Unit tests pass; benchmark test added if the change is physics
- [ ] Dimensional-consistency test passes
- [ ] Review complete; all Critical findings resolved
- [ ] `docs/INDEX.md` current
- [ ] Feasibility ledger updated if a gap metric changed

---

## Physics review checklist

These are the failure modes that produce **plausible-looking wrong numbers**, which are far
more dangerous than crashes.

**Spin-2, not spin-1.** Gravitational radiation is spin-2; electromagnetic radiation is
spin-1. Any code adapted from antenna, radar, or acoustics references implements the wrong one
and will fail silently:

| | EM (spin-1) | GW (spin-2) |
|---|---|---|
| Polarization rotation | e^(iψ) | **e^(2iψ)** |
| Angle between states | 90° | **45°** |
| Element pattern | dipole | **quadrupole** |
| Superposed quantity | scalar amplitude | **tensor h_ij after TT projection** |

Array gain is **not** simply N² — elements of differing orientation suffer polarization
mismatch.

**Conservation stamps stay on.** Results from a non-momentum-conserving source are marked
`UNPHYSICAL`. Mass-dipole radiation exists only when momentum is not conserved, and such a
dipole term is ~10¹⁰ times the true quadrupole signal. Unstamped, that artifact looks like a
breakthrough.

**FP64 for phase.** Absolute phase over 40 AU is ~10¹⁰ wavelengths, beyond FP32's precision.
Strain ~10⁻⁴⁰ is *subnormal* in FP32. Use `gwtb.core.units` scaled representation.

**Analytic derivatives.** Luminosity needs the third derivative of the quadrupole moment.
Finite differencing at that order amplifies noise catastrophically.

**Never delete a wall.** Diffraction, coupling, and magnitude limits are *findings*. If a
change makes one disappear, the change is defective — not the wall.

---

## Sourcing standards

Preferred references, in order:

1. Misner, Thorne & Wheeler, *Gravitation* (1973)
2. Maggiore, *Gravitational Waves* Vol. 1 (2008)
3. Poisson & Will, *Gravity* (2014)
4. Balanis, *Antenna Theory*, 4th ed. — array and beamforming results
5. Peer-reviewed papers where no textbook covers it

**Epistemic firewall.** This project sits adjacent to a discredited literature. The
high-frequency gravitational wave (HFGW) claims of Baker et al. were reviewed and rejected by
the JASON Defense Advisory Panel in *High Frequency Gravitational Waves*, JSR-08-506 (Eardley
et al., MITRE, 2008), which found the proposed applications fundamentally wrong.

Never cite gravwave.com, drrobertbaker.com, or HFGW patent literature as authority. The
credible prior art on engineered gravitational radiation is Grishchuk & Sazhin, *Sov. Phys.
JETP* 38(2):215 (1974).

Being adjacent to bad literature does not make a claim wrong. It means the citation standard is
higher, not lower. See [`docs/CLAIMS.md`](docs/CLAIMS.md).

---

## Setup

```bash
pip install -e ".[dev]"
```

```bash
pytest
```

```bash
ruff check src tests tools && mypy src && python tools/check_citations.py
```

## Pull requests

Branch from `main`, keep changes scoped to one module where possible, and fill in the PR
template checklist. CI must be green: ruff, mypy, citation discipline, and the full test suite.

## Claims discipline

Every assertion belongs to exactly one category in [`docs/CLAIMS.md`](docs/CLAIMS.md):
**established physics**, **our derived extension**, or **open conjecture**. Adding a claim
means adding a row. Promotion between categories requires review; we never promote our own
work to "established" — that requires independent peer-reviewed publication.

Demotions happen, and are recorded with a date and reason rather than silently deleted. A
failed validation is data.
