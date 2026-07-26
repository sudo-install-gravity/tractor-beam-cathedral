# Errata in Cited Sources

Errors we have found in the primary literature this project cites, with the verification that
established them.

**This file exists to prevent a specific failure mode.** Our code is correct and the published
source is wrong. Without this record, a future contributor checking our implementation against
the paper would conclude *we* have the bug and "fix" working code to match a typo. On a project
measured in generations, that is not a hypothetical.

Rules:

- Never silently correct a source. Record the discrepancy here, cite the corrected form in the
  code, and link the code comment to this file.
- Every entry must show how the error was established — numerically, or against an independent
  source. "It looks wrong" is not an entry.
- An error in a worked example does not discredit a source's derivations. Scope each entry
  precisely.

---

## ERR-001 — Flanagan & Hughes (2005), Eq. (4.41): wrong diagonal component

**Source:** Flanagan, É.É. & Hughes, S.A., "The basics of gravitational wave theory,"
*New J. Phys.* **7**:204 (2005), arXiv:gr-qc/0501041v3.

**Scope:** §4.4 "Numerical estimates" — the worked circular-binary example only. The derivations
in §4.1 (Eqs. 4.17, 4.19, 4.20, 4.22, 4.23) are correct and we rely on them.

**As printed**, the quadrupole moment tensor for a circular binary:

```
              ⎡ cos²Ωt − ⅓    cosΩt sinΩt    0  ⎤
I_ij = μR²    ⎢ cosΩt sinΩt   cos²Ωt − ⅓     0  ⎥
              ⎣ 0             0             −⅓  ⎦
```

**Correct form** — the `I_22` component must be `sin²Ωt − ⅓`:

```
              ⎡ cos²Ωt − ⅓    cosΩt sinΩt    0  ⎤
I_ij = μR²    ⎢ cosΩt sinΩt   sin²Ωt − ⅓     0  ⎥
              ⎣ 0             0             −⅓  ⎦
```

**Why:** the paper's own Eq. (4.39) defines `I_ij = μ(x_i x_j − ⅓R²δ_ij)` with
`x = (R cos Ωt, R sin Ωt, 0)`. Then `I_22 = μ(y² − ⅓R²) = μR²(sin²Ωt − ⅓)`. The printed form
also fails the trace check: with `cos²Ωt` twice on the diagonal the trace is not `−μR²/3·0`
as required for the relationship to the trace-free moment to hold consistently.

**Verified numerically:** the printed form differs from `Eq. (4.39)` evaluated directly by
`9.2e-2` (absolute, in units μR²=1) at Ωt = 0.7391. The corrected form agrees exactly (0.0).

---

## ERR-002 — Flanagan & Hughes (2005), Eq. (4.42): non-symmetric tensor

**Source:** as ERR-001.

**As printed**, the second time derivative:

```
                        ⎡  cos2Ωt   sin2Ωt   0 ⎤
Ï_ij = −2Ω²μR²         ⎢ −sin2Ωt  −cos2Ωt   0 ⎥
                        ⎣  0        0        0 ⎦
```

**Correct form** — the `(2,1)` entry must be `+sin2Ωt`:

```
                        ⎡  cos2Ωt   sin2Ωt   0 ⎤
Ï_ij = −2Ω²μR²         ⎢  sin2Ωt  −cos2Ωt   0 ⎥
                        ⎣  0        0        0 ⎦
```

**Why:** as printed the tensor is **not symmetric** (`Ï_12 ≠ Ï_21`). A mass quadrupole moment is
symmetric by construction — it is built from `x_i x_j` — and differentiation preserves symmetry.
The printed form is therefore impossible regardless of the algebra.

Directly: `I_12 = μR² cosΩt sinΩt = ½μR² sin2Ωt`, so
`Ï_12 = −2Ω²μR² sin2Ωt`, giving `+sin2Ωt` inside the `−2Ω²μR²` prefactor for **both** off-diagonal
entries.

**Verified numerically:** against `Eq. (4.39)` differentiated by central difference at
Ωt = 0.7391 with μ=R=Ω=1:

| Form | Symmetric? | Max error vs. ground truth |
|---|---|---|
| As printed | **No** | 3.98 |
| Corrected | Yes | 2.5e-8 (finite-difference limited) |

**Consequence for this project:** `tests/benchmarks/test_binary.py` (T-1.9) must implement the
**corrected** form. A test written from the paper verbatim would fail against correct code, and
the natural but wrong response would be to change the code.

---

## Verification method

Both entries were established by differentiating the source's own upstream definition
(Eq. 4.39) numerically and comparing against the printed downstream results. Reproduce with:

```bash
pytest tests/benchmarks/test_binary.py -k errata
```
