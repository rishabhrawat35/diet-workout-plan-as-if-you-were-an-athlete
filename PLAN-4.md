# What the engine does not know about the person in front of it

Findings from two review passes, combined into one plan. Nothing here is built
yet. Every claim below was run, not reasoned about; the command that produced
each one is implied by the numbers quoted.

Baseline at the time of writing: 93 tests, three example profiles, audit exits
`[0, 1, 2]` for example-a / example-b / example-c-16.

## The one sentence

The engine is rigorous about arithmetic it can check and silent about who the
arithmetic is for. Every enforcement mechanism fires on something the code can
enumerate from itself — functions, severity strings, document sections — and
nothing enforces on the one axis that matters most, which is what the engine was
told about the person.

---

# Part 1 — Things that are wrong right now

Ordered by what would hurt someone.

## 1.1 Two safety refusals can be bypassed by leaving a key out

`pregnant: true` and `postpartum_weeks: 6` both refuse correctly when set. Both
keys absent returns `None` and the engine proceeds. Neither is in `REQUIRED`.
Neither is asked in SKILL.md's intake — the words appear only in the Step 4 note
explaining what exit code 2 means, which is read by whoever is running the
engine, not answered by the person.

README advertises both refusals to users.

`medically_cleared` behaves the opposite way: absent refuses. So of three
life-stage gates, one fails safe and two fail silent.

## 1.2 A person with no injuries cannot get a plan at all

`injuries: []` passes the audit with zero violations, then `render.py` raises
`contract.Incomplete: contraindicated`. The `contraindicated` section is marked
only when the ledger emits an Injuries entry, which happens only when something
was banned or unmapped. All three shipped profiles have injuries, so no test
catches it.

This blocks exactly the healthy beginner the engine should serve best.

## 1.3 A diet break can be the hungriest week of the programme

`blocks.kcal_for_block` returns `round(tdee_kcal)` for a diet break with no check
that the plan's base calories are below TDEE. Run a 72-year-old woman, 58 kg,
155 cm, TDEE 1444, against a plan drafted at 2323:

```
wk  5-9  build            2323 kcal
wk 10    deload           1444 kcal   <- labelled the diet break
wk 16    deload           1883 kcal
```

The week labelled "maintenance: eat at TDEE through the break" is an 879 calorie
cut, and the easy training weeks are the hungriest. Fires for anyone whose TDEE
sits below the plan's calories, which is the normal case for a smaller body
handed a plan drafted for a bigger one. It fires on shipped example-b.

## 1.4 The document states a volume floor it does not enforce

The appendix prints "10 to 22 sets per muscle per week". The shipped plan gives
triceps 5.5, quads 7, core 8, hamstrings 7 — four muscles under the floor it
prints, zero violations. `lo` is computed at `audit.py:60` and never used in a
check. The ceiling is enforced; the floor is decoration.

Decide one: enforce it, or stop printing it as a floor. Enforcing it fires
immediately on the shipped plan, which is the decision, not an obstacle.

## 1.5 `days` and the plan's actual day count need not agree

A five-day plan audited at `days` = 2, 3, 5 and 7 passes every time with zero
violations, while TDEE moves 2377 → 2908. A 531 calorie spread, silent. The
volume checks read `plan["week"]`; the calorie arithmetic reads `p["days"]`.

Related: `days` above 7 makes `(tr * n + rs * (7 - n)) / 7` weight the rest day
negatively, so the weekly average comes out above the training-day total.

## 1.6 Two required fields are read by nothing

`eating_occasions` and `protein_sources` are in `REQUIRED`, the audit refuses to
run without them, and no module reads either. A vegetarian's "no egg" is
collected, gated on, and ignored. `distribution_ok` counts the plan's own slots,
not `eating_occasions`.

## 1.7 Unknown enum values are accepted silently

`job: "nurse"` falls through to the desk multiplier with nothing said, then dies
with a bare `KeyError` in the ledger. Same for `gym_traffic` and `storage`, where
an unrecognised value silently takes the shortest food-safety limit.
`check_goals` and `check_roles` refuse unknown values loudly. The pattern exists
and is applied to two of five enums.

---

# Part 2 — The engine does not know it is talking to a woman

`sex` is read in exactly two places in the whole engine: the Mifflin constant in
`bmr`, and `healthy_bodyfat_range`. Both spell it `p.get("sex", "m")`. The
default is male.

