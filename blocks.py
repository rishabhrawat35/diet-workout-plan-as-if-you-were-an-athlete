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
def kcal_for_block(kind, diet_break, base_kcal, tdee_kcal):
    if diet_break:
        return round(tdee_kcal), "maintenance: eat at TDEE through the break"
    if kind == "deload":
        return round(tdee_kcal - (tdee_kcal - base_kcal) * 0.5), \
               "half the usual deficit: training output is down, recovery is the point"
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


def problems(rows, p, weeks=24):
    out = []
    kinds = [r["kind"] for r in rows]
    if "deload" not in kinds:
        out.append(("floor", "No deload anywhere in the programme."))
    if (p.get("detrained") or p.get("injuries")) and "reintroduction" not in kinds:
        out.append(("floor", "Detrained or injured, but no reintroduction block."))
    if not any(r.get("diet_break") for r in rows):
        out.append(("floor", "No diet break in a programme this long."))
    for r in rows:
        if r.get("diet_break") and r["kind"] != "deload":
            out.append(("coherence", f"Diet break at week {r['from']} does not "
                        f"coincide with a deload."))
    gap = physio.deload_every_weeks(p)
    run = 0
    for r in rows:
        span = r["to"] - r["from"] + 1
        if r["kind"] == "deload":
            run = 0
        elif r["kind"] != "reintroduction":
            run += span
            if run > gap:
                out.append(("floor", f"{run} straight hard weeks by week "
                            f"{r['to']}, against a {gap} week limit."))
    total = sum(r["to"] - r["from"] + 1 for r in rows)
    if total != weeks:
        out.append(("coherence", f"Blocks cover {total} weeks, not {weeks}."))
    return out
