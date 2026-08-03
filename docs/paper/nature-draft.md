# Provenance-enforced simulation of engineered gravitational radiation: a spin-2 phased-array framework with a quantified feasibility ledger

**DRAFT — not for circulation.** Target format: *Nature* Article (Main ≤ 3,000 words;
Methods unlimited; ≤ 50 references; ≤ 6 display items in the main text; Extended Data
≤ 10 items). Section headings follow *Nature*'s Article template.

> **Reading note.** Every paragraph of content in this draft is followed by a
> ***Non-expert summary*** — a plain-language restatement of what that paragraph says,
> written for a reader with no physics training. These are **drafting aids, not part of
> the manuscript**, and must be stripped before submission. They exist so that a
> non-specialist author, collaborator, or reviewer can follow the argument end to end and
> challenge it. If a summary and its paragraph disagree, the paragraph is what the
> manuscript claims — but the disagreement is a bug worth chasing, because it usually
> means the paragraph is unclear rather than that the summary is wrong.

> **Status of this draft.** The Main, Discussion and Methods are written. **The Results
> section is a pre-registered stub** (§Results below): every subsection states the
> quantity to be reported, the run that produces it, the tolerance that would falsify
> it, and the display item it lands in — but no numbers from campaign runs are entered
> yet. Numbers that appear anywhere in this draft are **already-committed test and
> benchmark outputs** from the repository, not campaign results, and each is traceable
> to a named test. See §"Numbers in this draft" for the distinction and the audit rule.

***Non-expert summary:*** This paper is half-written on purpose. The parts explaining
*what we built* and *how it works* are done. The part reporting *what we found when we
ran it* is deliberately left as an empty, pre-filled-in outline — we wrote down what
we're going to measure and what result would prove us wrong **before** running anything,
so we can't quietly move the goalposts later. Any number you see in this draft today
comes from a test that already runs, not from a result we're hoping for.

---

## Author list

*Placeholder — to be completed before submission.*

Author 1<sup>1</sup>, …

<sup>1</sup>Affiliation.

Correspondence: dpaulday@protonmail.com

*Note for the author list:* the repository's contributor model is a long-horizon
("cathedral") one in which authorship will accrue across cohorts. A CRediT-style
contribution table plus a machine-readable `CITATION.cff` should be added to the
repository before submission so that the author list and the code's own provenance
record cannot drift apart. This is currently **not** in place and is a submission
blocker, not an editorial nicety.

***Non-expert summary:*** We haven't finished the author list. This project is designed
to outlive the people who started it, so contributors will keep joining for years, and we
need a formal, machine-readable record of who did what — kept in the code itself, so it
can't drift out of sync with the paper. That file doesn't exist yet, and we're calling
that a genuine blocker rather than paperwork, because a paper whose whole argument is
"track where everything came from" would look ridiculous if it couldn't track its own
authors.

---

## Abstract

*(target 150–200 words; current draft ≈ 195)*

Gravitational radiation is a spin-2 field, and the phased-array formalism that governs
coherent electromagnetic apertures does not carry over to it unchanged. We present
`gwtb`, an open-source framework that models the generation, propagation, coherent
superposition and target coupling of gravitational radiation from arrays of
controllably accelerated masses, together with the first systematic derivation of
array-theoretic quantities — element mismatch, array gain, alignment tolerance,
focusing phase — for a spin-2 rather than a spin-1 field. Polarization rotates as
e^(2iψ), so the element-to-element mismatch factor is cos(2Δψ) rather than cos(Δψ);
elements 90° apart cancel completely where electromagnetic intuition predicts a
doubling of power, and the orientation tolerance for 1% gain loss is exactly twice as
tight. Because such results have no external reference implementation to check against,
the framework's second contribution is architectural: every implemented equation carries
a machine-checked citation to a numbered equation in an open-access source, every claim
is registered as established, derived or conjectural, every approximation is recorded
with the regime in which it fails, and results computed from momentum-non-conserving
sources are cryptographically inseparable from an `UNPHYSICAL` provenance stamp.

**Keywords:** gravitational waves; linearized gravity; phased arrays; spin-2 fields;
research software engineering; computational reproducibility; planetary defence.

***Non-expert summary:*** Radio engineers know how to combine many antennas so their
signals reinforce each other in one direction — that's a "phased array," the technology
behind radar and 5G. We asked whether the same trick works for gravitational waves
(ripples in space itself). The answer is **yes, but the rules are different**, because
gravity's waves have a different symmetry from radio waves. Concretely: two gravitational
emitters turned 90° apart from each other **cancel out to nothing**, whereas two radio
antennas in the same arrangement would give you double the power. Get that wrong and your
array radiates silence while you confidently expect twice the output. Since nobody has
built one of these, there's no existing software to check our answers against — so the
paper's second half is about making the code itself auditable: every formula must cite a
specific numbered equation in a paper anyone can open, and any result computed from a
physically impossible setup gets permanently branded as such, in a way the software will
not let you remove.

---

## Main

The detection of gravitational waves<sup>1</sup> established that spacetime strain
propagates, superposes and can be measured. It did not establish that gravitational
radiation can be *engineered* — deliberately generated, phased, steered and delivered.
That question is treated seriously in only a small and uneven literature, and it is
adjacent to a body of work on "high-frequency gravitational waves" that a JASON review
commissioned by the U.S. Office of the Director of National Intelligence found to be
fundamentally in error<sup>2</sup>. The credible prior art on deliberately generated
gravitational radiation is narrow — the electromagnetic-cavity emission analysis of
Grishchuk and Sazhin<sup>3</sup> is its canonical entry.

***Non-expert summary:*** In 2015 scientists finally *detected* gravitational waves
arriving from colliding black holes, which proved these ripples are real and behave as
predicted. That is very different from being able to *make* them on purpose and aim them
somewhere. Almost nobody has studied the "make them" question seriously — and the people
who claimed to have solved it were investigated by a US government scientific review panel
and found to be plainly wrong. So this is a field with a small amount of good work and a
notable amount of discredited work, which shapes everything that follows.

This history creates an unusual methodological requirement. A framework in this problem
domain that reports a favourable number is, on its face, indistinguishable from the
discredited literature. The distinguishing property cannot be the result; it must be the
*apparatus that produced the result* — specifically, whether that apparatus is capable
of stating its own distance from the claim it is adjacent to, and whether it can be
audited by a reader who does not trust its authors.

***Non-expert summary:*** Here's the awkward problem. If our software spits out an
encouraging number, that alone looks *exactly* like the discredited work — encouraging
numbers are what those people produced too. So a good result cannot be what makes us
credible. The only thing that can is the machinery: can the tool honestly report how far
short it falls, and can a total stranger who assumes we're either fooling ourselves or
lying check every step? We designed for a hostile reader, not a friendly one.

We therefore built `gwtb` to two specifications simultaneously. As physics, it is a
linearized-gravity source-and-propagation code: retarded multipole expansion,
transverse-traceless projection, coherent superposition across an array of sources,
and explicit coupling channels at the target. As software, it is an *auditable* object:
citation discipline is enforced in continuous integration, claims are separated into
established physics, our derivations and open conjecture, approximations are catalogued
with their breakdown regimes, and a quantitative feasibility ledger is emitted on every
run stating how far the modelled configuration sits from the application it is motivated
by.

***Non-expert summary:*** So the software has two jobs at once. Job one is ordinary
physics: work out what gravitational waves a set of moving masses produces, how those
waves travel, how they combine, and what they do on arrival. Job two is bookkeeping with
teeth: the code refuses to build unless every formula cites its source; claims are sorted
into "textbook fact," "our own reasoning," and "guess"; every simplifying assumption is
written down *along with the conditions under which it stops being true*; and every single
run prints a scorecard of how far the design is from actually working.

### The physics gap that motivates the architecture

Three properties of the problem drive nearly every design decision.

***Non-expert summary:*** Three facts about this particular physics problem dictated
almost every choice we made in building the software. They're covered one at a time below.

**The regime is deeply linear.** Strains in any configuration this framework models are
of order h ~ 10⁻⁴⁰ — forty orders of magnitude inside the perturbative regime. Numerical
relativity, the standard tool for gravitational-wave source modelling, exists to handle
the strong-field region near merging compact objects and is the wrong instrument here:
it would solve a nonlinear partial differential equation to recover, at great cost, what
a linear integral gives exactly, on grids sized in geometric units of the source mass
rather than the 6 × 10¹² m of the engagement geometry. More importantly, linearity is
not a simplification we accept reluctantly. **Superposition holds exactly in the linear
regime, and without exact superposition the phrase "phased array of gravitational-wave
sources" has no referent.** The choice of formalism is what makes the concept coherent
enough to model at all.

***Non-expert summary:*** The effects here are unimaginably tiny — a number with forty
zeros after the decimal point. That's actually good news, twice over. First, it means we
can skip the monstrously expensive supercomputer methods built for violent events like
black-hole collisions; those tools are designed for a regime we never come close to
entering, and using them here would be like running a crash simulation to work out how
much a feather bends. Second, and more importantly, when effects are this small they
simply **add together**, cleanly and exactly. That matters enormously, because "combine
many sources so they reinforce each other" only means anything if the sources add. The
whole idea depends on being in this gentle regime.

**The leading radiation is quadrupolar, and this is a constraint on the concept, not a
detail of the implementation.** Expanding the retarded integral in multipoles, the mass
monopole is conserved and does not radiate; the mass dipole's second derivative is the
net external force, which vanishes for an isolated system; the mass quadrupole is the
first non-vanishing term<sup>4</sup>. It is tempting, when modelling a mass that is
"made to accelerate", to leave the accelerating agent out of the model. Doing so
silently breaks momentum conservation and promotes a mass-dipole term that is roughly
**10¹⁰ times** the true quadrupole signal. That artifact does not present as a bug. It
presents as a breakthrough. Guarding against it is the single most load-bearing
requirement on the software (Methods, "Conservation auditing").

***Non-expert summary:*** There's a hierarchy of ways an object can radiate gravity, and
nature switches off the two easiest ones. Simply *having* mass radiates nothing. Simply
*moving* radiates nothing either, as long as nothing outside your system is pushing. Only
the third-simplest motion — squeezing and stretching a shape — actually emits. **This is
where you can fool yourself catastrophically.** If you model a mass being shoved but
"forget" to include whatever is doing the shoving, the equations quietly hand you the
switched-off second option, and it's about **ten billion times bigger** than the real
signal. It doesn't look like a bug. It looks like you've discovered something
extraordinary. Preventing that specific self-deception is the single most important thing
this software does.