## 2.1 What a woman is currently handed

| Section | What she gets |
|---|---|
| Hormones | Four paragraphs about her own testosterone, including "adipose tissue contains aromatase… losing the fat is the hormonal intervention" |
| See a doctor about | Empty. `refer_out` holds one referral and it is male chest tissue |
| Fat floor | Justified to her as "below it testosterone falls modestly" |
| Protein | 1.9 g/kg, from a finding the document itself describes as "stronger for men" |
| Myths | Soy and testosterone, testosterone boosters "in men" — printed for everyone |
| Left out on purpose | "…raises testosterone in a man whose level is normal" |

Example-b is a 52-year-old woman and she ships in the repo. She is the one the
engine most likely gets wrong, and she is the fixture.

Absent from the entire repository: menstrual, cycle, luteal, follicular,
menopause, perimenopause, contraception, bone density, osteoporosis, RED-S,
energy availability, amenorrhoea.

## 2.2 What the energy cap misses, for both sexes

Energy availability is intake minus training cost, per kg of fat-free mass. The
engine's only brake is a flat 0.75% of bodyweight a week, plus a 25%-of-TDEE line
that lives inside `androgen_factors` as prose rather than as a floor.

Across a sweep of plausible profiles, that cap permits a deficit deeper than 25%
of TDEE in 86% of female profiles and 56% of male. Matched pairs land within
0.6 kcal/kg of each other, so this is not a cap that is harsher on women — it is
a cap too loose for everyone. What differs by sex is the consequence: menstrual
function and bone in women, androgen output in men, and the engine has words for
only one of those.

Fat-free mass can be estimated from `cm` and `waist_cm`, which the engine already
holds, but with roughly 5 percentage points of error against DXA. That is good
enough for a flag with its number and error stated. It is not good enough for a
refusal.

## 2.3 One new field, not six

`menstrual_status`, required when `sex == "f"`, values: cycling, irregular,
absent_3_months_plus, hormonal_contraception, perimenopausal, postmenopausal.

It cannot be derived. Menopause spans roughly 45 to 55, so age misfires on a
52-year-old in both directions, and nothing in the existing 20 fields implies
amenorrhoea. Each value reaches a different existing category:

- absent_3_months_plus / irregular → referral, plus an intake floor until seen
- postmenopausal → bone-loading readout, bone-density referral, iron flag off
- cycling → Measure row reads weight against four weeks ago, not last week
- hormonal_contraception → exists so the amenorrhoea referral does not misfire

## 2.4 One thing that must move first

`render.py:247` marks the required `downside` section only when the literal
string "androgen" appears in a ledger entry. Any sex-aware rewrite of the hormone
section breaks the build until that hook keys on the entry's area instead.

---

# Part 3 — The engine barely knows it is talking to a 70-year-old

Render a cleared 70-year-old and a 30-year-old with the same body against the
same plan, and diff: **the training table is byte-identical.** 28 of 379 lines
differ, every one of them calories, protein or deload spacing.

## 3.1 What age changes, completely

`life_stage_stop` (under 18, 65+ clearance), `bmr`, `protein_target_g` (+0.2 g/kg
at 60), `dose_g` (0.55 vs 0.40 g/kg at 60), `deload_every_weeks` (5 weeks at 55),
`diet_break_due_weeks` (capped at 10 from 45). Nothing else.

## 3.2 Load cannot be checked, and that is the right answer

The plan file carries no weight for any exercise. A 72-year-old's plan saying
"5 × 5 at 100 kg" raises nothing, and the string prints verbatim into the
document.

An absolute-load check is not buildable: the engine never learns a 1RM or a
working weight, and asking at intake would be a guess from someone who has never
lifted. **Do not build it.**

What is buildable from data already present is the **rep range**, which is a
proxy for relative load. Setting every rep range in the shipped plan to 3-5
changes the audit output by not one line. A 3-rep set is near-maximal whatever is
on the bar, and `e["reps"]` is already a string the engine holds.

## 3.3 The rigidity that matters

`volume_bounds` keys on training age alone, with no age term. A 72-year-old with
20 years of training and a 30-year-old with 20 years get the identical 10-to-22
set window. A constructed 68-year-old man with one training year gets bounds of
(8, 20), so **20 sets of calves and 16 of back raise no objection at all**. His
only training complaint is clock time.

