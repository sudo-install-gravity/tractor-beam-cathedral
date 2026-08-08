# Threat-population literature survey — inputs for the deflection tradespace section

**Status:** verified 2026-08-08 — the batched `researcher` pass ran the same day (6
VERIFIED, 4 VERIFIED-ALT, 1 carve-out, 0 firewall flags), and the resulting sprint is
**`docs/BACKLOG.md` Sprint 14**, whose header carries the authoritative per-source
verification block. Where this file and the Sprint 14 header disagree, the sprint header
wins. Key outcomes folded in below: Bennu's mass/density cite **Scheeres et al., *Nature
Astron.* 3:352 (2019)** (not Lauretta 568:55 — wrong paper for that claim); the secular
deflection amplification is **Izzo, AAS 05-141 (2005), eqs. (1)–(3)** (open ESA PDF;
equation numbers confirmed by eye; the PDF's stale *metadata* title mentions a debris
cloud — template reuse, content is correct); Greenstreet et al. 2020 medians are
**1.4/0.76/0.55/0.46/0.38 cm/s at 10/20/30/40/50 yr** for a 1 R⊕ miss; the SDT 2017
2.6 g/cm³ density stayed **UNVERIFIED** and is superseded by the two measured densities
(Bennu 1190, Didymos 2400 kg/m³). None of the sources trace to HFGW/Baker literature
(epistemic firewall checked).

**Purpose:** the planned Nature-paper section explores the tradespace among
(a) detection distance, (b) closure velocity, (c) object mass, and (d) required
gravity-spike strength to move an Earth-impacting trajectory to a miss, within the
lead time detection allows. This file records what the planetary-defense literature
assumes for (b) and (c), and what it already knows about (d) as a function of time.

---

## 1. Velocity assumptions in the literature

| Quantity | Value | Source | Status |
|---|---|---|---|
| Mean Earth-impact speed, NEA population | **~20.6 km/s** | Greenstreet NEO orbital model (Greenstreet, Ngo & Gladman 2012, *Icarus* 217:355), as used in impact-speed distributions | NEEDS-VERIFY (exact figure/table) |
| Mode of impact-speed distribution | **~15 km/s**, sharp peak | same | NEEDS-VERIFY |
| Tail of distribution | out to **~45 km/s** (asteroids) | same | NEEDS-VERIFY |
| Floor (any impactor) | **11.2 km/s** — Earth escape speed; gravitational focusing forbids slower impacts | elementary; state without citation or cite a textbook | OK |
| Ceiling (long-period comets) | **~72 km/s** — retrograde parabolic at 1 AU | standard celestial mechanics; comet-threat discussion in *Acta Astronautica* 2018 ("Defending the earth from long-period comets and sneaky asteroids") | NEEDS-VERIFY |
| Observed small-impactor distribution | consistent with ECSS sporadic-meteoroid standard; debiased via large fireballs | Drolshagen et al. 2020, *Planet. Space Sci.* 184:104869, arXiv:2011.07775 | VERIFIED (abstract level) |
| Debiased NEO orbit/size model (modern successor) | Granvik et al. 2018, *Icarus* 312:181 (open reprint); NEOMOD, arXiv:2306.09521 | — | available if reviewers want the newer model |

**Planning value used across the field: 20 km/s.** Chelyabinsk entered at 19 km/s —
the round number is empirically honest.

## 2. Mass / size assumptions in the literature

Survey policy and population (sets which masses are *plausible* threats):

- **140 m** is the statutory survey threshold (George E. Brown Act: find 90% of NEAs
  > 140 m). The 2017 NEO Science Definition Team report (Stokes et al. 2017, CNEOS,
  `https://cneos.jpl.nasa.gov/doc/2017_neo_sdt_final_e-version.pdf`) estimates
  **~25,000 NEAs > 140 m**, completeness ~30% at the time; ~1,000 NEAs > 1 km with
  ~95% found. Standard density assumption in that report is **2.6 g/cm³** (stony).
  PDF exceeds fetch limit — NEEDS-VERIFY against the report's own tables for the
  exact density/velocity assumptions before quoting.