**The array formalism must be re-derived, not ported.** Under a rotation ψ about the
propagation direction, gravitational-wave polarization transforms as e^(2iψ), not
e^(iψ); h₊ and h× are separated by 45°, not 90°; and superposition acts on the
TT-projected tensor h_ij, never on scalar amplitudes. Every open-source array-synthesis
library implements the spin-1 case. Code adapted from antenna, radar or acoustics
references will run, produce plausible numbers, and be wrong. We treated this as the
project's highest-risk failure class and attacked it with a dedicated design spike four
development sprints before anything depended on its output.

***Non-expert summary:*** You cannot just download existing antenna software and point it
at gravity. Light and radio waves "twist" one way as you rotate them; gravitational waves
twist **twice as fast**. Every off-the-shelf array tool in existence is built for the
first case. Borrow one and your code runs happily, produces sensible-looking numbers, and
is silently wrong — the worst possible failure, because nothing complains. We flagged this
as the project's biggest danger and deliberately tackled it *months* before anything else
depended on the answer, so that a mistake would surface early instead of poisoning
everything built on top of it.

### What the framework computes

`gwtb` is organized as nine layers with a strict dependency order (Fig. 1). `core`
supplies constants, validated array contracts, a scaled strain representation and the
numerical backends. `bodies` builds mass distributions and their multipole moments,
including the three mechanisms by which a sphere's radius and density cease to be
degenerate with its total mass. `kinematics` synthesizes finite (non-impulsive)
acceleration profiles and multi-tone drives. `source` converts those into radiation —
quadrupole strain, luminosity, linear memory, and a deliberately flagged dipole path.
`propagate` handles retarded evaluation, TT projection and spin-2 polarization. `array`
performs geometry, grating-lobe analysis, tensor superposition and focusing. `target`
evaluates geodesic deviation and three competing coupling channels side by side.
`ledger` emits the feasibility report. `viz` renders fields and beam patterns.

***Non-expert summary:*** The software is built as nine stacked layers, each depending
only on the ones below it, like floors of a building. From the bottom up: basic constants
and safety checks; descriptions of the physical objects (spheres, and what happens when
they squash or spin); the motions those objects perform; the gravitational waves those
motions emit; how the waves travel outward; how many emitters combine into a steered
beam; what happens when the beam arrives at the asteroid; the honest scorecard of how far
short we fall; and finally the pictures.

Two of these layers exist because of a physical fact rather than a software convenience.
`ledger` exists because a framework that cannot state its own gap is
epistemically indistinguishable from the literature described above. And the
`UNPHYSICAL` stamping machinery inside `source` exists because the ~10¹⁰ dipole artifact
must be *unable* to reach a headline result, not merely discouraged from doing so.

***Non-expert summary:*** Two of those nine layers aren't there for engineering reasons —
they're there for honesty reasons. The scorecard exists because a tool that can't say how
badly it's failing is indistinguishable from the discredited work. And the branding
machinery exists because "please remember not to misuse this number" is not good enough
when the number is ten billion times too big and looks like a Nobel Prize. It has to be
*impossible*, not merely discouraged.

### The spin-2 extension of array theory

For an array of N elements observed along n̂, the total strain is the sum of TT-projected
element tensors,

  h_ij^TT(n̂) = Σ_n Λ_ij,kl(n̂) · h_kl^(n) · e^(iφ_n),

which after projection lives in the two-dimensional polarization space spanned by e⁺ and
e^×. The sum is a vector sum in that space. Writing h ≡ h₊ − i h×, a rotation by ψ acts
as h → h e^(2iψ), and the consequences depart sharply from the electromagnetic case
(Table 1):

- The element-to-element mismatch factor is **cos(2Δψ)**. It is maximal at Δψ = 45°, not
  90°, and has period 180°.
- Two co-phased elements 90° apart **cancel completely**. Spin-1 reasoning predicts they
  are polarization-orthogonal and their powers add. An array laid out on
  electromagnetic reasoning with orthogonally-oriented elements radiates *nothing* along
  the intended axis, and its designer has every reason to expect twice the
  single-element power. Physically this is not exotic — an x-oriented oscillator
  stretches along x and squeezes along y while a y-oriented one does the reverse — but
  it is invisible by analogy from antenna theory.
- Array gain is N² **only** for co-oriented elements: gain = |Σ_n A_n e^(2iψ_n)|² / A².
- For orientations jittered with standard deviation σ about a common axis, the gain
  fraction is **exp(−4σ²)**, verified against 400 realizations at N = 100 and N = 1000
  to ~10⁻⁴ across σ ∈ [0°, 20°]. **A 1% power loss requires co-orientation to
  σ ≤ 2.87°, exactly twice as tight as the spin-1 equivalent.** This is a constraint on
  any physical array, not a modelling detail.

***Non-expert summary:*** This is the paper's central physics result, and it's the part a
radio engineer would get wrong. When you combine gravitational emitters, how much they
help each other depends on their relative rotation — but on **twice** the angle, compared
to radio. Four consequences. (1) The worst misalignment is at 45°, not 90°. (2) At exactly
90° the emitters don't just fail to help, they **actively erase each other**, giving you
literally zero — while radio intuition promises double. (3) You only get the full
multiplied-up power if every emitter is turned the same way. (4) Real hardware is never
perfectly aligned, and we can say exactly how much sloppiness costs: to lose no more than
1% of your power, every emitter must be aligned to within **2.87 degrees** — precisely
twice as strict as the radio equivalent. That last number is a hard engineering
requirement for anyone who ever tries to build one of these.

The two-element prototype that established these results reproduced the analytic TT form
to 10⁻¹⁴ across nine orientation angles and confirmed that the period in ψ is 180°, not
360°. The scalar array factor is retained in the codebase as an explicitly labelled
spin-1 baseline that the tensor superposition must reduce to for co-oriented elements —
a regression check that proves the extension is a controlled departure rather than a
rewrite.

***Non-expert summary:*** We checked this with a stripped-down two-emitter test case,
which matched the hand-derived algebra to fourteen decimal places at nine different
angles. We also deliberately **kept** the old radio-style calculation in the codebase,
clearly labelled as such, and require the new gravity version to agree with it in the one
situation where both should give the same answer. That's the proof that we extended the
old theory carefully rather than just replacing it with something new and unchecked.

### Provenance as an architectural feature

The framework's second contribution is that its epistemic status is *machine-readable*.
Five mechanisms, described in full in Methods:

1. **Citation discipline in CI.** Every public function in the physics packages must
   carry a docstring line of the form `Source: <reference>, eq. <number>`. A build
   fails without it. "Blanchet ch. 3" is rejected; "Blanchet eq. 3" is accepted. The
   check verifies that a citation is *present and specific*; correctness remains a human
   review gate. Sources are required to be openly accessible wherever possible, on the
   explicit ground that a citation a reader cannot open is not a citation.
2. **A claims registry** separating established physics (11 entries), our derived
   extensions (7) and open conjecture (4). Promotion from conjecture to derivation
   requires a written derivation plus a limiting case reducing to established physics;
   promotion from derivation to established requires independent publication, which we
   do not grant ourselves. **Demotions are recorded with a date and reason, never
   deleted.**
3. **An assumption ledger** — 30 rows at the time of writing — each naming an
   approximation, where it is asserted in code, the regime in which it holds, and the
   regime in which it *fails*. Several of this framework's interesting configurations
   live near those edges.
4. **An errata file** for verified errors in the primary literature. Two typographical
   errors in the worked binary example of a standard review<sup>5</sup> were established
   numerically — one of which yields a non-symmetric quadrupole tensor, which is
   impossible by construction. Without this record, a future reader checking our code
   against the paper would conclude that *we* have the bug and "fix" correct code to
   match a typo.
5. **Inseparable unphysicality stamping.** Results computed from a
   momentum-non-conserving source carry a stamp that ordinary numerical use cannot
   remove; attempts to coerce a stamped result into a bare array raise rather than
   silently converting (Methods, "Conservation auditing").

***Non-expert summary:*** Five safeguards, all automated rather than left to good
intentions. **(1)** Every physics formula must name the exact numbered equation it came
from, in a paper anyone can open for free — "see chapter 3" is rejected, "see equation 3"
is accepted — and the code literally will not build otherwise. **(2)** Every claim is
filed as "established fact," "our own reasoning," or "unproven guess," and we are not
allowed to promote our own work into the "established" pile; only outside publication can
do that. Downgrades are recorded permanently, never quietly deleted. **(3)** Every
simplification is listed together with the conditions under which it breaks — and
awkwardly, the configurations we most want to explore sit near those breaking points.
**(4)** We keep a list of mistakes we found in *published papers*, so a future reader
doesn't "correct" our working code to match somebody's typo. **(5)** Numbers from
physically impossible setups are branded, and the software refuses to hand them over
unbranded.

Fig. 2 shows how these five mechanisms interlock. Each was added in response to a
specific realized or near-miss failure, which we document rather than smooth over
(Discussion).

***Non-expert summary:*** None of those five safeguards was dreamed up in advance out of
tidiness. Each one exists because something actually went wrong, or very nearly did, and
we chose to write up the near-miss rather than quietly patch it and look competent.

---

## Results

> ### ⚠ STUB — pre-registered structure, no campaign numbers entered
>
> This section is deliberately written **before** the parameter-space campaign is run,
> in the pre-registration style, so that the analysis plan cannot be adjusted after
> seeing the outcome. Each subsection below states:
>
> - **Q** — the question,
> - **Run** — the exact entry point and configuration that answers it,
> - **Report** — the quantity and display item,
> - **Falsifier** — the outcome that would contradict the framework's stated claim, and
> - **Status** — `AWAITING RUN`.
>
> **Filling rule.** A subsection may only be completed from a committed run whose
> manifest hash appears in the Source Data. Any number entered here must be
> reproducible by `pytest` or by a committed script in `scratchpad/`. Prose may not be
> written before the number it describes.

***Non-expert summary:*** This whole section is an empty form, filled in ahead of time on
purpose. For each experiment we've written down the question, exactly which command
answers it, what we'll report, and — crucially — **what outcome would prove us wrong**,
all before running anything. This is a technique borrowed from medical trials to stop
researchers unconsciously reshaping their analysis once they've seen the data. The rule
we've imposed on ourselves: no sentence may be written until the number it describes
exists and can be regenerated from scratch by anyone.