## 3.4 Personas and challengers, answered plainly

The engine's real personas are the files in `profiles/`. Its real challengers are
the test suite and the audit — the multi-agent orchestrator was deleted in an
earlier migration because nothing called it, and the snapshot diff replaced it.
That was the right call and it is not being reopened.

Current coverage: 30 m, 52 f, 16 m refusal fixture. **No shipped profile reaches
60.** So `protein_target_g`'s 60+ branch and `dose_g`'s 60+ branch have never run
through `audit.py` or `render.py` — only through a synthetic unit test.

Adding a 72-year-old woman and a 68-year-old man as fixtures is the single
cheapest change in this document. Constructing them is what exposed 1.3, 3.3 and
the testosterone-for-a-postmenopausal-woman line.

## 3.5 What older adults need, by existing category

| Item | Evidence | Category |
|---|---|---|
| Rep-range floor at 65+, so loads stay sub-maximal | strong | refusal |
| Age term in `volume_bounds` | moderate | floor |
| Balance, chair-rise, gait speed | strong clinically | unenforced readout in Measure |
| Bone density, fracture risk | strong clinically | referral — already works via unmapped injuries |
| Blood pressure, Valsalva, medications | strong clinically | referral — works, but intake never asks |
| Sarcopenia protein distribution | moderate | already live via `dose_g` |

The referral path needs no new code. It needs the intake to ask about conditions
and medications, not only "injuries with what aggravates them".

---

# Part 4 — Beyond the gym

The containment is not the ranking. It is a **closed activity library**, exactly
as `coherence` already refuses an exercise the library does not know.

## 4.1 What priority can honestly mean

Four candidates, judged against "the engine never makes a claim it has not
checked":

- **Ranked by what the goal needs** — rejected. To put swimming above running for
  fat loss the engine must assert one modality beats the other at matched energy
  cost. It holds no evidence table to check that against.
- **Ranked by what injuries permit** — rejected as a ranking, kept as a filter.
  Allowed/not-allowed is binary; calling two states a ranking is dressing up a
  filter. The filter is the valuable part.
- **Ranked by time cost** — rejected. Needs a budget field and means only
  "cheapest first".
- **Ranked by the person's own stated preference** — accepted. The one basis the
  engine never has to defend, because it is not the engine's claim. Same class as
  `cooking_fat` or `gym_traffic`.

The order must be *read* by something or it is `enhanced` again. It is read by
one rule: when the engine reports that activity has to come out — loss-rate cap
breached, or an injury refusal — it names the **last** item first.

## 4.2 The data model

`data/activities.json`, new, following the exercise library pattern:

```json
{
  "swimming, moderate":  {"met": 7.0, "aerobic": true,  "aggravates": []},
  "running, outdoor":    {"met": 9.8, "aerobic": true,
                          "aggravates": ["lumbar disc", "patellofemoral"]},
  "badminton, singles":  {"met": 7.0, "aerobic": false,
                          "aggravates": ["patellofemoral"]},
  "walking, brisk":      {"met": 4.3, "aerobic": true, "aggravates": [],
                          "in_steps": true}
}
```

Profile, one field, order is priority:

```json
"activities": [
  {"do": "swimming, moderate", "minutes": 30, "times": 3},
  {"do": "badminton, singles", "minutes": 45, "times": 1}
]
```

Weekly minutes is `minutes * times` and is therefore not stored. No plan key in
the minimal version — it would restate the profile.

## 4.3 The arithmetic has a right answer

`activity_factor` has two terms of different kinds. The steps term is a **price**
and it is accurate: 0.015 × BMR works out at about 26.5 kcal per 1000 steps
against a real cost near 29. The `days` term is a **band**, not a price: 0.06 ×
BMR credits one session with 742 kcal a week against a real 250 to 400.

**Today** three 30-minute swims contribute nothing. Their real cost at 7 METs is
108 kcal/day, so TDEE is understated by 4%, the true loss is 0.46 kg/week while
the document prints 0.37, and nothing fires because both sit under the cap.

**If an author folds swims into `days`** (5 → 8) the factor credits 319 kcal/day
against a true 108 — a 211 kcal/day error, the same size as the cooking-oil
defect this project already memorialises. And `days` above 7 breaks the weekly
average outright.

