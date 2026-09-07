# Output defects, and what has to change

Found by reading the rendered document rather than the code. Every one of these
passed all 71 tests, because no test looked at what the document actually said.

## The root cause

A food's key doubles as its display name, and the key has a quantity baked into
it: `roti 1 medium`, `egg white 1`, `paneer 100 g`, `rice cooked 1 katori`. A
multiplier is then applied on top. Two quantities in one string is what produces
every line below.

## What the reader sees

| # | Renders as | Should be | Cause |
|---|---|---|---|
| 1 | `egg bhurji, 3 whole eggs, 2 x roti 1 medium` | three separate items | food names contain commas; items joined with commas |
| 2 | `3 x egg white 1` | `3 egg whites` | quantity in the key, multiplier on top |
| 3 | `2 x roti 1 medium` | `2 roti` | same |
| 4 | `0.5 x rice cooked 1 katori` | `½ katori rice` | same, plus decimals for fractions |
| 5 | `0.5 x paneer 100 g` | `50 g paneer` | a gram weight cannot take a multiplier |
| 6 | `dal cooked 1 katori (toor, moong...)` | `dal (toor, moong...)` | key used as a category label |
| 7 | `6 x boiled egg 1` in the floor day | `6 boiled eggs` | same as 2 |

## What is missing

| # | Gap | Why it matters |
|---|---|---|
| 8 | No macros per food item | The reader cannot swap anything without guessing |
| 9 | No per-meal subtotal | No way to see where the day's calories sit |
| 10 | Nothing verifies items sum to the meal, or meals to the day | The only total shown is computed separately from the items |
| 11 | The rest day is prose, never audited | `audit.py` checks one day. Two of every seven days are unchecked. |
| 12 | Appendix explains formulas, not decisions | The reader learns how BMR works, not why they train five days |

## The changes

| Step | Change | Files |
|---|---|---|
| 1 | Split food key into name, unit, and macros per one unit | `data/foods-*.json` |
| 2 | Composite dishes carry an ingredient list, not a comma name | `data/foods-*.json` |
| 3 | Quantity formatter: fractions, grams, plurals | `render.py` |
| 4 | Per-meal macro table with item rows and subtotals | `render.py` |
| 5 | Arithmetic verification: items to meal to day to target | `audit.py` |
| 6 | Rest day becomes real data and gets audited | `plans/*.json`, `audit.py` |
| 7 | Key decisions, generated from the profile | `decisions.py`, `render.py` |
| 8 | Tests for every row above | `test_render.py` |

## Status

All twelve fixed and covered by tests in `test_render.py`, which reads the
rendered document rather than the numbers behind it. That is the gap that let
every defect above ship: 71 tests passed while the document said "3 x egg
white 1".

Found while fixing, not in the original list:

| Defect | Fix |
|---|---|
| Header said 218 g carbs, the table said 219 | One rounding pass feeds both |
| Rest day showed a training-day calorie target | Target row carries only the floors that apply to every day |
| `epa_dha`, `iron_heme` printed as labels | Reader-facing names in `PATTERN_RISK` |
| `typical_home`, `insulated_gelpack` printed in prose | Word tables in `decisions.py` |
| "Stop the deficit at 89.0 cm" | `:g` format |
| A moved food read as a deletion plus an addition | `rest_day_diff` detects moves |
| Rest day lost 20 g of protein when the whey was dropped | The scoop moves to 17:00 instead |