- Size–frequency is a steep power law: each factor-of-10 in diameter is roughly a
  factor-of-1000 in mass and a large drop in frequency (impact interval: ~60 yr for
  20 m, ~10⁴ yr for 140 m-class regional events, ~5×10⁵ yr for 1 km, ~10⁸ yr for 10 km).

Mass anchors (measured or well-constrained real objects — use these as the mass axis
tick marks in the tradespace figure):

| Object | Diameter | Mass | Velocity note | Source | Status |
|---|---|---|---|---|---|
| Chelyabinsk (2013) | ~20 m | **~1.2×10⁷ kg** | 19 km/s entry; ~500 kt; **zero warning** (approached from sunward sky) | Brown et al. 2013, *Nature* 503:238; Popova et al. 2013, *Science* 342:1069 | NEEDS-VERIFY (exact mass) |
| 2008 TC3 | ~4 m | ~8×10⁴ kg | discovered **19 h** before impact | Jenniskens et al. 2009, *Nature* 458:485 | NEEDS-VERIFY |
| 2019 OK | ~60–130 m | ~10⁹–10¹⁰ kg | 0.19 lunar distances miss, **~1 day** warning | widely reported; find archival citation | NEEDS-VERIFY |
| Dimorphos | 151 m | **~4.3×10⁹ kg** (inferred) | DART target | Daly et al. 2023 / Nature Astronomy 2024 physical-properties paper | NEEDS-VERIFY |
| Bennu | 490 m | **7.33×10¹⁰ kg** (measured) | ρ = 1.19 g/cm³ — **rubble pile**; directly relevant to our Kelvin-sphere k₂ wall (INDEX assumption ledger) | Lauretta et al., OSIRIS-REx results | NEEDS-VERIFY |
| Generic 1 km @ 2.6 g/cm³ | 1 km | 1.4×10¹² kg | global-consequence threshold (NRC 2010) | arithmetic | OK |
| Chicxulub-class | ~10 km | ~1.4×10¹⁵ kg | extinction-class | arithmetic + literature | OK |

So the tradespace mass axis spans **~10⁷ to ~10¹⁵ kg** (20 m to 10 km), with the
policy-relevant center at **~10⁹–10¹² kg** (140 m – 1 km).

## 3. Required deflection vs. lead time — what is already established

- **Ahrens & Harris 1992, *Nature* 360:429** (doi:10.1038/360429a0) — the founding
  result: required Δv scales as **1/t** with time-before-impact; order **1 cm/s if
  applied decades ahead**. Our `target/deflection.py:miss_distance` implements this
  impulsive along-track logic (citation already in module).
- **NRC 2010, *Defending Planet Earth*** (nationalacademies.org/read/12842) —
  benchmark: **1 cm/s displaces the arrival point ~15,000 km in 10 years**
  (NEEDS-VERIFY: quote wording vs. the report's own Table 5.x; our own formula
  gives the same order with the ~3× along-track orbital amplification). Method
  matrix by size and warning: gravity tractor ≲ 100 m with decades; kinetic
  impactor up to ~1 km with decades; nuclear standoff for > 1 km or short warning
  (2.4 cm/s on km-scale bodies at ~100 kt).
- **Greenstreet et al. 2020, *Icarus* 347:113792** — 10,000 virtual impactors from
  the debiased population, deflection applied 10–50 yr out, target miss ~4,000 mi.
  Median Δv ∝ 1/t confirmed statistically; **spread is ×10 either way** at fixed t
  (intervening planetary close approaches create low-Δv "keyholes"). This is the
  closest existing analogue of our tradespace: it covers the (mass-free Δv × lead
  time) plane. **Our section's novelty is adding the detection-distance/closure-
  velocity axes and converting Δv to required spike strength through the tidal
  coupling channel.**
- **DART, achieved state of the art:** Δv = **2.70 ± 0.10 mm/s** on Dimorphos
  (~4.3×10⁹ kg), momentum enhancement β ≈ 2.2–4.9 (Cheng et al. 2023, *Nature*
  616:457; Thomas et al. 2023, *Nature* 616:448 for the 33-min period change).
  Achieved impulse ≈ 10⁷ kg·m/s from one ~580 kg impactor at 6 km/s.