**So price it additively**, keeping the honest term honest:

```python
def activity_kcal(p, acts):          # kcal/day, averaged over the week
    return sum((acts[a["do"]]["met"] - 1) * 3.5 * p["kg"] / 200
               * a["minutes"] * a["times"]
               for a in p.get("activities", [])
               if not acts[a["do"]].get("in_steps")) / 7
```

`met - 1` removes the resting metabolism already inside BMR. `in_steps` keeps
walking out, because the steps term already prices it.

This makes an **existing** check fire on new input, which is the cheapest
possible integration: example-a has 258 kcal/day of headroom before the loss-rate
cap. Swimming 3 × 30 adds 108 and passes. Running 5 × 45 adds 396 and trips it.

The weak joint, stated: the MET value is self-reported effort dressed as a
constant. Someone swimming gently at 5 METs is priced at 7. The mitigation is
that the ledger prints the MET, the minutes and the resulting calories, so the
reader sees the figure that moved their target.

## 4.4 Endurance becomes half-real

`GOAL_EFFECT["endurance"]` currently buys one honest sentence saying nothing was
planned. With activities present it can become a floor: an endurance goal
requires at least 150 aerobic minutes a week — the WHO and ACSM public-health
minimum, a figure with a source rather than one the engine invented.

What it must say out loud: 150 minutes is a health minimum and does not deliver a
stated event.

Interference stays an instruction, not a check. The engine's real coupling
between cardio and lifting is energetic, not volumetric, and that is already
policed by the loss-rate cap. A volumetric threshold has no citable table, so it
would be the engine asserting.

---

# The plan

Four phases. Each step declares its diff before it runs, the suite stays green,
and the snapshot must match the declaration — the discipline from MIGRATION.md
and PLAN-3.md.

## Phase 1 — Stop the bleeding (small, no new concepts)

| # | Change |
|---|---|
| 1 | Gate `pregnant`, `postpartum_weeks`, `detrained`, `gym_traffic`, `chest_tissue_unassessed`; add the questions to SKILL.md |
| 2 | Let an injury-free person get a document |
| 3 | Fix the diet-break inversion: never label a week a break if it feeds less than the build weeks |
| 4 | `days` must match the plan's day count, and may not exceed 7 |
| 5 | Refuse unknown enum values for `job`, `storage`, `gym_traffic`, `cooking_fat` |
| 6 | Decide the volume floor: enforce it or stop printing it |

## Phase 2 — The structural fix

| # | Change |
|---|---|
| 7 | A test that `REQUIRED` and "profile keys the code reads" agree in both directions, mirroring the ledger coverage mechanism. Fires today on six ungated keys and two unread ones |

Without this, phase 1 item 1 is a patch and the same bug returns.

## Phase 3 — Who the person is

| # | Change |
|---|---|
| 8 | Move the `downside` contract hook off the word "androgen" (prerequisite) |
| 9 | `androgen_factors` becomes `hormone_factors`, branching on sex and life stage. Male branch kept verbatim |
| 10 | `menstrual_status`, required when `sex == "f"`, wired to referral / floor / readout as in 2.3 |
| 11 | Energy-availability flag with its number and error stated. A flag, not a refusal |
| 12 | Condition the iron readout; stop `leafy_greens` silencing the calcium flag |
| 13 | `pelvic floor` into `INJURY_MAP` beside the existing hernia entry |
| 14 | Age term in `volume_bounds`; rep-range floor at 65+ |
| 15 | Two new fixtures: a 72-year-old woman and a 68-year-old man |
| 16 | Intake asks about conditions and medications, not only injuries |

Item 15 is the cheapest change here and should land first in this phase — it is
what makes the rest visible.

## Phase 4 — Beyond the gym

| # | Change |
|---|---|
| 17 | `data/activities.json`, closed library |
| 18 | `activities` profile field, ordered |
| 19 | `physio.activity_kcal`, added to TDEE additively, narrated in the ledger |
| 20 | Two checks: unknown activity refused; declared activity against injuries refused |
| 21 | Endurance goal becomes a 150-aerobic-minute floor |
| 22 | One document section listing activities in the person's own order, with the energy each contributes |
| 23 | A rest-day section: what to do on a day with no session, printed as an unenforced instruction |

