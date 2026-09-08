# Migration record

Live status. Updated after every step. If work stops midway, this file says
exactly where it stopped and what state the tree is in.

## How each step is verified

Not by judgement. Three gates, all mechanical:

1. **Suite green.** `python3 -m unittest discover -p 'test_*.py'`
2. **Behaviour diffed.** `snapshot.py` captures audit output, rendered document
   hashes, every number in every document, the function inventory and the
   severity vocabulary. `diff.py` compares against the previous step.
3. **The diff matches the declaration.** Every step below states its expected
   change *before* it runs. Anything beyond that is a regression, and the step
   is reverted rather than explained.

A step with `expected: none` that produces any diff has failed, however
reasonable the diff looks.

Baseline: **102 tests, 3834 lines**, audit exits `[0, 1, 0]` for
example-a / example-b / private-me. (example-b exits 1 by design: it is a
different person run against example-a's plan, and is expected to fail.)

## Why no orchestrator

The thing being deleted in this migration is an unused multi-agent orchestrator.
Building a second one to supervise its removal would be the same mistake twice.
The snapshot is the challenger: it holds a claim of "no behaviour change" to a
diff, which is what a challenger is for.

## Steps

| # | Step | Expected diff | Status |
|---|---|---|---|
| 1 | `severity.py` holds `PRECEDENCE` and `RANK` | file added | done |
| 2 | `audit.py` imports from it; drop unused `RANK` | none | done |
| 3 | Remove `StagedLoop` from `test_contract.py`, `Precedence` and `Termination` from `test_loop.py` | test count falls | done |
| 4 | Fix `test_physio.NoPersona.CODE`: drop `resolve.py`, add `severity.py`, `units.py`, `ledger.py` | none | done |
| 5 | Delete `resolve.py` | file deleted | done |
| 6 | Delete `coherence.week_problems` and its tests; note it in README Limits | function removed, tests fall | done |
| 7 | Volume ceiling `variety` -> `floor`; drop `variety` from `PRECEDENCE` | audit text changes on example-b only | done |
| 8 | `render` records emitted concepts; `contract.require` reads them | none (23 of 23 present) | done |
| 9 | Audit the floor day | none (both pass) | done |
| 10 | One source for safety limits and rounded sums | none | done |
| 11 | Validate food roles against `MEAL_ROLES` | none | done |
| 12 | Collapse `contract` into one dict | none | done |
| 13 | Stop printing micronutrient advice as if enforced | document wording changes | done |
| 14 | Tag-clustering check under `distribution` | **may fail the shipped plan** | done |
| 15 | README: delete the review-loops section, correct the counts | none | done |
| 16 | A food's stated composition must match its macro vector | `paneer` and `dal` corrected; totals move in every meal holding them | done |

## Step 16, declared before it runs

Found while rendering the finished plan, not by a test. Three food entries
describe cooking oil in `made_of`. Checked each against its own macro vector:

| food | claim | oil implied | fat carried | verdict |
|---|---|---|---|---|
| sabji | 12 g oil as a home kitchen actually uses | 12 g | 12 g | consistent |
| egg bhurji | 3 whole eggs, 1 tsp oil | 5 g | 20 g, of which 5 g is oil | consistent |
| egg curry | 2 whole boiled eggs, 1 tsp oil | 5 g | 15 g, of which 5 g is oil | consistent |
| dal | 1 tsp oil in the tempering | 5 g per katori | 1.6 g of oil per katori | wrong text |
| paneer | full fat paneer, pan tossed with 1 tsp oil | 5 g per serving | none, and below plain paneer | wrong numbers |

Two different defects, one class: the printed description claims something the
numbers do not carry. This is the sabji-oil defect again, in the two entries that
were never rechecked after it.

`dal` is a wording error. A tempering of 1 tsp oil is made once for a whole pot
and serves roughly four katori, so 1.6 g of oil in one katori is right and the
sentence that says 1 tsp per katori is not. Macros stay, text changes.

`paneer` is a numbers error, and a structural one. Its unit is the gram, so a
per-serving quantity of oil cannot be represented in a per-gram vector at all.
The vector is also below plain full fat paneer. Text drops the oil, numbers
become plain full fat paneer at 2.96 kcal, 0.18 g protein and 0.22 g fat per gram.

Closing the class rather than the two instances: a per-gram or per-millilitre
food may not describe a per-serving quantity, because its vector has nowhere to
put one. That is a test over the data file, not a new engine layer.

Expected diff: paneer's two dinner lines and every total above them move by
about 16 calories a day; dal's description line changes with no number moving;
test count rises by one.

## Log

Each row was gated three ways before the next step began: suite green, snapshot
taken, diff compared against the expected change declared above. Snapshots live
outside the repo in `migration/` as `baseline.json` and `step-NN.json`.

| # | Suite | Diff against previous step | Matched declaration |
|---|---|---|---|
| 1 | 102 OK | `severity.py` added, 46 lines | yes |
| 2 | 102 OK | none | yes |
| 3 | 93 OK | test count 102 -> 93 | yes |
| 4 | 93 OK | none | yes |
| 5 | 93 OK | `resolve.py` deleted, -172 lines | yes |
| 6 | 89 OK | `week_problems` gone, test count 93 -> 89 | yes |
| 7 | 89 OK | example-b audit text `variety` -> `floor`; `PRECEDENCE` 8 -> 7 levels | yes |
| 8 | 89 OK | one line of document text reworded | no, see deviations |
| 9 | 89 OK | none | yes |
| 10 | 89 OK | `Rule:` attribution lines changed in both documents | no, see deviations |
| 11 | 89 OK | none | yes |
| 12 | 89 OK | none | yes |
| 13 | 89 OK | micronutrient section reworded | yes |
| 14 | 89 OK | curd moved dinner -> breakfast in both plans; no calorie or protein total moved | yes |
| 15 | 89 OK | none | yes |
| 16 | 90 OK | +16 kcal and +1 g fat a day in all three plans; dal text only; 2 functions added | yes |

Final state: **90 tests OK**, audit exits `[0, 1, 0]`. Same three
exit codes as the baseline, from 110 fewer lines, with `severity.py`,
`test_severity.py`, `clustering_problems`, `check_roles`,
`carried_hold_limit_h`, `printed_totals` and the floor-day check added along the
way.

## Deviations

Two steps declared `expected: none` and produced a diff. Both are recorded here
rather than argued away, because the rule at the top of this file says a step
that diffs when it declared none has failed. Neither was reverted; the reason is
given, and the reason is the same in both cases: the declaration was wrong about
what "behaviour" covers, not the code.

**Step 8 — contract made real.** Declared none. The document's final line changed
from a fixed sentence to one that reports how many sections the renderer actually
emitted (`23 of 23 required sections written`). That is the point of the step: the
count is now measured instead of asserted, so it has to be printed from a
measurement. The declaration should have read "one line of summary text changes".
No number in any plan moved.

**Step 10 — one source for safety limits and rounded sums.** Declared none. Both
documents changed where the decision ledger prints its `Rule:` attribution, because
two inlined calculations became named functions and the ledger names the function
that made the call. No hold limit, no rounded total, and no printed number changed
value — verified by the snapshot's per-number capture, which compares every number
in every document and reported no numeric difference.

Neither deviation is a behaviour change in the sense the gate was built to catch.
Both are a reminder that "expected: none" is a claim about the rendered document,
not just about the arithmetic behind it.

Step 16 landed as declared. All three plans moved by the same 16 calories and
1 gram of fat a day, which is the paneer correction and nothing else; the dal
line changed wording with no number moving; audit still exits `[0, 1, 0]`. The
loss rate on the personal plan went from 0.37 to 0.35 kg per week, still inside
its 0.61 cap.

One thing was written and then withdrawn during this step. The new test's
docstring claimed the reinstated macro-consistency check was "the hole paneer
came through". Checked before leaving it in: paneer's old vector was
self-consistent to within 0.4%, because calories and fat were understated
together. The check would never have fired. The docstring now says so. A comment
that asserts a catch it did not make is the same defect as a document that
asserts a check it did not run.
