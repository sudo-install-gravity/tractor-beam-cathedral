"""B-1 alignment tolerance — the finite-N bias in `gain/N^2 ~ exp(-4 sigma^2)`.

Scratch prototype. NOT production code. Evidence for the 2026-08-03 amendment
to ADR-0003 (claim B-1).

Question: ADR-0003 states the alignment-tolerance law

    gain / N^2  ~  exp(-4 sigma^2)

and claims it "matches to ~1e-4 across sigma in [0, 20] deg" at N = 100 and
N = 1000. The committed test asserts only abs=2e-3 at N = 200. Why the gap --
new knowledge, a disagreement, or something else?

Answer: neither. The law is the N -> infinity limit. At finite N the estimator
carries an exact positive bias that neither document names:

    E[gain/N^2] = exp(-4 sigma^2) + (1 - exp(-4 sigma^2)) / N

Derivation. With z_n = exp(2 i psi_n), psi_n ~ N(0, sigma^2) iid, and
mu = E[z] = exp(-2 sigma^2) (the normal characteristic function at t = 2):

    E[|S|^2] = sum_n E[|z_n|^2] + sum_{n != m} E[z_n] E[z_m*]
             = N * 1 + N(N-1) mu^2

    E[gain] = E[|S|^2] / N^2 = mu^2 + (1 - mu^2)/N

and mu^2 = exp(-4 sigma^2). The `N * 1` term is the |z|^2 = 1 self-term: it
cannot vanish, and divided by N^2 it leaves a 1/N floor.

Three checks:

  A. The formula, against direct simulation with the sampling noise driven
     down far enough that the bias is resolvable (400k realizations).
  B. The 1/N scaling of the deviation.
  C. What ADR-0003's own printed table implies -- i.e. whether its "~1e-4"
     summary is consistent with the numbers directly beneath it.

Run: .venv\\Scripts\\python.exe scratchpad\\spike_b1_alignment_bias.py  (~40 s)
Prints CONFIRMED or MISMATCH.
"""

from __future__ import annotations

import numpy as np

REALIZATIONS = 400_000


def law(sigma_deg: float) -> float:
    """ADR-0003's stated law: the N -> infinity limit."""
    return float(np.exp(-4 * np.radians(sigma_deg) ** 2))


def predicted(n_elements: int, sigma_deg: float) -> float:
    """The finite-N expectation this spike proposes."""
    return law(sigma_deg) + (1.0 - law(sigma_deg)) / n_elements


def bias(n_elements: int, sigma_deg: float) -> float:
    return (1.0 - law(sigma_deg)) / n_elements


def measure(n_elements: int, n_real: int, sigma_deg: float, seed: int) -> tuple[float, float]:
    """Mean gain fraction and its standard error, vectorized over realizations."""
    rng = np.random.default_rng(seed)
    s = np.radians(sigma_deg)
    psi = rng.normal(0.0, s, size=(n_real, n_elements))
    c = np.cos(2 * psi).sum(axis=1)
    d = np.sin(2 * psi).sum(axis=1)
    g = (c * c + d * d) / n_elements**2
    return float(g.mean()), float(g.std(ddof=1) / np.sqrt(n_real))


def check_a() -> bool:
    """The bias formula, against simulation with noise suppressed."""
    print("A. Finite-N bias formula vs direct simulation")
    print(f"   {REALIZATIONS:,} realizations per point\n")
    print(
        f"   {'sigma':>6} {'N':>6} {'obs dev':>12} {'std err':>9} "
        f"{'pred bias':>11} {'obs/pred':>9}  verdict"
    )
    worst = 0.0
    for n in (100, 200, 1000):
        for sd in (2.87, 10.0, 20.0):
            m, se = measure(n, REALIZATIONS, sd, seed=12345 + n * 7 + int(sd * 100))
            dev, b = m - law(sd), bias(n, sd)
            ratio = dev / b
            worst = max(worst, abs(ratio - 1.0))
            flag = "ok" if abs(ratio - 1.0) < 0.10 else "OFF"
            print(f"   {sd:6.2f} {n:6d} {dev:+12.3e} {se:9.1e} {b:+11.3e} {ratio:9.4f}  {flag}")
    ok = worst < 0.10
    print(f"\n   worst departure from unity: {worst:.3f}  -> {'CONFIRMED' if ok else 'MISMATCH'}\n")
    return ok