---

# Rejected, with reasons

Kept here so nobody proposes them again.

- **An absolute load check.** No input exists. The engine never learns a working
  weight and asking would be a guess.
- **A conditioning field** ("I am unfit"). Changes no number. It would be
  `enhanced` again. What the person means is already expressible as `detrained`
  plus `days` plus `training_age_yrs` — once `detrained` is actually asked.
- **A numeric priority field on activities.** Derivable from array position.
- **A stored weekly-minutes figure.** `minutes × times`.
- **A geriatric severity level.** Severity ranks problems inside one plan.
  Everything here lands in refusal, floor, energy or referral already.
- **A sex term in `volume_bounds`, `deload_every_weeks`, `dose_g` or
  `fluid_ml`.** Evidence weak; the first two already move on age, training age
  and sleep, and the last two already scale on bodyweight.
- **Lowering the protein floor for women.** The sex moderator is real at moderate
  evidence; overshooting at these intakes is not harmful at strong evidence. Fix
  the sentence, not the number.
- **A bone-loading floor.** Every lower-body day this engine produces already
  satisfies it. It fired on neither example. Readout only.
- **A dedicated contraception field.** Weak and conflicting evidence, and weak
  evidence may not become an instruction. It earns one *value* inside
  `menstrual_status`.
- **A power-training library field.** No shipped exercise would carry it.
- **An axial-load or barbell flag.** The shipped library has no barbell, so it
  could not fire against shipped data.
- **A volumetric cardio-interference threshold.** No citable table.
- **Three rest-day checks** (steps floor, intensity keyword scan, activity-factor
  comparison). None can fire.


---

# Executed

All four phases landed. 95 tests, up from 93. Five example profiles, up from
three. 26 contract sections, up from 24.

| Phase | Items | Result |
|---|---|---|
| 1 | Gate the ungated fields; injury-free person; diet-break inversion; days vs plan; enum refusals; volume floor wording | all six, each refusal proven to fire |
| 2 | REQUIRED vs keys-the-code-reads, both directions | proven to fire both ways |
| 3 | Contract hook off "androgen"; sex-aware hormone_factors; menstrual_status; energy availability; iron and calcium; pelvic floor; age in volume_bounds; rep-range floor at 65; two geriatric fixtures; intake rewritten | all landed |
| 4 | Activity library; activities field; additive calories; two activity checks; endurance floor; activity and rest-day sections | all landed |

## What changed beyond the plan, and why

**The deload branch had the same inversion as the diet break.** Fixing only the
break left the recovery weeks feeding 1883 against build weeks at 2323 for the
same 72-year-old. Both branches now take `max(base, ...)`.

**`postpartum_weeks: 0` is not "not applicable".** The first version of the
field used 0 for "no", and the refusal fired on the fixture, correctly: zero
weeks postpartum is the most vulnerable week there is. The field now takes
`false` for "not recently" and a number for weeks.

**The two pregnancy fields are asked of women only.** Requiring a man to
declare he is not pregnant is noise, and noise in an intake script is how
questions stop being asked. `physio.required_for` makes the gate sex-aware.

**`check_activities` raises; `activity_conflicts` reports.** The first version
reported an unknown activity as a violation, and then `activity_kcal` crashed on
it before the violation could be read. An activity the library has never heard
of is a data error in the same class as an unknown goal, so it raises. An
activity an injury rules out is a judgement about this plan, so it reports.

**The volume floor was removed from the document, not enforced.** Enforcing 10
sets on every muscle would add sets to triceps and calves purely to reach a
number. The appendix now states the cap as the rule and the lower figure as the
useful range, and says why a muscle worked indirectly can sit below it.

**`peri_workout` depends on a slot-naming convention.** The 72-year-old's plan
failed the contract until a meal was named "after training". The convention was
stated nowhere; it is now in SKILL.md step 3, with the `day_rest` requirement.

**The 72-year-old needed three attempts to pass.** First attempt fed her a 681
calorie surplus. Second met the calories but missed the 60-plus per-sitting
protein dose. Third met both and then her hill walking raised her TDEE, pushing
her into a deficit and raising her protein floor to 122 g. That sequence is the
engine working: a 58 kg 72-year-old on a plan drafted for an 80 kg man is a hard
case, and every objection it raised was correct.