## 4. Warning time — the axis the deflection literature quietly assumes away

The Δv ∝ 1/t results above are usually quoted at t = decades. The discovery
literature says decades of warning is the *exception*:

- **Cheng, Scolnic, Kurlander, Chow & Fernandes 2026** (arXiv:2601.16255), LSST
  simulated impactor discovery: fraction of impactors discovered before impact and
  **median warning time by size** —
  - 10–20 m: 10.5% discovered, median warning **12.4 days**
  - 20–50 m: 26.8%, median **21.5 days**
  - 50–140 m: 50.3%, median **~106 days**
  - \>140 m: 79.7% discovered, but **only 39% get more than one year**
- Real events agree: Chelyabinsk (20 m) — zero warning; 2008 TC3 — 19 h;
  2019 OK (~100 m) — ~1 day.
- Long-period comets: months-to-a-year of warning at best, at 50–72 km/s closure
  (*Acta Astronautica* 2018 above).

**Consequence for the tradespace:** for everything except the pre-catalogued large
population, lead time is set by *detection distance and closure velocity*, not by
survey completeness statistics. That is precisely our tradespace's front axis:

> t = d / v_c (first order). At 20 km/s closure: detection at 1 AU → **87 days**;
> at 5 AU → **1.2 yr**; at 40 AU (our `TARGET_RANGE`) → **9.5 yr**.

A detection system that works at 40 AU converts a Chelyabinsk-class "zero warning"
into a decade — which is the regime where the 1/t law makes cm/s-class deflection
meaningful at all. Conversely at 1 AU detection, required Δv is ~40× the decades
value, and slow-push methods are excluded by the literature's own method matrix.

## 5. Mapping onto the framework (for the section design, not yet tasked)

- Lead time: t = d/v_c over the grid d ∈ [0.05, 40] AU, v_c ∈ [11.2, 72] km/s.
- Required Δv(t): use `target/deflection.py:miss_distance` inverted for one Earth
  radius + gravitational-focusing cross-section; cross-check the median curve of
  Greenstreet et al. 2020.
- Required impulse: m·Δv over m ∈ [10⁷, 10¹⁵] kg.
- Required spike strength: convert impulse to the tidal-coupling channel via
  `target/coupling.py` — remembering the R6/geodesic finding that a GW delivers
  **tidal strain, not net force**, so the honest output is the required strain/
  gradient at the target, compared against the R5 ledger's achievable values. The
  existing R6 single-point "Required = 43 N" generalizes into this surface.
- Expect the section to be a *walls* result (rule 5: never delete a wall): the
  ledger gap will vary across the tradespace but almost certainly stays a gap;
  the interesting output is **where in (d, v_c, m) the gap is smallest**, and the
  detection-distance→lead-time conversion above, which is genuinely new relative
  to Greenstreet et al.'s fixed-epoch treatment.

## Sources (retrieval trail)

- https://www.nature.com/articles/360429a0 (Ahrens & Harris 1992)
- https://www.nationalacademies.org/read/12842/chapter/7 (NRC 2010, mitigation ch.)
- https://www.sciencedirect.com/science/article/abs/pii/S0019103520301755 (Greenstreet et al. 2020)
- https://b612foundation.org/the-effect-of-warning-time-on-the-deflection-of-earth-impacting-asteroids/
- https://arxiv.org/abs/2601.16255 (Cheng et al. 2026, LSST impactor warning times)
- https://arxiv.org/abs/2011.07775 (Drolshagen et al. 2020, observed impact-velocity distribution)
- https://cneos.jpl.nasa.gov/doc/2017_neo_sdt_final_e-version.pdf (SDT 2017 — too large to fetch this session; verify locally)
- https://www2.boulder.swri.edu/~bottke/Reprints/Granvik_2018_Icarus_312_181_Debiased_Orbit_Mag_NEO.pdf (Granvik et al. 2018)
- https://www.nature.com/articles/s41586-023-05878-z (Cheng et al. 2023, DART momentum)
- https://phys.org/news/2013-11-results-russian-chelyabinsk-meteor-published.html (Chelyabinsk secondary)
