# Subtraction plan

## What "best" means here

The engine's only real differentiator is that it checks its own work. The food
data is commodity, the renderer is commodity. If the checking is not true, there
is nothing left.

So:

> **Best = the engine never makes a claim it has not checked.**

Four things follow, and they rank the work:

1. **A check that cannot fail is worse than no check.** It converts "unknown"
   into "verified" and nobody finds out.
2. **Code the README advertises but never runs is the same failure, aimed at a
   developer.** They grep, find it dead, and stop trusting the rest.
3. **Advice printed but not applied is the same failure, aimed at the reader.**
4. **Duplication is future silent wrongness.** Two copies of a number drift, and
   the plan starts contradicting its own explanation.

Ranked by who is hurt and whether they would notice:

| Failure | Hurts | Noticed? |
|---|---|---|
| A wrong number nobody checks | the person, for months | no |
| An unsafe instruction | the person, immediately | yes |
| A false assurance | the person, and anyone trusting them | no |
| Advertised code that is dead | a developer evaluating it | yes, and they discount everything else |
| Advice the plan contradicts | the person | sometimes |
| Verbosity | nobody | — |

Measured before planning: `audit.py` 54 ms, `render.py` 52 ms, 102 tests in
337 ms. **Nothing here is slow and none of this makes it faster.** Anyone
expecting a performance change will not get one.

## From the reader's side

They install a skill, answer twenty questions, and act on the result daily for
24 weeks. What they need is: is this safe, can I do it, do the numbers hold.

None of the dead code is visible to them. Two things are:

- The plan prints `23 required sections present` when nothing verified that.
- The plan prints `pair the plant sources with something containing vitamin C`
  and then builds a dinner that works against it.

## From the repository's side

The README sells "review loops that cannot get stuck" with a staged agent and
challenger design and a termination argument. That file is never called. The
first developer who greps for `stage_resolve` finds it is dead, and then has no
reason to believe the audit runs either.

That makes deleting it, and the README section, the highest-credibility item in
this plan even though it changes no behaviour.

## The dairy question, decided against the definition

Three dairy items at one dinner is roughly 600 to 700 mg of calcium. Single-dose
absorption falls off above about 500 mg, and calcium inhibits non-heme iron in
the same meal. This diet has no heme iron at all, and `sabji` rotates to palak.

The engine is not wrong because it failed to track calcium. It is wrong because
**it prints iron-absorption advice and then builds the meal that undermines it.**
That is failure mode 3.

Three ways to fix it:

| | Cost | Verdict |
|---|---|---|
| a. Stop printing advice the engine does not apply; say plainly it is not enforced | 2 lines | **Do this.** It removes an unbacked claim, which is the definition. |
| b. Add calcium and iron per food and check both scopes | 18 foods x 2 values, plus a scope concept the engine does not have | Not now. 36 numbers I cannot verify from here, and it reopens the scope question. |
| c. Flag one nutrient class concentrated in one sitting, using the tags that already exist | ~12 lines, no new data | **Do this.** It reuses `distribution`, which already means "a nutrient bunched instead of spread". |

(c) needs no threshold table: flag when a single meal holds more than half the
day's items of one tag class. Dinner holds 3 of 5 dairy items. Scale-free, no
new data, no new severity, no new concept.

What (c) does **not** claim: that this is harmful, or how many milligrams. It
reports a fact it can verify and leaves the significance to the appendix. That
is the definition applied to itself.

## Issues found while detailing, not in the first draft

| Issue | Consequence |
|---|---|
| `audit.py` imports `RANK` and never uses it | Dead import; deleting `resolve.py` breaks the line for no reason |
| `test_contract.py` holds a `StagedLoop` class, 6 tests | Deleting `resolve.py` breaks a file that also holds the live contract tests |
| `test_physio.NoPersona.CODE` lists `"resolve.py"` | The persona test opens every file in that tuple. Deleting the file makes it fail with FileNotFoundError, not a clear message |
| Nothing owns the severity vocabulary | `coherence`, `blocks` and `audit` all emit severity strings; only `audit` reads the order. After `resolve.py` goes, the order needs a home. |

So `resolve.py` is referenced by **five** files, not one. Deleting it in the
wrong order breaks the import chain and two test modules.

## The plan

Ordered so the tree is green after every step.

| # | Step | Files touched | Risk | Verified by |
|---|---|---|---|---|
| 1 | New `severity.py`: `PRECEDENCE`, `RANK`, 12 lines. Same content, honest name -- nothing in it resolves anything. | +1 file | none | imports |
| 2 | Point `audit.py` at it and drop the unused `RANK` import | audit.py | none | suite green |
| 3 | Delete `StagedLoop` from `test_contract.py`; delete `Precedence` and `Termination` from `test_loop.py`. Keep `Coherence`, `Categories`, `UnknownExercise`, `Completeness`. | 2 test files | **medium -- both files hold live tests** | count before and after |
| 4 | Remove `"resolve.py"` from `test_physio.NoPersona.CODE`, add `"severity.py"`, `"units.py"`, `"ledger.py"` which were never covered | test_physio.py | low | persona test still fails on a planted leak |
| 5 | Delete `resolve.py` | -172 | none once 1-4 land | suite green |
| 6 | Delete `coherence.week_problems` and the `Categories` tests; add a line to README Limits saying variety is not checked and why | coherence.py, test_loop.py, README | low | suite green |
| 7 | Relabel the volume ceiling from `variety` to `floor`. `variety` now has no producer: drop it from `PRECEDENCE`, 8 levels to 7. | audit.py, severity.py | low | no string in the codebase raises a severity absent from `PRECEDENCE` -- new test |
| 8 | `render` records each concept as it emits it; `contract.require` reads that set | render.py, contract.py | **medium -- goes live** | simulated: 23 of 23 present, passes today |
| 9 | Audit the floor day against the protein floor and the printed numbers | audit.py | low | both example people pass, verified |
| 10 | One source for the food-safety limits (`physio.carried_hold_limit_h`), one for the rounded sums (`units.printed_totals`) | physio, units, audit, ledger, render | **medium -- five files** | numbers identical before and after |
| 11 | Validate every food's `role` against `MEAL_ROLES` at load | coherence.py, audit.py | low | planted typo raises |
| 12 | Collapse `contract.DIET`/`TRAINING`/`SHARED` into `ALL` | contract.py | none | suite green |
| 13 | Stop printing micronutrient advice as if applied; say it is guidance | physio.py, render.py | none | wording |
| 14 | Add the tag-clustering check under `distribution` | coherence.py, audit.py | **medium -- may fail the shipped plan** | simulate first; if dinner fails, that is the check working and the plan changes |
| 15 | README: delete the review-loops section, update line counts and the severity table | README.md | low | no claim without code behind it |

Net roughly **-300 lines**, one new 12-line file, two decorative checks made
real, one new check that costs no new data.

## What will happen

**Runtime:** unchanged. Deleting code that never executed does not speed up code
that did.

**Today's plans:** steps 8, 9 and 11 are simulated as passing. Step 14 is not --
the dinner probably fails it, which is the point, and the fix is to move one
dairy item to another meal.

**Test count:** roughly 102 down to 90, then back up with the new checks.

## Deliberately not doing

- Per-meal nutrient scope. Still unexpressible. Easier to judge with 300 fewer
  lines around it.
- Generation. The engine grades plans, it does not write them. Three dairy items
  at dinner was a hand-authoring choice and step 14 only catches it after the
  fact.
