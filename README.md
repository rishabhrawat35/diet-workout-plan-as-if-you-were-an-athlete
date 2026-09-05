# Trainer

Builds a resistance training and eating plan for one person, checks it against
that person, and refuses the cases an automated tool should not touch.

Python 3.8 or newer. No dependencies, no network, no API key.

```bash
python3 audit.py  --profile profiles/example-a.json --plan plans/example-a.json
python3 render.py --profile profiles/example-a.json --plan plans/example-a.json \
                  --out example-a-plan.md
python3 -m unittest discover -p 'test_*.py'   # 62 tests
```

No profile is the default. The engine will not run without being told whose
plan it is building.

Exit 0 clean, 1 violations in precedence order, 2 refusal.

## Why it is one engine and not two

Training and eating constrain each other. A deficit changes recovery capacity,
recovery capacity sets the deload interval, the deload interval sets the block
calendar, and the block calendar has to change what is eaten that week. Built
separately, the two halves contradict: the first version put a diet break at
week 12 and training deloads at weeks 11 and 18, so the person would have eaten
at maintenance during a hard week and dieted through an easy one.

## What it checks

Violations are ranked, and the ranking is the design. A lower-ranked constraint
may never be satisfied by breaking a higher-ranked one.

| Rank | Kind | Fails when |
|---|---|---|
| 0 | refusal | Life stage, a contraindicated movement, equipment the gym does not have |
| 1 | safety | Carried food held past its limit for that temperature and storage |
| 2 | floor | Protein, fat, fibre, priority volume, loss rate, missing deload or diet break |
| 3 | energy | Session longer than the time budget; macros not summing |
| 4 | coherence | A carrier with nothing wet; two heavy compounds back to back; one station overloaded |
| 5 | distribution | Too few sittings reach the per-sitting protein dose |
| 6 | variety | A slot identical every time with nothing to rotate within |
| 7 | palatability | A meal or session nobody will keep doing |

## What it refuses

Under 18, pregnant, under 12 weeks postpartum, 65 or over without recorded
medical clearance. Also any plan built from an incomplete intake: twenty fields
are required and the gate raises rather than warns.

## Files

| File | What it is |
|---|---|
| `physio.py` | All physiology. Energy, protein, recovery, volume, injuries, endocrine |
| `coherence.py` | Whether a meal is a meal and a session is doable |
| `blocks.py` | The 24-week calendar, and the rule that eating follows training |
| `contract.py` | The 23 sections a finished plan must contain |
| `myths.py` | Standing answers, and claims the engine may never emit |
| `resolve.py` | Precedence order and the staged agent/challenger loops |
| `audit.py` | Runs every check |
| `render.py` | Writes the document: actionable body, reasoning in an appendix |
| `data/` | Region and gym specifics. Swap the file, not the code |
| `profiles/`, `plans/` | Two example people. Anything named `private-*` is ignored by git |

## Adding a region or a gym

Nothing in the code names a cuisine or a machine. `data/foods-*.json` carries
roles, cuisines, categories and palatability; `data/exercises-*.json` carries
equipment, load class and tolerability. A vegan in Lagos and a pescatarian in
Lisbon need a new data file, not a code change.

## No persona in the engine

Nothing in the code is shaped around one individual. Supplements, warm-up,
progression, the deload rule, the bad-day rules and the floor day are plan
data, not renderer text, because they differ person to person. Two shipped
examples differ on sex, age, training age, days available, gym traffic,
climate, storage and injury, and produce different targets from the same code.
Four tests enforce this: no personal identifier in any module, no hardcoded
bodyweight or measurement, example profiles carry no real name, and a second
person runs end to end.

## Limits

- Body fat is estimated from waist and height. Every body-composition statement
  inherits that error.
- No alcohol, eating out, or social meals.
- No medication or medical condition layer. Thyroid, insulin resistance and
  several common drugs change energy and body composition. The engine is blind
  to all of them.
- Palatability and tolerability scores are estimates until the person replaces
  them with their own.
- Not medical advice.