### R1 — Validation against known systems

**Q.** Does the implementation reproduce results the community already agrees on, at
the precision claimed?

**Run.** `pytest tests/benchmarks/` (full suite).

**Report.** Extended Data Table 1: benchmark, quantity, reference value, computed value,
relative deviation, governing equation ID.

**Falsifier.** Any benchmark whose deviation exceeds its committed tolerance.

**Status.** `PARTIALLY AVAILABLE` — the benchmark suite is green in the repository and
its current values are given in Extended Data Table 1 as committed test outputs. This
subsection needs only the narrative pass and the final re-run under the submission tag.
The load-bearing entries are: the circular-binary strain and luminosity at rtol 10⁻⁶;
the luminosity built from the analytic third derivative reproducing the independent
closed form L = (32/5)(G/c⁵)μ²a⁴ω⁶ to **4.1 × 10⁻¹⁶**; the PSR B1913+16 orbital decay
rate reproduced to **0.21%** (−2.4031 × 10⁻¹² computed against −2.398 × 10⁻¹²
observed<sup>6,7</sup>); and the dipole-cancellation benchmark, in which the dipole
term vanishes to < 10⁻¹² relative across 20 seeded momentum-conserving configurations
while a deliberate positive control exceeds 10⁻³.

***Non-expert summary:*** Before trusting the software on anything new, we make it
reproduce things already known to be true. The headline check involves a real pair of
stars — a binary pulsar discovered in 1974, whose orbit is measurably shrinking as it
radiates gravitational waves. That measurement won a Nobel Prize. Our code predicts the
shrinkage rate to within **0.21%** of the observed value. We also verify the "switched-off
second option" from earlier really does switch off: in properly modelled setups it
vanishes to a trillionth, while a deliberately broken setup we included as a control
shows it blazing away. That second half matters — a test that only ever passes isn't
testing anything.

### R2 — The spin-2 array laws, measured rather than derived

**Q.** Do the cos(2Δψ) mismatch law, the N²-only-for-co-oriented gain law, and the
exp(−4σ²) alignment tolerance hold across the array configurations of interest, or only
in the two-element case in which they were derived?

**Run.** Orientation sweep over Δψ ∈ [0°, 180°] at N ∈ {2, 16, 64, 100, 1000}; jitter
study at σ ∈ [0°, 20°], ≥ 400 realizations per point, seeded.

**Report.** Fig. 3 (measured gain vs. 2 + 2cos(2Δψ), with the spin-1 prediction
overplotted); Fig. 4 (gain fraction vs. σ against exp(−4σ²) and exp(−σ²)).

**Falsifier.** Departure from cos(2Δψ) beyond the committed tolerance at any Δψ; or the
90° cancellation failing to be complete; or the measured tolerance curve agreeing better
with exp(−σ²) than exp(−4σ²).

**Status.** `AWAITING RUN`. The two-element case is already committed (Table 1) and
agrees exactly; the N-element generalization is the new content.

***Non-expert summary:*** We proved the new rotation rules using just two emitters. Do
they still hold with sixteen, a hundred, a thousand? That's this experiment. We've stated
in advance exactly what would prove us wrong: if the 90° pair fails to cancel completely,
or if the alignment-tolerance curve turns out to match the ordinary radio formula better
than our gravitational one, then our central claim is broken and we say so.

### R3 — Body-parameter sensitivity and the degeneracy-breaking mechanisms

**Q.** Under what conditions do a body's radius and density stop being degenerate with
its total mass, and by how much?

**Run.** Fixed-mass sweeps over radius across ≥ 2 orders of magnitude, for the rigid,
elastic (Love-number) and finite-size-retardation models; materials spanning
steel/tungsten/osmium rigidities.

**Report.** Fig. 5: radiated quadrupole amplitude vs. radius at fixed mass, one trace
per model. Extended Data Table 2: measured degeneracy-breaking factor per mechanism.

**Falsifier.** Any radius dependence appearing in the *rigid* model — the rigid model's
radiated amplitude must sit at the numerical floor, and a leaked R-dependent term as
small as 10⁻¹⁴ is designed to trip the floor check.

**Status.** `AWAITING RUN` for the campaign sweep; the committed unit-scale study
already shows rigid-model radiation at a measured floor of 10⁻¹⁵ against elastic-model
variation of ~7.6 × 10⁴ – 1.0 × 10⁵ ×, which the campaign should extend rather than
merely repeat.

***Non-expert summary:*** If you're building emitters, you'd like to know whether it
matters that your masses are big and light versus small and dense. For a perfectly rigid
ball the surprising answer is **no** — only the total weight matters, and size and density
cancel out entirely. But real objects aren't perfectly rigid: they flex. Once you allow
flexing, size and density matter enormously — we measure a difference of up to about
100,000× across steel, tungsten and osmium. This experiment maps that out, and includes a
trap for ourselves: if the *rigid* model ever shows any size dependence at all, even at
the fourteenth decimal place, something has leaked and the code is wrong.

### R4 — Spatiotemporal focusing with incommensurate drive frequencies

**Q.** Does driving array elements at mutually incommensurate (prime-valued) frequencies
produce the mode-locking signature — peak amplitude N·A at the focus against a random-
phase background — and does the peak-to-background ratio scale as √N?

**Run.** `focused_field` at f ≥ 10⁵ Hz for the reference aperture, N ∈ {16, 64, 100};
background estimated over randomized phase realizations.

**Report.** Fig. 6: focal-plane amplitude map and the peak-to-background ratio vs. √N.

**Falsifier.** Ratio not scaling as √N; or the peak failing to reach N·A at broadside to
rtol 10⁻⁶.

**Status.** `AWAITING RUN`. **Four traps must be honoured in the analysis and stated in
the caption**, each of which produces a test that passes while asserting nothing:
(i) at the project's nominal 1 kHz drive the 12.4 km reference aperture spans D/λ = 0.041
— it is a point source, not an array, and *every* weighting including uniform w = 1
returns exactly N, so any measurement at that frequency is vacuous; (ii) the sign
convention exp(+iφ) is undetermined within a few beamwidths of broadside and must be
pinned tens of beamwidths off-axis; (iii) peak gain is N only near broadside, falling to
≈ 45 at 50 beamwidths for N = 64; (iv) the random-phase background mean is the Rayleigh
value √(Nπ)/2 ≈ 0.886√N, **not** √N, so an implementer chasing the 12% discrepancy would
be chasing correct behaviour.

***Non-expert summary:*** A trick borrowed from lasers: if you drive many emitters at
frequencies that never quite line up with one another (using prime numbers, so their
rhythms take an extremely long time to repeat), all the waves coincide at exactly **one
point in space and time** and nowhere else — a brief, sharp spike instead of a spread-out
beam. This experiment tests whether that works here. The important part is the four
warnings: each describes a way of running this test that would *appear* to succeed while
actually measuring nothing. The nastiest is the first — at the frequency we'd naturally
pick, our array is smaller than a single wavelength, which makes it behave like one single
emitter rather than an array. In that situation the test passes perfectly even if you
delete the entire focusing calculation. We found these by measuring, and we're publishing
them because they're the traps most likely to catch the next person.

### R5 — The walls, quantified

**Q.** What is the actual magnitude of each barrier separating this concept from a
delivered deflection, and in what order must they be attacked?

**Run.** Full feasibility-ledger emission across the scoping configuration set, with
run manifests.

**Report.** Table 2 (main text): each wall as a ledger row — achieved, required, units,
gap in decades, source module, provenance. Fig. 7: gap in decades per wall, sorted.

**Falsifier.** **Any wall that disappears.** Under this project's rules a wall is a
finding, not a bug; if a code change makes one vanish, the change is presumed defective
until proven otherwise, and the burden of proof is on the change.

**Status.** `AWAITING RUN`. The three walls to be reported are diffraction (a 1 km spot
at 40 AU requires an aperture of ~6 × 10⁹ wavelengths **at any frequency** — raising
frequency does not relax the ratio, it shrinks the physical size that ratio corresponds
to, from ~1.2 × 10⁷ AU at 1 Hz to ~12 AU at 1 MHz); coupling (a gravitational wave
produces tidal strain, not net force, and momentum transfer requires absorption against
a negligible cross-section); and magnitude (radiated power scales as ω⁶, making
frequency the dominant lever by ~10³⁶ between 1 Hz and 1 MHz operation, against a
requirement of ~1.4 × 10¹⁰ N·s to impart 0.01 m s⁻¹ to a 1 km asteroid — for scale, the
DART impactor delivered ~1.2 × 10⁷ N·s<sup>8</sup>).

***Non-expert summary:*** This is the section that says how badly the idea fails, on
purpose and in detail. Three walls stand in the way. **Focus:** to concentrate the beam
onto a 1 km target at the distance of Pluto, your transmitter must be about six billion
wavelengths across — and cranking the frequency up doesn't rescue you, it just changes
what that means in metres, from absurd to merely impossible. **Grip:** a gravitational
wave stretches and squeezes things, it doesn't *push* them; to push, the asteroid would
have to absorb the wave, and it barely absorbs any. **Strength:** we're roughly forty
orders of magnitude short on raw power. For scale, NASA's DART mission actually shifted an
asteroid in 2022 by flying a spacecraft into it, and even that delivered about a thousand
times less push than the job needs. The rule we've written into the project: **if a code
change ever makes one of these walls vanish, we assume the change is broken, not that we
solved it.**

### R6 — Cross-channel comparison at the target

**Q.** How does radiative coupling compare, quantitatively, against the one
gravity-based deflection mechanism that demonstrably works?

**Run.** `compare_channels` across the scoping set: tidal strain, absorption thrust, and
near-zone gravitational gradient (the gravity-tractor mechanism<sup>9,10</sup>).

**Report.** Table 3: all three channels side by side, same units, same configuration.

**Falsifier.** Radiative coupling exceeding the near-zone channel at any modelled
configuration would contradict the framework's stated expectation and must be
investigated as a defect before being reported as a result.

**Status.** `AWAITING RUN`.

