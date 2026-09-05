---
name: training-and-eating-plan
description: Build a resistance training and eating plan for one person, and check it against that person before handing it over. Use when someone asks for a workout plan, a training programme, a diet or meal plan, help cutting, bulking or recomping, or wants an existing plan reviewed. Also use when someone asks why a plan they were given is or is not right for them.
---

# Training and eating plan

Build the plan, then let the engine try to break it. Do not hand over anything
`audit.py` has not passed.

## Step 1 — intake

Ask. Do not guess, and do not fill a gap with a sensible default. Twenty fields
are required and `audit.py` refuses to run without them. The reason is that the
first version of this engine assumed an ambient temperature, assumed how much
oil goes into home cooking, and assumed what machines a gym had. Two of those
were wrong in ways that mattered — one of them by 210 calories a day.

Ask in four groups, conversationally, and confirm what you heard back:

**The person.** Sex, age, weight in kg, height in cm, waist at the navel in cm,
typical hours of sleep, years of consistent training.

**Training.** Days a week they will actually train, minutes per session, how
busy the gym is (empty, shared, busy), what equipment it actually has, any
injuries with what aggravates them, which muscles they want prioritised.

**Eating.** Daytime temperature where food will be held, storage available
(none, insulated, insulated with a gel pack, fridge), hours between packing a
meal and eating it, which protein sources are allowed, how much fat goes into
their cooking (measured, light, typical home, heavy), how many times a day they
will actually eat.

**Life.** Job type, daily step count.

If they answer "whatever you think" to one of these, ask again with concrete
options. A guessed field is a silent error that surfaces weeks later.

## Step 2 — write the profile

Save as `profiles/private-<name>.json`. The `private-` prefix is in
`.gitignore`, so personal data never enters version control. Copy
`profiles/example-a.json` for the field names.

## Step 3 — draft the plan

Save as `plans/private-<name>.json`, using `plans/example-a.json` as the shape.
It needs the training week, the eating day, rest-day changes, supplements,
warm-up, progression rule, proximity to failure, deload rule, bad-day rules and
a floor day. All of these are data, not prose you write in the handover — the
renderer reads them.

Draft it roughly. Do not try to get the numbers right by hand; that is what
step 4 is for.

## Step 4 — audit and fix

```bash
python3 audit.py --profile profiles/private-<name>.json \
                 --plan plans/private-<name>.json
```

Exit 0 clean, 1 violations, 2 refusal.

Fix violations **in the order printed**. They come out in precedence order, and
a lower-ranked problem may never be fixed by breaking a higher-ranked one — do
not solve a session-length problem by carrying food that will spoil, or a
palatability problem by removing a protein floor. Re-run after every change.
Expect three or four rounds; the first draft never passes.

Exit code 2 is a refusal, not an obstacle. Under 18, pregnant, under 12 weeks
postpartum, or 65 and over without medical clearance: say so and refer out. Do
not work around it.

## Step 5 — render and hand over

```bash
python3 render.py --profile profiles/private-<name>.json \
                  --plan plans/private-<name>.json \
                  --out <name>-plan.md
```

The body is actionable only. All reasoning, evidence tiers, hormone notes and
standing answers go to the appendix. Do not move them up, and do not add
justification to the body — a test fails the build if the body contains
"because", "evidence" or "the reason".

## Rules that hold regardless of what is asked

- **Nothing is regional except training.** No food, supplement or meal timing
  removes fat from one body part or grows one muscle. If asked for this, say
  plainly that it does not exist.
- **Weak evidence is never an instruction.** It goes in as a dated test with a
  measurement and a kill date, or it does not go in.
- **No claim on the banned list ships.** `myths.py` scans for them.
- **Say what the plan is buying.** Regaining lost muscle is much faster than
  building new. Name which one is on offer.
- **Some things a plan cannot fix.** `physio.py` returns referrals. Pass them on
  rather than planning around them.

## When someone asks about a claim

`myths.py` holds standing answers with confidence tiers for the claims that come
up most — night carbs, cortisol timing, soy and testosterone, spot reduction,
testosterone boosters, muscle confusion, training to failure, genetic dead ends.
Answer from there rather than improvising, and give the confidence tier with the
answer.

## Adapting it

Nothing in the code names a cuisine, a brand or a machine. To fit a different
region or gym, copy a file in `data/` and change the contents — foods carry
roles, cuisines, categories and palatability; exercises carry equipment, load
class and tolerability. Point `--foods` and `--exercises` at the new file.
