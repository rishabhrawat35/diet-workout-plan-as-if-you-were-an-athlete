# Execution plan

Written before any code changed. Each requirement quotes the request, states the
change, and states the test that proves it. Nothing is marked done without its
test passing.

## Requirements

| # | Asked for, in the requester's words | Change | Proven by |
|---|---|---|---|
| R1 | "the user should be able to see a summary table just like before with the right data" | Body keeps the two-column Time / Food table. Day totals stay on the header line above it. | A test asserts the body contains exactly one food table and that its header row is `Time \| Food`. |
| R2 | "in appendix we can have the detailed table again for reference" | The itemised macro table moves below the `# Appendix` line. | A test asserts the itemised table appears after `# Appendix` and that no itemised table appears before it. |
| R3 | "where is the appendix with imp decisions" | Already built and rendering. Confirm its location rather than rebuild it. | Section present, 8 entries, page 6 of the PDF. |
| R4 | "have we created system to build that out while the engine is making decisions based on users inputs?" | Replace re-derivation with a recorded log. | A test asserts every rule in `physio.py` is narrated, and fails when a rule is added without one. |

## R4 in detail

### The problem with what exists

`decisions.py` re-derives decisions at render time from the profile. Three
consequences:

- It reports only decisions someone wrote a paragraph for. A rule with no
  paragraph is silently absent.
- It cannot report what was rejected, which is the part worth reading.
- A rule can be changed without its explanation changing, and nothing notices.

### The design

`ledger.py` holds one narrator per decision point. The narrator calls the pure
rule, then records what was chosen, what forced it, and what the answer would
have been under different inputs.

The rules in `physio.py` stay pure and untouched. Purity is what makes them
testable, and a rule that writes to a log while computing is harder to trust,
not easier.

What makes this a record rather than a reconstruction is the coverage test:

    every public rule in physio.py must appear in ledger.NARRATED

Adding a rule without narrating it fails the build. That is the mechanism the
old design lacked -- not the storage, the enforcement.

### What gets recorded

| Field | Meaning |
|---|---|
| `area` | energy, protein, recovery, volume, injuries, logistics, calendar |
| `chose` | the value the plan uses |
| `because` | the input that forced it, in the person's own numbers |
| `rejected` | what it would have been under different inputs, and why that does not apply |
| `rule` | the function that decided, so a reader can go and read it |

`audit.py` also records the violations it raised during the run, so a plan that
needed three passes can show what changed and why.

## Order of work

1. R1 and R2 together. They are one move.
2. R4: `ledger.py`, then wire `render.py` to it, then delete `decisions.py`.
3. Coverage test, then the rest of the tests.
4. Re-render both example people and the private plan; read the output.
5. Report against each acceptance criterion above, one line each.

## Not doing

- Changing any number, food, exercise or threshold. This is a presentation and
  provenance change only. If a number moves, that is a bug in this work.