***Non-expert summary:*** There's already a respectable, boring way to nudge an asteroid
with gravity: park a heavy spacecraft next to it and let ordinary gravitational attraction
tow it, very slowly. That's the "gravity tractor," and it's the benchmark any exotic
proposal has to beat. Here we put all three options side by side in the same units and let
the reader compare. Note the built-in scepticism: if our fancy wave-based method ever
*beats* the boring one, we treat that as a probable bug to investigate before we'd treat
it as a discovery.

### R7 — Numerical-regime findings

**Q.** Which numerical constructions in this problem fail *silently* at astronomical
scale, and what is the sufficient remedy?

**Report.** Extended Data Table 3, and the Methods derivation of the split-phase
identity.

**Status.** `AVAILABLE` — this subsection can be written now from committed results and
is, in our judgement, of interest beyond this application. Two findings: differencing
two ~10¹² m element ranges at 40 AU returns **exactly zero in float64** — every
element's range rounds to the same value, so 100% of the focusing information is lost
with no error, no warning, and a plausible-looking array of zeros; and the absolute
propagation phase at 40 AU / 1 kHz is ~1.25 × 10⁸ rad, where float64's representable
spacing (~1.5 × 10⁻⁸ rad) is **~340× larger than the entire per-element differential**
(~4.4 × 10⁻¹¹ rad). The reference/differential split is therefore not a single-precision
optimization; it is the only way to obtain the quantity at all. Both are verified
against 60-digit decimal references rather than against the implementation's own
arithmetic.

***Non-expert summary:*** This finding has nothing to do with gravity and may be the most
broadly useful thing here. Computers store numbers with limited precision. When you
subtract two enormous, almost-identical distances — billions of kilometres that differ by
a few metres — the computer returns **exactly zero**. Not approximately: exactly. Every
scrap of the information you needed is silently destroyed, with no error message and a
perfectly innocent-looking answer. We hit this twice in different places. The fix is to
rearrange the arithmetic so the enormous number is never actually written down. Anyone
doing precision work at astronomical scale — navigation, radar, interferometry — can hit
this same trap, which is why we're reporting it separately.

---

## Discussion

**What this framework is for.** Its most valuable output is not a working device. It is
a parameterized, auditable statement of *which orders of magnitude must be attacked, and
in what order*, so that contributors across a long project lifetime aim at the real
bottleneck rather than a comfortable one. The "transducer" problem — whatever physical
mechanism might convert stored energy into gravitational radiation at useful efficiency
— is deliberately out of scope and is registered as an open conjecture rather than
assumed away.

***Non-expert summary:*** We are not claiming to have built a tractor beam, and we don't
expect anyone to build one soon. What this project produces is a rigorous, checkable map
of *exactly which impossible things would have to become possible, and in what order* — so
that anyone working on this over the coming decades attacks the real bottleneck instead of
whichever one happens to be the most fun. The single biggest unknown — what physical device
could turn stored energy into gravitational waves efficiently — we explicitly do **not**
solve, and we file it as an open question rather than quietly assuming it away.

**The spin-2 array results are the transferable physics.** They are independent of the
deflection application and apply to any proposal involving coherent superposition of
gravitational radiation from spatially separated sources. The 90°-cancellation result in
particular is a trap that any group approaching this problem from an engineering
background will encounter, and it is not documented in the array-synthesis literature
because that literature is spin-1 by construction.

***Non-expert summary:*** The rotation rules we derived don't depend on asteroids at all.
They apply to *any* attempt to combine gravitational-wave sources, for any purpose. The
90°-cancellation result in particular is a landmine sitting directly in the path of anyone
who approaches this from an engineering background — which is to say, most people who
would try — and it appears nowhere in the existing antenna literature, because that
literature never had to consider it.

**On negative results as deliverables.** The framework's derivation of the uniform-sphere
l = 2 finite-size form factor (Methods) illustrates the epistemic machinery working as
designed. A literature search for a citable numbered equation **failed**, and that
failure is recorded as the decision rather than papered over: the result is admitted as
our derivation, justified by three independent numerical routes agreeing to
1.7 × 10⁻¹², with the likely primary source cited *without* an equation number because a
guessed number is worse than none. In the process, both form factors originally proposed
for the task were shown to be the wrong multipole order — one of them being spin-1
antenna machinery that was within one commit of entering the codebase as gravitational
physics.

***Non-expert summary:*** A worked example of the safety machinery catching a real error.
We needed a particular correction factor and went looking for a published source. We
couldn't find one — and rather than fudge it, we recorded the failure itself as the
decision, derived the result ourselves, and proved it three separate independent ways that
agree to twelve decimal places. Along the way we discovered that **both** of the formulas
we'd originally intended to use were simply wrong for this situation, and one of them was
the borrowed-from-antennas mistake described earlier. It was one step away from going into
the code as real gravitational physics.

**Limitations.** (i) The linear formalism cannot access nonlinear ("Christodoulou")
memory; only linear memory is available. For the finite-maneuver configurations modelled
here the linear term dominates, but this is a real restriction. (ii) The static
(adiabatic) tidal response assumes the body reaches equilibrium deformation
instantaneously relative to the drive, which **fails as the drive frequency approaches
the body's internal modes — exactly the high-frequency regime the ω⁶ scaling makes most
interesting.** No frequency-dependent complex-k₂ treatment exists here yet. (iii) The
Love-number model assumes a homogeneous incompressible sphere and therefore breaks for
differentiated, porous or rubble-pile bodies, i.e. a large fraction of real deflection
targets; the function cannot detect this from its arguments and the caller must. (iv) At
40 AU, focusing is numerically degenerate with steering — a "focal point" is a steering
direction at infinity — so near-field focusing is out of scope and the code raises
rather than degrading when asked for it. (v) Momentum-non-conserving configurations are
modelled only as a stamped diagnostic; they are not an approximation but a deliberate
fiction, since the linearized field equations are strictly inconsistent with a
non-conserved source.

***Non-expert summary:*** Five things this work genuinely cannot do, stated plainly.
**(i)** We can only model the simpler of two known permanent after-effects a passing wave
leaves behind. **(ii)** We assume objects flex instantly in response to being driven,
which stops being true at high frequencies — and high frequency is precisely the regime
that's most promising, so this limitation bites exactly where it hurts most. **(iii)** Our
flexing model assumes a uniform solid ball, but many real asteroids are loose piles of
rubble, and the software can't detect that on its own — a human has to notice. **(iv)** At
these distances "focusing" and "aiming" become mathematically the same thing; the code
refuses the request rather than pretending otherwise. **(v)** The physically impossible
setups aren't approximations, they're deliberate fictions, kept only as diagnostics and
branded accordingly.

**On adjacency to discredited work.** We state the boundary explicitly rather than
leaving it to the reader. A claim being adjacent to bad literature does not make it
wrong; it means the citation standard is *higher*, not lower. The feasibility ledger is
the working mechanism that holds the line, because it makes the framework report its own
distance from the application on every run. We do not cite the HFGW patent or conference
literature as authority for anything, and a source tracing to it halts the review
process by rule.

***Non-expert summary:*** We name the discredited work openly instead of hoping nobody
notices the resemblance. Sitting next to bad science doesn't make you wrong — but it does
mean you owe the reader *more* rigour, not less. Our practical defence is the scorecard:
the tool reports its own shortfall every time it runs, which is precisely what the
discredited work never did. And we have a hard rule that if a source traces back to that
literature, work stops rather than continuing carefully.

---

## Methods

### Physical formulation

We work in linearized gravity throughout. With g_μν = η_μν + h_μν, |h_μν| ≪ 1, and the
trace-reversed perturbation h̄_μν = h_μν − ½η_μν h, the harmonic-gauge field equation has
the retarded solution

  h̄^μν(t, **x**) = (4G/c⁴) ∫ T^μν(t − |**x** − **x**′|/c, **x**′) / |**x** − **x**′| d³x′
  *(ref. 4, eq. 1)*

The radiative quadrupole formula and luminosity are

  h_ij^TT(t, r) = (2G/c⁴r) · Λ_ij,kl(n̂) · d²Q_kl/dt² |_(t − r/c)
  *(ref. 4, eq. 2)*

  Q_ij = ∫ ρ(**x**)(x_i x_j − ⅓δ_ij|**x**|²) d³x
  *(ref. 4, eq. 3)*

  L_GW = (G/5c⁵) ⟨ d³Q_ij/dt³ · d³Q_ij/dt³ ⟩
  *(ref. 4, eq. 4)*

with the TT projector taken from ref. 5, eq. 4.22. `Q_ij` denotes the **reduced
(trace-free)** moment throughout; where a source uses the second moment I_ij the
conversion Q_ij = I_ij − ⅓δ_ij I is applied at the point of use and noted in the
docstring, and the function names distinguish them.

***Non-expert summary:*** The four equations above are the standard, long-established
textbook physics of gravitational waves — we implement them, we don't defend them. In
words: treat space as flat with a small ripple on top; the ripple spreads outward at the
speed of light, so what you feel now depends on what the source was doing earlier, by
exactly the travel time; the strength of the ripple depends on how the source's *shape*
is changing; and the total energy radiated depends on how fast that shape-change is
itself changing. The final note is pure housekeeping: there are two slightly different
conventional definitions of "shape," they differ by a simple correction, and we pick one,
name our functions accordingly, and flag every place a source uses the other — because
mixing them up silently is a classic error.

**Analytic derivatives are mandatory.** For point masses, differentiating ref. 4 eq. 3
in time gives closed forms for Q̈_ij and Q⃛_ij in terms of positions, velocities,
accelerations and jerks. Finite differencing at third order is forbidden in this
codebase, and the prohibition is measured rather than asserted: relative error against
the analytic form follows the classic U-curve, reaching **1.1 × 10²** (i.e. wrong by a
factor of 100) at step h = 10⁻⁶ and bottoming at 8.0 × 10⁻⁷ at h = 10⁻³. The decisive
validation is not the finite-difference comparison but the algebraic identity: the
luminosity built from the analytic Q⃛ reproduces the independent closed form
L = (32/5)(G/c⁵)μ²a⁴ω⁶ to 4.1 × 10⁻¹⁶.

***Non-expert summary:*** The energy calculation needs a rate-of-change-of-a-
rate-of-change-of-a-rate-of-change. There are two ways to get such a thing: do the calculus
by hand and write down an exact formula, or have the computer estimate it by comparing
nearby values. **We ban the second method, and we measured why.** Estimating numerically
can be wrong by a factor of a hundred, and — counterintuitively — asking for *finer*
steps makes it worse, not better, because tiny rounding errors get amplified. Our
hand-derived version was confirmed a different way entirely: it reproduces a known exact
algebraic answer to sixteen decimal places.

