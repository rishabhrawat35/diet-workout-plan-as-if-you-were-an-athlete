# Goals, and one check that cannot fail

Same discipline as MIGRATION.md: every step declares its diff before it runs,
the suite must stay green, and the snapshot must match the declaration. A step
that diffs when it declared none has failed and is recorded as a deviation.

Baseline: **90 tests, audit exits `[0, 1, 0]`**, documents as committed at
`e021331`.

## The problem being solved

`priorities: ["calves", "chest", "glutes"]` is one person's body written into a
field name. It cannot express "I want to run a half marathon", "I want a bigger
squat", "I want to lose fat", "I want nothing in particular", or two of those at
once. The fix is not more fields. It is one field that carries a goal's *shape*
rather than assuming everyone's goal is a muscle.

## What a goal is allowed to do

A goal may only ever tighten a bound. It may never loosen one. Every
goal-derived number enters as `max(general_floor, goal_floor)`, which is what
`priority_min_sets` already does. No goal reaches `life_stage_stop`,
`max_weekly_loss_kg`, the protein floors, `fat_floor_g`, `carried_hold_limit_h`,
`banned_movements`, `myths.BANNED` or `refer_out`. Step 23 makes this a test
rather than a paragraph.

## Steps

| # | Step | Expected diff | Status |
|---|---|---|---|
| 20 | Delete `blocks.problems`; move its invariants into a test over a profile sweep | function and its call removed, test count changes, no audit output or document change | done |
| 21 | `goals` replaces `priorities` | ledger wording in both documents, no number moves | done |
| 22 | `deficit` derived from the arithmetic instead of declared | example-b's protein floor falls from 1.9 to 1.6 g/kg; example-a and private-me unchanged | done |
| 23 | Monotonicity test: a goal may only add violations, never remove one | test count rises | done |
| 24 | Measure table reads the plan instead of naming two fixed lifts | measure row changes in both documents | done |
| 25 | Girth readout for a `size` goal, stated as unenforced | a line is added to both documents | done |

## Step 22 was re-declared before it ran

The first declaration said "none, if every profile's declared value already
matches". Checked before running, and one does not. example-b declares
`deficit: true` while its plan feeds 2293 calories against a TDEE of 1795 --
a 498 calorie surplus. The engine has been applying the deficit protein floor
of 1.9 g/kg to a profile that is gaining weight, because the field said so and
nothing compared the field to the arithmetic. That is the whole reason to
derive it, so the step proceeds with the honest declaration instead.

## The schema

```json
"goals": [
  {"want": "fat_loss"},
  {"want": "size",     "of": "calves"},
  {"want": "strength", "of": "leg press"}
]
```

`want` is a closed set. `of` names a muscle or an exercise that must resolve
against data the engine already holds, or the goal is refused at load, the way
`coherence.check_roles` already refuses an unknown food role. `goals: []` is
legal and means the person declared none; the document then says which
goal-derived checks did not run, so an empty list cannot read as personalisation.

No date field, no priority weight, no separate measurability field. Each would
be stored and never read, which is what `enhanced` was.

## Why goals are not a severity level

`severity.PRECEDENCE` ranks problems inside one plan. A goal is not a problem.
Two goals that pull against each other do not need resolving at the goal layer:
they contribute their own floors, and if the floors cannot all be met the
existing volume ceiling or session budget reports it as an ordinary `floor` or
`energy` violation. A conflict becomes a fact only when it makes some plan
undeliverable, and at that moment the engine already catches it.

## Log

| # | Suite | Diff | Matched declaration |
|---|---|---|---|
| 20 | 90 OK | `blocks.problems` removed, one test swapped for a 256-profile sweep. No audit or document change | yes |
| 21 | 90 OK | ledger wording in all three documents, no number moved | yes |
| 22 | 90 OK | example-b's protein floor 129 g -> 109 g; other two documents reworded only | yes, after re-declaration |
| 23 | 92 OK | test count rises by two | yes |
| 24 | 92 OK | measure row now names lifts read from the plan | yes |
| 25 | 92 OK | a goals section in every document, 24 of 24 contract sections | yes |

Final: **92 tests**, audit exits `[0, 1, 0]`.

## Two things caught mid-flight

**A validator that was about to become dead on arrival.** Step 21 added
`strength_goals` alongside `size_goals`. Nothing called it — the strength path
did not exist until step 24. The ledger coverage test refused the build, which
is the same mechanism that would have refused `enhanced` had it existed when
`enhanced` was written. The function was deleted and reintroduced in step 24
with a caller.

**A monotonicity test that could not fail.** Step 23's first version ran against
the two shipped profiles and asserted that adding a goal never removes a
violation. Proof attempt: plant a `fat_loss` goal that raises the loss-rate cap
to 99 kg a week, and see the test fail. It passed. Neither shipped profile trips
the loss cap, so there was no violation for the planted goal to remove — the
test was the same defect as the `blocks.problems` check deleted one step
earlier, written by the same hand on the same day.

The rewrite adds a stress case that does trip the cap, plus a second test that
fails if the baseline stops covering `safety`, `floor`, `energy` and
`distribution`. Both planted loosenings are now caught.