def check_b() -> bool:
    """The deviation must fall as 1/N."""
    print("B. Does the deviation scale as 1/N?  (sigma = 10 deg, independent seeds)\n")
    ratios = []
    prev = None
    for n in (100, 200, 400, 800, 1600):
        d, se = measure(n, REALIZATIONS, 10.0, seed=999 + n)
        d -= law(10.0)
        note = ""
        if prev is not None:
            r = prev / d
            ratios.append(r)
            note = f"   ratio to previous = {r:5.3f}  (expect 2.000)"
        print(f"   N={n:5d}   dev = {d:+.4e}  +/- {se:.1e}{note}")
        prev = d
    mean_ratio = float(np.mean(ratios))
    ok = abs(mean_ratio - 2.0) < 0.25
    print(
        f"\n   mean halving ratio: {mean_ratio:.3f} (expect 2.000)"
        f"  -> {'CONFIRMED' if ok else 'MISMATCH'}\n"
    )
    return ok


def check_c() -> bool:
    """Is ADR-0003's '~1e-4' summary consistent with its own printed table?"""
    print("C. ADR-0003's printed table (N = 1000) vs its '~1e-4 across [0,20] deg' summary\n")
    # Transcribed verbatim from ADR-0003 section 3.
    adr_sigma = (1.0, 2.0, 2.9, 5.0, 10.0, 20.0)
    adr_measured = (0.99879, 0.99515, 0.98978, 0.97010, 0.88562, 0.61511)
    adr_law = (0.99878, 0.99514, 0.98980, 0.97000, 0.88528, 0.61423)
    print(f"   {'sigma':>6} {'ADR meas':>10} {'ADR law':>10} {'its own dev':>12} {'vs ~1e-4':>10}")
    worst_dev = 0.0
    for sd, m, lw in zip(adr_sigma, adr_measured, adr_law, strict=True):
        dev = m - lw
        worst_dev = max(worst_dev, abs(dev))
        print(f"   {sd:6.2f} {m:10.5f} {lw:10.5f} {dev:+12.2e} {dev / 1e-4:9.1f}x")
    print(f"\n   worst deviation in the ADR's OWN table: {worst_dev:.2e}")
    overstated = worst_dev > 3e-4
    print(
        f"   -> the '~1e-4' summary is {'OVERSTATED' if overstated else 'supported'}"
        f" by a factor of ~{worst_dev / 1e-4:.0f}"
    )
    print("\n   And at the smaller N the ADR also claims (N = 100), the bias ALONE is:")
    for sd in (10.0, 20.0):
        print(
            f"      sigma={sd:5.1f} deg -> {bias(100, sd):.2e}   ({bias(100, sd) / 1e-4:.0f}x the claim)"
        )
    print("\n   -> CONFIRMED: '~1e-4 across [0,20] deg at N=100 and N=1000' cannot hold.")
    print("      It holds only for sigma <~ 5 deg, and only at the larger N.\n")
    return overstated


def main() -> None:
    print(__doc__.split("Run:")[0].rstrip())
    print("\n" + "=" * 78 + "\n")
    a, b, c = check_a(), check_b(), check_c()

    print("=" * 78)
    print("\nWhat this means for the committed test at its N = 200, 200 realizations:")
    for sd in (10.0, 20.0):
        _, se_big = measure(200, REALIZATIONS, sd, seed=4242 + int(sd))
        per_run = se_big * np.sqrt(REALIZATIONS / 200)
        print(
            f"   sigma={sd:5.1f} deg: irreducible bias {bias(200, sd):.2e}"
            f"  +  per-run noise ~{per_run:.1e}"
        )
    print(
        "\n   The old abs=2e-3 was therefore CORRECTLY SIZED, not sloppy -- and it could\n"
        "   NOT have been tightened to the ADR's ~1e-4 at N=200: the bias alone is 5.7e-4.\n"
        "   The defect is in ADR-0003's summary sentence, not in the test.\n"
        "\n   Fix: assert against the bias-corrected prediction, which lets the tolerance\n"
        "   drop to the sampling noise AND makes the 1/N term load-bearing.\n"
        "\n   TRAP, found by code-reviewer 2026-08-03 and worth keeping with this evidence:\n"
        "   the tolerance must be STATISTICAL (a multiple of the estimator's standard\n"
        "   error), not a flat absolute number. The SE spans 30x across sigma in\n"
        "   [2.87, 20] deg, so a single value cannot fit both ends. A flat abs=1e-4 was\n"
        "   tried first, sized off the observed deviation for ONE seed -- it sat at\n"
        "   0.7 SE at sigma=20 deg and failed 13 of 30 reseeds while passing on the\n"
        "   committed seed. Sizing a tolerance from one seed's residual instead of from\n"
        "   the standard error is the same class of error as the ADR overstatement this\n"
        "   spike exists to correct: mistaking one favourable draw for a margin.\n"
    )
    verdict = a and b and c
    print("=" * 78)
    print(
        "\nVERDICT: "
        + (
            "CONFIRMED -- bias formula holds; ADR-0003 summary needs amending"
            if verdict
            else "MISMATCH -- do not amend anything, re-derive first"
        )
    )


if __name__ == "__main__":
    main()