### Software architecture

Nine packages under `src/gwtb/`, in dependency order:

| Layer | Responsibility |
|---|---|
| `core` | Physical constants with sources; `StrainScale` scaled-strain representation; ADR-0002 shape/dtype/unit-vector validation guards; array-API backend shim (NumPy / Numba), field-grid kernel, split-phase arithmetic |
| `bodies` | `Sphere` (mass, inertia, self-quadrupole, oblateness); Love-number elastic deformation; multipole moments and their analytic derivatives; finite-size form factor with an out-of-regime warning |
| `kinematics` | Finite acceleration profiles (bang-bang, S-curve, quintic, raised-cosine) behind one abstract base; prime-frequency multi-tone drive synthesis; spectral analysis |
| `source` | Quadrupole strain and luminosity; maneuver waveforms; linear memory; the flagged dipole path; conservation audit and `UNPHYSICAL` stamping |
| `propagate` | Transverse-traceless projection; per-source retarded evaluation and batched propagation; spin-2 polarization basis, decomposition and rotation |
| `array` | Element geometry (linear, planar, sparse); grating-lobe bounds; scalar array factor (**explicitly the spin-1 baseline**); spin-2 tensor superposition and mismatch loss; focal phases, focused field, spot size, trade surfaces |
| `target` | Geodesic deviation; three coupling channels compared side by side; Δv and miss-distance propagation |
| `ledger` | Frozen `GapMetric` schema, `GapReport`, run manifests, per-epic row builders |
| `viz` | Beam patterns (polar and 3-D), polarization ellipses, field slices, volumetric export |

***Non-expert summary:*** The table above is the floor plan, one row per layer, listing
what each is responsible for. Note the entry for the `array` layer: it deliberately
contains **both** the old radio-style calculation and the new gravitational one, with the
old one explicitly labelled so nobody mistakes it for physics. Keeping a known-good wrong
answer around on purpose, clearly marked, is how we prove the new answer is a careful
extension rather than an unchecked replacement.

At the time of writing: **7,117 lines of source, 8,801 lines of test, 870 tests** (867
passing; 3 skipped for optional GPU/rendering dependencies), 53 registered equations,
7 architecture decision records, 3,139 lines of governance documentation, and 111 of 118
planned tasks complete.

***Non-expert summary:*** Some scale figures. There is **more test code than actual code**
— about 8,800 lines of checking against 7,100 lines of doing — which is unusual and
deliberate for a project whose main product is trustworthiness. 870 automated checks run
every time anything changes. 53 equations are individually catalogued with their sources,
and there are another 3,100 lines of documentation purely about how decisions get made and
recorded.

**Binding conventions (ADR-0002).** Body collections are "first axis is the body"
(`masses (N,)`, `positions (N,3)`, …), matching row-major locality and the convention in
`astropy` and most N-body codes. Tensors carry their indices in the **trailing** axes, so
`einsum` subscripts are identical whether or not a leading time or grid axis is present.
Directions are unit vectors validated to atol 10⁻¹² — a silently unnormalized direction
produces a plausible, wrong TT projection. **SI units internally, everywhere, with no
geometric-unit (G = c = 1) shortcuts**: the conversion from geometric units in the
literature is precisely where factors of G/c⁴ get dropped, so keeping SI throughout means
every implemented equation carries its dimensional factors explicitly and can be
dimension-checked against its citation. **float64 everywhere**, with no float32 without
an ADR authorizing it, and public entry points *raise* on float32 input rather than
promoting it, so upstream precision loss is caught rather than masked. Retarded time is
computed **per source element**, never from an array centroid; the test suite contains a
benchmark that distinguishes the two, because retardation from the wrong origin is a
quiet, high-damage error.

***Non-expert summary:*** House rules everyone must follow, each chosen to prevent a
specific silent mistake. **Use ordinary metres and kilograms throughout**, never the
compressed "natural units" physicists prefer — those look elegant but hide constants, and
hidden constants are exactly what goes missing when you copy a formula out of a paper.
**Always use high-precision numbers**, and if someone hands the code low-precision ones it
stops rather than quietly upgrading them, so that the sloppiness is caught where it
happened. **Compute the travel-time delay separately for every emitter**, never once for
the array as a whole — a small shortcut there produces answers that look completely
reasonable and are wrong.

### Spin-2 tensor superposition

Implemented as `superpose_tt`, with the derivation recorded in ADR-0003. Acceptance
conditions, all committed as tests: the construction reduces to the scalar array factor
for co-oriented elements to rtol 10⁻⁹ (the regression that proves the extension is a
controlled departure); for Δψ = 45° the gain is strictly less than N²; `mismatch_loss`
returns cos(2Δψ), is maximal at 45° rather than 90°, and has period 180°; and the 90°
**cancellation** is asserted explicitly by name, since it is the case most likely to be
"fixed" by a contributor applying electromagnetic intuition.

***Non-expert summary:*** This is the core new calculation, and the list above is what it
must prove before we accept it. The last item is the interesting one: there is a test whose
*name* says the 90° case must produce exactly zero. It's named that explicitly because a
future contributor with a radio background will look at that zero, conclude it's obviously
a bug, and "fix" it. The test exists to stop them — it's a message to someone who hasn't
joined the project yet.

`superpose_tt` sums along **one common observation direction** and raises inside the
Fraunhofer distance, because tensors projected along different directions live in
different polarization spaces and cannot be added. Whether this permitted a focusing
construction was resolved by measurement rather than assumption (ADR-0006): at 40 AU the
angular spread of per-element observation directions is 1.034 × 10⁻⁹ rad against the
5.009 × 10⁻² rad alignment budget — a **2.4 × 10⁷ ×** margin — so the common-n̂ premise
is not threatened, and `focused_field` is a steered far-field superposition with weights
exp(+i·φ_a). Near-field focusing is out of scope, the existing Fraunhofer guard enforces
it, and the resulting error is propagated rather than caught.

***Non-expert summary:*** The combining calculation only works if every emitter is
looking at the target in *effectively* the same direction — otherwise you'd be adding
quantities that aren't comparable, like adding a northward push to an eastward one and
calling the result a number. Rather than assume that was fine, we measured it: at the
target distance, the directions differ by about a **twenty-five-millionth** of what would
be needed to cause trouble — a safety margin of 24 million. So the assumption is safe here,
and we've written down exactly the circumstances that would make it unsafe. If someone
requests a scenario where it *would* break, the code stops with an error instead of
producing a confident wrong answer.

### The uniform-sphere finite-size form factor

The exact radiative source multipole replaces the long-wavelength radial weight r^l with
the j_l(kr) factor of the outgoing Green's-function partial-wave expansion:

  I_l^exact = [(2l+1)!! / k^l] ∫ j_l(kr) ρ_l(r) r² dr

which reduces to ∫ρ_l(r) r^(l+2) dr as kr → 0. Substituting the small-argument series
for j_l — taken from **DLMF 10.53.1**<sup>11</sup>, transcribed literally and verified in
exact rational arithmetic for l = 0…6 — and dividing by the long-wavelength limit gives

  F_l(kR) = 1 − (kR)²(l+3)/[2(2l+3)(l+5)] + O((kR)⁴),

and at l = 2, **F₂(kR) = 1 − 5(kR)²/98**.

***Non-expert summary:*** All the simple formulas assume the emitting object is tiny
compared to the wavelength it produces. Real objects aren't, and the correction matters.
Working it out gives a specific small number: the emission is reduced by a factor involving
5/98. Getting that exact fraction right is the whole point of this section — several
plausible-looking wrong fractions exist, and they're nearly impossible to tell apart by
eye.

**Verification.** Four independent routes (Extended Data Table 4). Exact rational series
from DLMF 10.53.1 gives 5/98 exactly for l = 0…6 and, as an external anchor, reproduces
the textbook-checkable l = 0 result 1 − (kR)²/10. A far-field retarded phase integral
over a uniform ball by two-dimensional Gauss–Legendre quadrature — **evaluating no
spherical Bessel function anywhere** — gives 0.051020408163352, a relative error of
**1.7 × 10⁻¹²**. Direct integration of the exact retarded Green's function exp(ikD)/D at
*finite* distance, with no far-field approximation, gives 1.4 × 10⁻⁸; that residual was
diagnosed rather than assumed, being flat in observation distance, *growing* with
quadrature order (which no truncation error does), and ~3× the self-contained noise floor
supplied by the analytically-vanishing imaginary part — i.e. float64 accumulation, not
physical disagreement. A literal point-mass lattice of up to 1.44 × 10⁶ masses gives
~5 × 10⁻⁵, consistent with its O(h) staircase.

***Non-expert summary:*** Because we had no published source to cite, we proved the answer
four separate ways that share no machinery — so a mistake in one method can't hide in the
others. The strongest agrees to twelve decimal places. One method deliberately simulates
the sphere as over a million individual point masses and just adds up their contributions
by brute force. Where one route disagreed slightly, we didn't wave it away: we diagnosed
it and showed the discrepancy *grew* when we asked for more computational precision — which
is the signature of accumulated rounding noise, not of a real physical disagreement.

**The radial profile is load-bearing.** Equation F_l assumes the l-pole mass distribution
is *volume-filling*, δρ uniform on [0, R]. A body that acquires its quadrupole by
deforming its **surface** has δρ ∝ δ(r − R) and a different answer,
F₂^surface(kR) = 15 j₂(kR)/(kR)² = 1 − (kR)²/14 — **40% larger**. Both are "the uniform
sphere"; the phrase does not determine the answer. The correction must therefore **not**
be applied to the tidal Love-number or Maclaurin-oblateness quadrupoles, which are
incompressible-body surface deformations, without re-deriving. A future source quoting
1/14 is *not* a confirmation of this result — it confirms the other one.

***Non-expert summary:*** A subtle trap worth the warning. There are two different ways a
uniform ball can distort — throughout its whole volume, or only at its surface — and they
give answers differing by 40%. Both are honestly described by the phrase "a uniform
sphere," so the words alone don't tell you which formula you need. We use the first. The
warning to the future: if someone later finds a textbook quoting the *other* number, that
is **not** confirmation that we were right — it's confirmation of the other case entirely,
and treating it as agreement would introduce a 40% error while feeling like diligence.

