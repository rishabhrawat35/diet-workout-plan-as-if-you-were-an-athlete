# Trainer

**A training and eating plan that checks its own work before you see it.**

Most plans are written once and handed over. This one gets argued with first —
by code that knows what a plan for *you* should look like, and refuses to hand
over anything that fails.

---

## What you get

One document. The front is what you do: the week's training, the day's food,
supplements with timing, the 24-week calendar, what to measure and what to do
when the numbers move. Everything else — where each number came from, what the
evidence actually says, which popular claims are nonsense — is in an appendix
at the back, so the part you print and put on a desk stays instructions.

## What makes it different

**It refuses to guess.** Twenty things about you are required, and it will not
run without them. Not because it is fussy — because guessing is how plans go
wrong invisibly. It once assumed a teaspoon of oil went into home cooking when
the real answer was three. That single guess was 210 calories a day, which
would have halved the fat loss while the plan claimed otherwise.

**It knows a meal from a list of macros.** Two roti with boiled eggs and a raw
salad hits every nutritional target and is not a breakfast, because nobody eats
dry roti. The engine catches that. It catches the same class of mistake in
training: a day can hit its set count and still be undoable, because two heavy
lifts sit back to back or four exercises need the one cable machine.

**It puts safety above everything else.** Checks are ranked. Food safety
outranks convenience, convenience outranks enjoyment, and the engine is
structurally unable to fix a small problem by creating a bigger one.

**It will not sell you anything.** No food, supplement or meal timing removes
fat from one part of your body or grows one muscle. Nothing over the counter
raises testosterone in a man whose level is normal. Claims like these cannot
appear in a plan it produces — there is a scanner that blocks them.

**It tells you when to stop.** Every measurement comes with the trigger that
changes the plan, including the one that says the diet has done its job.

## What it will not do

Under 18, pregnant, under 12 weeks postpartum, or 65 and over without medical
clearance — it refuses and refers you to a person. It also flags things a diet
cannot fix and tells you to see a doctor instead of planning around them.

It does not know about your medications, your thyroid, or anything you eat
socially. It estimates body fat from a tape measure, which is rough. It is not
medical advice.

---

## Using it with Claude

This repo is a Claude skill. Put it where Claude looks for skills:

```
~/.claude/skills/trainer/
```

Then just ask — "build me a training and diet plan", "review my current
programme", "why is my plan telling me to do this". Claude reads `SKILL.md`,
walks you through the intake, drafts a plan, runs the audit, fixes what it
finds, and hands you the document. You do not touch a terminal.

Your answers are written to `profiles/private-you.json`, which git ignores. Your
personal details never enter version control.

## Using it yourself

Python 3.8 or newer. No dependencies, no network, no API key, nothing to
install.

```bash
python3 audit.py  --profile profiles/example-a.json --plan plans/example-a.json
python3 render.py --profile profiles/example-a.json --plan plans/example-a.json \
                  --out example-a-plan.md
python3 -m unittest discover -p 'test_*.py'
```

Exit 0 clean, 1 violations, 2 refusal. There is no default profile — the engine
will not run without being told whose plan it is building.

---

# For developers

## Why one engine and not two

Training and eating constrain each other. A deficit changes recovery capacity,
recovery capacity sets the deload interval, the deload interval sets the block
calendar, and the calendar has to change what is eaten that week. Built
separately the halves contradict: an earlier version put the diet break at week
12 and training deloads at weeks 11 and 18, so the person would have eaten at
maintenance through a hard week and dieted through an easy one.

## The precedence order is the design

Violations carry a rank. A lower-ranked constraint may never be satisfied by
breaking a higher-ranked one — this is enforced in `resolve.py`, not left to
whoever is fixing the plan.

| Rank | Kind | Fails when |
|---|---|---|
| 0 | refusal | Life stage, a contraindicated movement, equipment the gym does not have |
| 1 | safety | Carried food held past its limit for that temperature and storage |
| 2 | floor | Protein, fat, fibre, priority volume, loss rate, missing deload or diet break |
| 3 | energy | Session longer than the time budget; macros not summing |
| 4 | coherence | A carrier with nothing wet; two heavy lifts back to back; one station overloaded |
| 5 | distribution | Too few sittings reach the per-sitting protein dose |
| 6 | variety | A slot identical every time with nothing to rotate within |
| 7 | palatability | A meal or session nobody will keep doing |

`resolve.py` also holds the staged agent/challenger loops: each rank is settled
then frozen, so a later stage cannot reach backwards into an earlier one.
Termination is bounded by ranks × round cap regardless of how agents behave.

## Layout

| File | What it holds |
|---|---|
| `physio.py` | All physiology — energy, protein, recovery, volume, injuries, endocrine, the intake gate |
| `coherence.py` | Whether a meal is a meal and a session is doable |
| `blocks.py` | The 24-week calendar, and the rule that eating follows training |
| `contract.py` | The 23 sections a finished plan must contain |
| `myths.py` | Standing answers with confidence tiers, and claims that may never ship |
| `resolve.py` | Precedence order and the staged loops |
| `audit.py` | Runs every check |
| `render.py` | Writes the document: actionable body, reasoning in an appendix |
| `SKILL.md` | How Claude drives all of the above |
| `data/` | Region and gym specifics |
| `profiles/`, `plans/` | Two example people. Anything named `private-*` is ignored by git |

## Constraint checks and completeness checks

Every check in the first version asked *is this number legal*. None asked *is
this section present*. So violations were caught automatically and omissions
were not — supplements vanished between two drafts, post-workout feeding was
never addressed, the warm-up and the progression rule were never written down.
Each was found by a human reader, one at a time.

`contract.py` is the fix: 23 required sections, with a test that removes each one
individually and asserts the plan becomes undeliverable. Prose does not fail a
build; this does.

## Adding a region or a gym

Nothing in the code names a cuisine, a brand or a machine. `data/foods-*.json`
carries roles, cuisines, categories and palatability. `data/exercises-*.json`
carries equipment, load class and tolerability. A vegan in Lagos and a
pescatarian in Lisbon need a new data file, not a code change.

Same for the person: supplements, warm-up, progression, the deload rule, the
bad-day rules and the floor day are all plan data rather than renderer text,
because they differ person to person.

## Tests

```bash
python3 -m unittest discover -p 'test_*.py'    # 62 tests
```

Most exist because something shipped broken. The suite covers the intake gate
refusing on each field individually, the cooking-fat gap being large enough to
matter, food safety by temperature and storage, the diet break landing on a
deload, loop termination against oscillating and runaway agents, and four tests
asserting no individual's details appear anywhere in the engine.

## Limits

- Body fat is estimated from waist and height. Every body-composition statement
  inherits that error.
- No alcohol, eating out, or social meals.
- No medication or medical condition layer. Thyroid, insulin resistance and
  several common drugs change energy and body composition. The engine is blind
  to all of them.
- Palatability and tolerability scores are estimates until replaced with the
  person's own ratings.
- Not medical advice.
