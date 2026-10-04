"""
The programme calendar, and the rule that the diet must follow it.

This module exists because of a defect neither half could see alone. The
training plan had reintroduction, build, deload and push blocks across 24
weeks. The diet was one flat calorie number for all 24. So the diet break fell
at week 12 while the training deloads fell at weeks 11 and 18, meaning the
person would have eaten at maintenance during a hard week and dieted through a
deload -- the exact inverse of what either half intended.

A deload is a week of reduced training output. Holding calories there is what
makes it a recovery week rather than just an easier one.
"""

import physio


def build(p, weeks=24):
    """Blocks, with deloads placed at the person's own recovery interval and a
    diet break attached to one of them rather than floating free."""
    gap = physio.deload_every_weeks(p)
    brk = physio.diet_break_due_weeks(p)

    out, wk = [], 1
    if p.get("detrained") or p.get("injuries"):
        out.append({"from": 1, "to": 4, "kind": "reintroduction"})
        wk = 5

    run = 0
    while wk <= weeks:
        if run >= gap:
            out.append({"from": wk, "to": wk, "kind": "deload"})
            wk += 1
            run = 0
            continue
        span = min(gap - run, weeks - wk + 1)
        out.append({"from": wk, "to": wk + span - 1, "kind": "build"})
        wk += span
        run += span

    # Attach the diet break to the first deload at or after it is due, so the
    # eating week and the easy training week are the same week.
    target = None
    for b in out:
        if b["kind"] == "deload" and b["from"] >= brk:
            target = b
            break
    if target is None:
        target = next((b for b in reversed(out) if b["kind"] == "deload"), None)
    if target:
        target["diet_break"] = True
    return out


# Calories by block. The training plan changes what the body is doing; the diet
# has to change with it or the two halves contradict each other.
# What to do differently in each kind of week.
#
# Written because the calendar printed "reintroduction" for four weeks and
# "build" for the rest, and no instruction anywhere in the document differed
# between them. A block label the reader cannot act on is a claim the plan does
# not back. Every kind `build()` can emit must have an entry here, and a test
# fails the build if one does not.
#
# These are instructions to the reader, not constraints the audit can check: the
# plan holds one training week, and that week is the full-volume one. The
# document says so rather than implying the reduced weeks were audited too.
BLOCK_INSTRUCTION = {
    "reintroduction":
        "Do every exercise listed, at the sets listed, but stop each set with "
        "3 reps still in you rather than 1 or 2. Do not add weight during these "
        "weeks even if the reps feel easy.",
    "build":
        "Do every exercise listed, at the sets and reps listed, each set stopped "
        "1 or 2 reps short of form breaking. Add weight whenever an exercise hits "
        "the top of its rep range on every set for two sessions in a row.",
    "deload":
        "Do every exercise listed, at half the sets, at the same weight. Stop "
        "every set well short of hard.",
}


def break_kcal(base_kcal, tdee_kcal):
    """A diet break must feed MORE than the weeks it is a break from.

    This returned TDEE unconditionally. For anyone whose TDEE sits below the
    plan's calories -- the normal case for a smaller body handed a plan drafted
    for a bigger one -- the week labelled "eat at TDEE through the break" was
    the hungriest week of the programme. A 58 kg 72-year-old on a plan drafted
    at 2323 got 1444 in her break week and 2323 in every build week.
    """
    return round(max(base_kcal, tdee_kcal))


def kcal_for_block(kind, diet_break, base_kcal, tdee_kcal):
    if diet_break:
        k = break_kcal(base_kcal, tdee_kcal)
        why = ("maintenance: eat at TDEE through the break"
               if k > round(base_kcal) else
               "the plan already feeds at or above maintenance, so this week "
               "holds calories rather than raising them")
        return k, why
    if kind == "deload":
        # max() for the same reason break_kcal needs it: when the plan already
        # feeds at or above maintenance there is no deficit to halve, and
        # halving it arithmetically made the recovery week the hungriest week.
        k = round(max(base_kcal, tdee_kcal - (tdee_kcal - base_kcal) * 0.5))
        return k, ("half the usual deficit: training output is down, recovery "
                   "is the point" if k > round(base_kcal) else
                   "calories held: there is no deficit to ease here")
    if kind == "reintroduction":
        return round(base_kcal), "full target: the deficit starts on day one"
    return round(base_kcal), "full target"


def calendar(p, base_kcal, tdee_kcal, weeks=24):
    rows = []
    for b in build(p, weeks):
        kcal, why = kcal_for_block(b["kind"], b.get("diet_break"),
                                   base_kcal, tdee_kcal)
        rows.append({**b, "kcal": kcal, "note": why})
    return rows