**Validity floor.** The leading-order series goes *negative* at kR = √(98/5), i.e.
R/λ = 0.7046, and is meaningless well before that; departure from unity is already
2.0142% at R/λ = 0.1. A structured `LongWavelengthAssumptionWarning` is raised at
R/λ ≥ 0.1, naming the assumption-ledger row it violates. The exact closed form
F₂(x) = 75[3Si(x) + x cos x − 4 sin x]/x⁵ is recorded as the test reference but is **not**
a remedy: it is cancellation-limited below kR ≈ 0.05, losing ~5 digits per decade, and is
*less* accurate than the series in the regime the function is used in.

***Non-expert summary:*** This correction is an approximation, and approximations have
edges. Past a certain object size the formula starts returning *negative* emission, which
is physically meaningless — so the code actively warns you when you approach that edge, and
tells you which written-down assumption you're violating. There is also an exact version of
the formula, and here's the counterintuitive part: **the exact version is worse in
practice**, because computing it involves subtracting nearly-equal large numbers, the same
precision-destroying trap described earlier. So we keep the approximate one and guard its
edges.

The implementation is mutation-tested: replacing 5/98 with 1/6, 1/10, 1/14, a sign flip,
a 0.1% nudge, or a **0.001%** nudge each fails 4–5 tests. Notably, the natural "tends to
unity as R/λ → 0" test passes for *every* wrong coefficient except the sign flip; the
load-bearing test is the one that pins the coefficient exactly.

***Non-expert summary:*** To confirm the tests actually work, we deliberately broke the
code and checked they noticed. We swapped in each of the plausible wrong fractions, flipped
a sign, and nudged the correct value by a **thousandth of a percent** — every sabotage was
caught. This also exposed something important: the most obvious, natural-seeming test
passes happily for *every* wrong value we tried. It would have given complete false
confidence. Only one specific test does the real work.

### Conservation auditing and the `UNPHYSICAL` stamp

Two layers. `audit` *detects* non-conservation from masses and accelerations. A
`StampedResult` wrapper *propagates* that verdict through arithmetic so it cannot be
laundered.

***Non-expert summary:*** Two separate jobs. One part *notices* that a setup is
physically impossible. The other part makes sure that verdict travels with the number
through every subsequent calculation, so it can't be lost or laundered along the way.

The natural implementation — an `np.ndarray` subclass with `__array_finalize__` — was
built and measured first, and rejected on one row of evidence: `np.asarray` and
`np.array` on an ndarray subclass take a fast path that returns a **base-class array
without ever calling `__array__`**, silently discarding the stamp. Defining `__array__`
does not help; it is not consulted. There is no hook, and therefore no way to make the
loss loud. `np.asarray` is the call most likely to appear in exactly the plotting, export
and serialization code where an unstamped 10¹⁰ artifact would do its damage, and the call
least likely to be scrutinized in review.

***Non-expert summary:*** We tried the obvious approach first and it failed a test we're
glad we ran. The natural way to attach a permanent label to a number turns out to have a
hole: one extremely common, innocuous-looking operation strips the label off silently, with
no way to detect or prevent it. Worse, that operation is exactly what appears in the
plotting and file-saving code — the very last step before a number becomes a chart someone
puts in a presentation, and the step nobody scrutinises. So we threw the approach away.

`StampedResult` is therefore an explicit wrapper. Because it is not an ndarray, NumPy is
*obliged* to call `__array__`, where a stamped result raises `StampStrippedError` instead
of converting. Arithmetic is routed through `__array_ufunc__` with `__array_priority__`
set so that `ndarray + StampedResult` defers to the wrapper. Three supporting rules:
unphysicality is **contagious** (results derived from two unphysical sources name both);
`out=` is **refused**, since writing into a caller-supplied array is the same laundering
hole by another route; and there is **no `unstamp()` method** — raw numbers come from an
explicit, greppable `.value` attribute that leaves a trace in review. 36 tests cover
arithmetic in both operand orders, ufuncs, reductions, slicing, `str()`, JSON
round-trips, and refusal of each coercion path. That `StampedResult` will not drop into a
function requiring an ndarray is the **intended behaviour**: such a function is precisely
where the stamp would have been lost.

***Non-expert summary:*** The replacement design puts the number inside a sealed container
that the system cannot open behind your back. Three deliberate cruelties. The taint is
**contagious** — anything computed from a tainted number is itself tainted, and names both
sources. There is **no "remove label" function**, on purpose; the only way to get the raw
number out is a specific phrase that's easy to search for, so it shows up in review. And
the container deliberately **won't fit** into ordinary code that expects a plain number.
That's not a shortcoming to work around — those are precisely the places the label would
have been lost.

The frozen ledger schema initially had no field able to carry a stamp, which *forced*
callers to unwrap to `.value` — turning the artifact into a ledger row that clears its
requirement by ten orders of magnitude. This was caught as a Critical review finding on
the day the schema was frozen and closed by a sixth field, `provenance`, plus a
`GapMetric.from_stamped()` constructor, while the freeze still had no dependents. The
residual risk is ergonomic rather than structural and is recorded as such.

***Non-expert summary:*** A near-miss worth recording. The scorecard format was finalised
without anywhere to record the taint — which meant anyone filling in the scorecard was
*forced* to strip the label first. The result would have been a report claiming we'd
exceeded our target by ten billion times, with nothing on the page indicating it was
nonsense. Caught on the same day the format was frozen, and fixed by adding a column while
nothing yet depended on it.

### Numerical methods at astronomical scale

Two constructions in this problem fail silently and are documented as findings.

***Non-expert summary:*** Two ways the arithmetic itself betrays you at these distances,
both of which we record as findings rather than quietly patching.

**Range differencing.** The direct difference of two ~10¹² m element ranges at 40 AU is
**identically zero in float64**. The remedy is never to form the large quantity:
R_a − R_ref = (|q_a|² − 2s·q_a)/(R_a + R_ref).

***Non-expert summary:*** Subtracting two nearly-identical astronomical distances gives
exactly zero, destroying the very information you were after. The fix is algebraic
sleight of hand: rearrange the sum so the enormous numbers cancel *on paper*, before the
computer ever has to store one.

**Absolute phase.** At 40 AU / 1 kHz the absolute propagation phase is ~1.25 × 10⁸ rad,
where float64's spacing is ~1.5 × 10⁻⁸ rad — ~340× larger than the entire per-element
differential of ~4.4 × 10⁻¹¹ rad. (In float32 the spacing at that magnitude is ~8 rad,
wider than a full cycle.) The remedy is a `SplitPhase` factorization
exp(iφ_a) = exp(iφ_ref)·exp(iΔφ_a) in which phasors *multiply*, so the large common phase
and the small residual are never added. The framework exposes `.phasor()` and documents
`.recombine()` as irreducibly lossy. **This is not a single-precision optimization; it is
the only way to obtain the number at all.** Both are validated against 60-digit `decimal`
references rather than against the implementation's own float64 arithmetic.

***Non-expert summary:*** The same disease in a second place. Tracking where a wave is in
its cycle after travelling billions of kilometres requires a number so large that the
smallest difference the computer can represent is **340 times bigger than the entire
effect we're trying to measure**. In lower precision it's worse still — the gap exceeds a
full wave cycle, so the answer is pure noise. The fix splits the number into a huge shared
part and a tiny individual part that are multiplied rather than added, so they never meet
inside a single quantity. To be sure, we check the result against arithmetic carried out to
sixty digits, rather than against the code's own answers.

The framework also enforces that strain is carried in a scaled representation:
h ~ 10⁻⁴⁰ is *subnormal* in IEEE binary32 (smallest normal ≈ 1.18 × 10⁻³⁸) and loses
precision in intermediate float64 products.

***Non-expert summary:*** A related storage problem: the signal is so faint that in
lower-precision arithmetic it falls off the bottom of what can be represented at all. So we
carry it in rescaled units and convert only at the very end.

### Governance mechanisms

**Citation CI.** `tools/check_citations.py` parses the AST of every module in the physics
packages and requires each public function and class to carry
`Source: <reference>, eq. <number>`. The regular expression demands the `eq.` token
specifically — that is what distinguishes a citation from a hand-wave at a chapter.
Docstrings are whitespace-collapsed before matching so that long citations may wrap
legitimately. Infrastructure, visualization and ledger packages are exempt by
declaration, on the ground that they consume cited results rather than introducing
equations. Exit code 1 fails the build.

***Non-expert summary:*** An automated gatekeeper reads the source code and refuses to let
it build unless every physics function names the exact equation it implements. Pointing at
a whole chapter isn't good enough — it must be a specific numbered equation a reader can
look up in one step. Layers that only *use* physics rather than introduce it are exempt,
and that exemption is written down rather than assumed.

**The five-gate commit check.** `ruff check`, `ruff format --check`, `mypy src`,
`check_citations.py`, and `pytest`. All five must pass.

***Non-expert summary:*** Five automatic checks run before any change is accepted:
style, formatting, type consistency, citations, and the full test suite. All five must
pass — there is no "just this once."

**The task workflow.** Every unit of work runs RESEARCH → IMPLEMENT → REVIEW → INDEX,
with gates: a governing equation must be verified against its primary source *before*
implementation, and a research pass returning UNVERIFIED **blocks** the task and escalates
it to a design spike rather than permitting implementation from memory. Spikes produce a
decision record and no production code. Physics changes receive additional
dimensional-analysis, index-convention and spin-2 review checks.

***Non-expert summary:*** Every piece of work follows the same four steps: look it up,
build it, review it, record it. The important rule is the first gate — **if the source
can't be verified, work stops.** Nobody is permitted to implement physics from memory,
however confident they are. When that happens the task converts into a research
investigation whose only output is a written decision, deliberately producing no code at
all, so the reasoning gets settled before anything is built on it.

**Structural anti-silence.** The project's recurring failure mode has not been wrong
output but *silent disappearance*: a task that failed to parse and vanished from the
schedule; tasks stranded behind a blocker and simply absent from the plan; completed work
misreported as unreachable; a task declared blocked in prose but scheduled anyway,
because the scheduler reads a machine-readable dependency field and cannot read an
English paragraph. The standing rule is to fail loudly rather than degrade quietly, and
blocking conditions are expressed in the field the tool actually reads.

***Non-expert summary:*** The mistakes that have actually hurt this project were never
wrong answers — they were **things quietly disappearing**. Work that fell off the schedule
without anyone noticing. Tasks blocked in a way nobody could see. One case where a human
wrote "this is blocked" in a sentence, but the scheduling tool only reads a structured
field and cheerfully scheduled it anyway. The lesson, now a standing rule: prefer a loud
crash to a quiet degradation, and put warnings in the place the machine actually looks —
not in prose it can't read.

### Validation suite

Benchmarks, distinct from unit tests, validate physics against external or analytic
references (Extended Data Table 1). A benchmark that has not run since the code it
validates last changed is treated as **stale, not passing**. Where a specified external
reference was unavailable — an array-synthesis package that could not be installed in the
offline build environment — the substitution to a closed-form analytic reference is
**recorded in the index as a flagged substitution** rather than made silently, per the
project's own "make absence loud" rule.

***Non-expert summary:*** We separate two kinds of checking: does the code do what we
intended, and does the physics match reality? A validation that hasn't been re-run since
the code changed is treated as **expired, not passing** — the same way you'd treat food.
And when we couldn't obtain a comparison tool we'd planned to check against, we substituted
a different reference and *wrote that down prominently*, rather than swapping it in quietly
and letting the paper imply a comparison we never made.

Two cross-validations are worth naming because they were predicted before the code
existed. Linear memory computed from the Braginsky–Thorne/Favata formula<sup>12</sup>
reproduces the settled post-maneuver value of the independent quadrupole route
**bit-for-bit on-axis** (difference exactly 0.0), and to 1 ULP for oblique observation
directions — the discrepancy being arithmetic, not physical, since the quadrupole route
forms and then subtracts a trace term that the projection removes analytically but whose
rounding does not vanish. Asserting bit-equality off-axis would be asserting a property of
float64 operation ordering, so the benchmark asserts exactness on-axis and 4 ULP off it.

***Non-expert summary:*** The most satisfying check in the project. A passing
gravitational wave leaves a permanent trace — space doesn't quite return to how it started.
That can be computed two completely different ways, and we wrote down, *before either was
implemented*, that the two must agree. They do: in the head-on case, **not approximately
but to the very last binary digit.** Off to one side they differ in the final digit, and we
tracked down exactly why — an unavoidable rounding artefact of doing the arithmetic in a
different order, not a physics disagreement. So we require perfection head-on and allow a
few digits' slack elsewhere, rather than pretending either result is more exact than it is.

### The epistemic firewall

Codified as a rule with a mechanical consequence: a source tracing to the HFGW patent
literature or its associated web presences halts the review process and is never cited as
authority. The JASON review<sup>2</sup> is cited as the finding of record. Grishchuk and
Sazhin<sup>3</sup> is the credible prior art on deliberately engineered gravitational
radiation.

***Non-expert summary:*** A hard rule with teeth: if any source we're about to rely on
traces back to the discredited body of work, everything stops. Not "proceed with caution" —
stop. We cite the official government review as the record of *why* that work is
discredited, and we point to the one genuinely credible 1974 paper as the honest starting
point.

---

## Data availability

All numerical results in this manuscript are produced by the committed test and benchmark
suite and are reproducible from the repository at the tagged submission commit. Source
Data for each figure will be deposited as machine-readable run manifests
(`ledger.RunManifest`), each recording the configuration, the code version and the
provenance of every emitted metric. **Deposit DOI: to be minted at submission.**

***Non-expert summary:*** Every number in the paper can be regenerated by anyone who
downloads the code. Each figure will ship with a machine-readable record of the exact
settings and the exact version of the code that produced it, so a sceptic can rebuild the
result rather than take our word for it.

## Code availability

`gwtb` is released under Apache-2.0. The explicit patent grant is deliberate: the project
invites outside groups to develop hardware against the framework, and that clause protects
both them and downstream users. Repository:
`https://github.com/sudo-install-gravity/tractor-beam-cathedral`. **The repository must be
public before submission** — this is a tracked, currently-open blocker.

***Non-expert summary:*** The code is free and open for anyone to use, including
commercially. We chose a licence that explicitly grants patent rights, because we're
inviting other people to try building hardware against this framework and we don't want
them exposed to a patent trap later. One catch: the repository isn't public yet, and it
must be before this paper can be submitted.

---

## References

*(Nature style, numbered by first appearance. Placeholders marked `[complete]` still need
volume/page verification against the published record.)*

1. Abbott, B. P. *et al.* Observation of gravitational waves from a binary black hole
   merger. *Phys. Rev. Lett.* **116**, 061102 (2016).
2. Eardley, D. *et al.* *High Frequency Gravitational Waves*. JSR-08-506 (JASON, MITRE
   Corporation, 2008).
3. Grishchuk, L. P. & Sazhin, M. V. Emission of gravitational waves by an electromagnetic
   cavity. *Sov. Phys. JETP* **38**, 215–221 (1974).
4. Blanchet, L. Gravitational radiation from post-Newtonian sources and inspiralling
   compact binaries. *Living Rev. Relativ.* **17**, 2 (2014). arXiv:1310.1528.
5. Flanagan, É. É. & Hughes, S. A. The basics of gravitational wave theory. *New J. Phys.*
   **7**, 204 (2005). arXiv:gr-qc/0501041.
6. Kowalska, I., Bulik, T., Belczyński, K., Dominik, M. & Gondek-Rósińska, D. The eccentricity
   distribution of compact binaries. *Astron. Astrophys.* **527**, A70 (2011).
   arXiv:1010.0511.
7. Weisberg, J. M. & Huang, Y. Relativistic measurements from timing the binary pulsar
   PSR B1913+16. *Astrophys. J.* **829**, 55 (2016). arXiv:1606.04581.
8. Daly, R. T. *et al.* Successful kinetic impact into an asteroid for planetary defence.
   *Nature* **616**, 443–447 (2023). `[complete]`
9. Lu, E. T. & Love, S. G. Gravitational tractor for towing asteroids. *Nature* **438**,
   177–178 (2005).
10. Schweickart, R., Chapman, C., Durda, D. & Hut, P. *Threat Mitigation: The Gravity
    Tractor*. B612 Foundation White Paper 042 (2006). arXiv:physics/0608157.
11. *NIST Digital Library of Mathematical Functions*, §10.53. https://dlmf.nist.gov/10.53
12. Favata, M. The gravitational-wave memory effect. *Class. Quantum Grav.* **27**, 084036
    (2010). arXiv:1003.3486.
13. Hinderer, T. Tidal Love numbers of neutron stars. *Astrophys. J.* **677**, 1216 (2008).
    arXiv:0711.2420.
14. Cheng, W. H., Lee, M. H. & Peale, S. J. Complete tidal evolution of Pluto–Charon.
    *Icarus* **233**, 242–258 (2014). arXiv:1402.0625.
15. Thorne, K. S. Multipole expansions of gravitational radiation. *Rev. Mod. Phys.* **52**,
    299–339 (1980). *(Cited without an equation number: the source is paywalled and its
    numbering could not be confirmed. Per this project's citation rule a guessed equation
    number is worse than none.)*
16. Orfanidis, S. J. *Electromagnetic Waves and Antennas* ch. 19 (Rutgers Univ., open
    access). *(Spin-1 reference by construction; cited only for the scalar baseline.)*
17. Misner, C. W., Thorne, K. S. & Wheeler, J. A. *Gravitation* (Freeman, 1973).
18. Born, M. & Wolf, E. *Principles of Optics* §8.5.2 (Cambridge Univ. Press, 1999).
19. Zel'dovich, Ya. B. & Polnarev, A. G. Radiation of gravitational waves by a cluster of
    superdense stars. *Sov. Astron.* **18**, 17 (1974).
20. Braginsky, V. B. & Thorne, K. S. Gravitational-wave bursts with memory and experimental
    prospects. *Nature* **327**, 123–125 (1987). *(Historical provenance only — a Letter
    with no numbered equations; ref. 12 is cited for the implemented form.)*
21. Dolph, C. L. A current distribution for broadside arrays. *Proc. IRE* **34**, 335–348
    (1946). *(In-paper equation numbers unconfirmed; implemented via `scipy.signal.windows`.)*
22. Taylor, T. T. Design of line-source antennas for narrow beamwidth and low side lobes.
    *IRE Trans. Antennas Propag.* **3**, 16–28 (1955). *(As ref. 21.)*
23. Fitzpatrick, R. *Newtonian Dynamics* and *Theoretical Fluid Mechanics* (Univ. Texas,
    open-access lecture notes).

***Non-expert summary:*** The sources we rely on. Two entries are unusual and worth
noticing. **Ref. 15** is cited deliberately *without* an equation number, because the paper
sits behind a paywall and we couldn't confirm the numbering — and our own rule says a
guessed number is worse than no number. **Ref. 16** is an antenna textbook, included only
as the labelled radio-physics baseline; it must never be cited for anything gravitational,
and the note says so where anyone would see it.

---

## Acknowledgements

*Placeholder.*

## Author contributions

*Placeholder — use CRediT taxonomy. Must be reconciled with the repository's commit
provenance and `CITATION.cff` before submission.*

## Competing interests

The authors declare no competing interests. *(Confirm before submission; note the
Apache-2.0 patent grant in Code availability.)*

***Non-expert summary:*** Standard journal declarations, not yet filled in. The last one
states that nobody stands to profit in a way that might bias the results — flagged for
confirmation before submission, given the patent grant mentioned above.

---

## Display items

### Table 1 | Spin-2 versus spin-1 array behaviour

Two co-phased elements, the second rotated by Δψ about the line of sight. Measured values
from the committed two-element prototype; the spin-1 column is what an antenna-theory
derivation predicts for the same geometry.

| Δψ | measured gain (spin-2) | 2 + 2cos(2Δψ) | spin-1 prediction | outcome |
|---|---|---|---|---|
| 0° | 4.000000 | 4.000000 | 4.000000 | full coherence, gain N² |
| 30° | 3.000000 | 3.000000 | 3.732051 | partial |
| **45°** | **2.000000** | 2.000000 | 3.414214 | **orthogonal — powers add, gain N** |
| 60° | 1.000000 | 1.000000 | 3.000000 | partial |
| **90°** | **0.000000** | 0.000000 | 2.000000 | **complete cancellation** |
| 180° | 4.000000 | 4.000000 | 0.000000 | full coherence again |

*Alignment tolerance (not shown): gain/N² ≈ exp(−4σ²), matching measurement to ~10⁻⁴
across σ ∈ [0°, 20°] at N = 100 and N = 1000. 1% loss at σ = 2.87°, exactly 2× tighter
than the spin-1 exp(−σ²).*

***Non-expert summary:*** The paper's key result in one table, and the fastest way to see
the point. Take two emitters and rotate one relative to the other. Column 2 is what
gravity actually does; column 4 is what radio-antenna theory predicts for the identical
arrangement. **At 90° they disagree completely**: gravity gives you exactly zero, radio
theory promises double. At 180° the roles reverse — gravity is back to full strength while
radio theory says zero. Anyone designing such an array using antenna intuition would build
something that emits nothing and have no idea why.

### Table 2 | Feasibility ledger — **STUB, awaiting R5**

| Wall | Achieved | Required | Units | Gap (decades) | Source module | Provenance |
|---|---|---|---|---|---|---|
| Diffraction (aperture) | *TBD* | *TBD* | wavelengths | *TBD* | `array.focus` | |
| Coupling (impulse) | *TBD* | *TBD* | N·s | *TBD* | `target.coupling` | |
| Magnitude (emission) | *TBD* | *TBD* | W | *TBD* | `source.quadrupole` | |
| Body quadrupole | *TBD* | *TBD* | kg·m² | *TBD* | `bodies.multipole` | |

***Non-expert summary:*** The scorecard, currently blank pending the experiments. When
filled in, each row will read: here's what we achieve, here's what's required, and here's
the shortfall expressed in powers of ten. The final column records where each number came
from, so no figure can appear without a traceable origin.

### Table 3 | Coupling channels compared — **STUB, awaiting R6**

| Channel | Mechanism | Magnitude | Units | Notes |
|---|---|---|---|---|
| Tidal strain | Geodesic deviation | *TBD* | — | The honest headline number |
| Absorption thrust | Momentum flux × cross-section | *TBD* | N | Expected negligible; reported anyway |
| Near-zone gradient | Gravity tractor (refs 9,10) | *TBD* | N | The benchmark any proposal must beat |

***Non-expert summary:*** Three ways gravity could move an asteroid, to be compared
side by side once measured. Note the middle row: we expect it to be so small as to be
irrelevant, and we're reporting it **anyway**, because silently omitting the unflattering
option is how honest comparisons turn into sales pitches.

### Figure legends

**Fig. 1 | Framework architecture.** Nine-layer dependency graph with the two
governance-motivated layers (`ledger`, conservation stamping within `source`) highlighted,
annotated with the equation IDs each layer implements. *To be drawn.*

**Fig. 2 | The provenance apparatus.** How citation CI, the claims registry, the assumption
ledger, the errata file and the unphysicality stamp interlock, and which failure mode each
was added in response to. *To be drawn.*

**Fig. 3 | Element mismatch is cos(2Δψ), not cos(Δψ).** Measured array gain versus relative
element orientation, with the spin-1 prediction overplotted; the complete cancellation at
90° annotated. *Awaiting R2.*

**Fig. 4 | Spin-2 alignment tolerance is exactly twice as tight.** Gain fraction versus
orientation jitter σ, against exp(−4σ²) and exp(−σ²); the 1% loss points at 2.87° and 5.73°
marked. *Awaiting R2.*

**Fig. 5 | Degeneracy breaking.** Radiated quadrupole amplitude versus radius at fixed mass
for the rigid, elastic and finite-size models. The rigid trace should lie on the numerical
floor. *Awaiting R3.*

**Fig. 6 | Mode-locked spatiotemporal focus.** Focal-plane amplitude map and
peak-to-background ratio versus √N. Caption **must** state the D/λ of the geometry and that
the background reference is √(Nπ)/2, not √N. *Awaiting R4.*

**Fig. 7 | The walls, in decades.** Gap between achieved and required for each ledger row,
sorted, with the transducer problem shown as an explicitly out-of-scope bar. *Awaiting R5.*

***Non-expert summary:*** The seven planned figures. Two are diagrams of how the software
and its safety machinery are put together. Three show the new rotation rules and the
alignment requirement. One shows the focusing experiment. The last one is the honest chart:
a bar per obstacle, each bar's height being how many powers of ten we fall short — including
a bar for the problem we explicitly refuse to claim we've solved.

### Extended Data

**Extended Data Table 1 | Benchmark validation status.** Benchmark, quantity, reference,
computed, deviation, equation ID, last-run commit. *Partially available.*

**Extended Data Table 2 | Degeneracy-breaking factors per mechanism.** *Awaiting R3.*

**Extended Data Table 3 | Silent numerical failures at astronomical scale.** Construction,
magnitude, failure mode, remedy, verifying test. *Available.*

**Extended Data Table 4 | Independent verification of the l = 2 form factor.** Four routes,
their shared machinery (none), and their residuals. *Available.*

**Extended Data Table 5 | Assumption ledger.** All 30 rows: assumption, where asserted,
valid when, breaks down at. *Available.*

**Extended Data Table 6 | Claims registry.** All 22 claims by category, with sources and
promotion/demotion history. *Available.*

***Non-expert summary:*** Six supporting tables for readers who want to check our work
rather than take it on trust. The two most useful to a sceptic are Table 5 — every
simplifying assumption together with the conditions under which it fails — and Table 6 —
every claim sorted into established fact, our own reasoning, or acknowledged guess.

---

## Numbers in this draft

Every numeric value above is one of three kinds, and the distinction must survive editing:

1. **Committed test/benchmark output** — reproducible today by `pytest` or a committed
   script. All numbers in the Main, Discussion, Methods and Table 1 are of this kind.
2. **Pre-registered target** — stated in the Results stub as what *will* be measured. No
   value is asserted.
3. **`TBD`** — a hole in a stub display item.

There are no values of a fourth kind, and none may be introduced. A number that cannot be
traced to a named test does not belong in this manuscript.

***Non-expert summary:*** A rule for whoever edits this draft next. Every number here is
one of exactly three things: something a computer can regenerate on demand today, a
placeholder for something we've promised to measure, or an explicit blank. There is no
fourth category — no estimates, no remembered figures, no "roughly." If a number can't be
traced to a specific test, it doesn't belong in the paper.

---

## Submission notes — delete before submission

**Venue.** *Nature* is a stretch for this manuscript and the drafting reflects a
deliberate choice about which contribution is foregrounded. The concept-feasibility
framing has no path: the framework's own ledger reports a gap of tens of orders of
magnitude, and an editor who reads "gravitational tractor beam" will place it next to the
literature ref. 2 assessed. The framing with a real chance is **methodological** — a spin-2
extension of array theory with no reference implementation, plus provenance enforced
mechanically in software — and this draft leads with that.

Realistic alternatives, in descending order of fit:

- ***Nature Computational Science*** or ***Nature Methods*** — a research-software paper
  whose thesis is that epistemic status can be made machine-checkable. Probably the best
  fit for the manuscript as written.
- ***Classical and Quantum Gravity*** or ***Phys. Rev. D*** — foreground the spin-2 array
  derivation and the finite-size form factor, drop most of the governance material to an
  appendix. This is where the *physics* result is most likely to be read by people who can
  check it.
- ***Journal of Open Source Software*** — for the software artifact itself; short, and
  complementary rather than competing.

***Non-expert summary:*** An honest assessment of where this could actually be published.
*Nature* is the most prestigious journal in science and this is a long shot — if we pitch
it as "we invented a tractor beam," an editor will file it next to the discredited work and
reject it, correctly. The version with a real chance leads with the *method*: a genuine new
piece of physics that nobody has worked out before, plus a novel approach to making
scientific software self-auditing. The alternatives listed are less famous but better
matched, and a physics-specialist journal is where experts most likely to *catch our
mistakes* would actually read it.

**Blockers before any submission.**

1. **The repository is not public.** Code availability cannot be satisfied. This is
   tracked in the backlog and is the project's sole remaining externally-blocked item.
2. **No `CITATION.cff`, no author list, no CRediT table.** A manuscript about provenance
   discipline that cannot state its own authorship provenance is self-refuting.
3. **The Results campaign has not been run.** R2–R6 are stubs by design; R1 and R7 could
   be written today.
4. ~~`docs/INDEX.md` §2 is stale.~~ ~~§4 Validation Status is absent.~~ **Both resolved
   2026-08-02.** §2 was rewritten against the code and §1 gained EQ-035–EQ-053; §4 then
   gained 18 rows covering the ~30 tasks it had never documented, including T-6.5/T-6.6.
   **Three findings from that pass remain open and two of them touch claims this
   manuscript makes.** (a) The `exp(−4σ²)` alignment law is quoted in the Abstract, the
   Main and Table 1 from ADR-0003's prototype measurement (~10⁻⁴ across σ ∈ [0°, 20°] at
   N = 100 and N = 1000), but the *committed test* asserts only abs 2 × 10⁻³ at N = 200
   over σ ≤ 10° — **the CI check is materially weaker and narrower than the figure the
   manuscript prints.** Either tighten the test to the ADR's figures or restate the claim.
   (b) ADR-0003's 1 × 10⁻¹⁴ analytic-TT agreement, quoted in the Main, exists **only in the
   scratch prototype** — no committed test pins an absolute analytic value, so as printed
   it is not reproducible from the repository. (c) `octupole_moment` claims a cross-check
   against ref. 4 eq. 302a that no test executes.
5. **EQ-040 must go through `researcher` before submission.** It cites ref. 5 eq. 4.22 for
   the e^(2iψ) rotation law — the same equation number EQ-004 cites for the TT projector —
   while its docstring self-labels the result as established physics. **The e^(2iψ)
   transformation is the Abstract's central assertion; its citation must be sound.**
6. **Reference 8** (DART) and any other `[complete]` marker need volume/page verification
   against the published record, not against memory.

***Non-expert summary:*** Six things that must be fixed before this can be submitted
anywhere, and two of them are substantive rather than administrative. The awkward pair: the
paper quotes a precision figure for the alignment requirement that is **better than what
our own automated tests actually check**, and it quotes an accuracy figure that currently
lives only in a scratch file rather than in the reproducible test suite. Both are exactly
the kind of gap this project's whole method exists to catch — found by our own audit, in
our own paper, about our own headline result. We either tighten the tests to match the
claims or soften the claims to match the tests; we do not print the better number and hope.
Separately, one citation supporting the Abstract's central assertion has not been
independently verified, and it must be before anyone reads this.
