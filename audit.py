#!/usr/bin/env python3
"""
Run every check against a profile and a plan.

    python3 audit.py --profile profiles/example-a.json --plan plans/example-a.json

Exit 0 clean, 1 violations, 2 refusal. Violations are reported in precedence
order, so the first thing printed is always the thing to fix first.
"""
import argparse, json, sys
import physio, coherence, blocks, myths, units
from severity import PRECEDENCE

FREQ_EXEMPT = {"biceps", "triceps", "core", "delts"}


def load(path):
    with open(path) as f:
        return json.load(f)


def food_totals(items, foods):
    t = [0.0] * 5
    for name, qty in items:
        for i, v in enumerate(units.macros(qty, foods[name])):
            t[i] += v
    return t


def printed_totals(items, foods):
    """One home for this, in units.py. Kept as a name audit.py already used."""
    return units.printed_totals(items, foods)[:4]


def run(p, plan, foods, lib, acts=None):
    v = []

    stop = physio.life_stage_stop(p)
    if stop:
        print(f"REFUSED\n\n  {stop}\n")
        sys.exit(2)
    physio.require_context(p)
    coherence.check_roles(foods)
    coherence.check_composition(foods)
    physio.check_goals(p)
    physio.check_enums(p)
    if acts:
        physio.check_activities(p, acts)
        v += physio.activity_conflicts(p, acts)

    # ---- training volume
    sets, freq = {}, {}
    for day, exs in plan["week"].items():
        seen = set()
        for e in exs:
            m, n = e["muscle"], e["sets"]
            sets[m] = sets.get(m, 0) + n
            if m not in seen:
                freq[m] = freq.get(m, 0) + 1; seen.add(m)
            for s2 in e.get("also", []):
                sets[s2] = sets.get(s2, 0) + n * 0.5
                if s2 not in seen:
                    freq[s2] = freq.get(s2, 0) + 1; seen.add(s2)
    # The volume checks read plan["week"]; the calorie arithmetic reads
    # p["days"]. They were never compared, so a five-day plan audited at days=2
    # passed with zero violations while TDEE moved by 531 calories. Above 7 the
    # weekly average weights the rest day negatively and comes out above the
    # training-day total.
    if not 1 <= p["days"] <= 7:
        v.append(("refusal", f"days is {p['days']}; a week has 7."))
    elif len(plan["week"]) != p["days"]:
        v.append(("floor", f"The plan has {len(plan['week'])} training days but "
                           f"the profile says {p['days']} a week. The volume "
                           f"checks read the plan; the calorie target reads the "
                           f"profile."))
    v += coherence.rep_range_problems(plan["week"], p["age"])
    lo, hi = physio.volume_bounds(p)
    pmin = physio.priority_min_sets(p)
    goals = physio.size_goals(p)
    for m in sorted(sets, key=lambda x: -sets[x]):
        if m in FREQ_EXEMPT:
            continue
        pri = m in goals
        if freq[m] < 2 and pri:
            v.append(("floor", f"{m} is a priority trained {freq[m]}x/week."))
        if sets[m] > hi:
            v.append(("floor", f"{m} at {sets[m]:.1f} sets is past the {hi} set "
                               f"ceiling for this training age."))
    for pr in goals:
        if sets.get(pr, 0) < pmin:
            v.append(("floor", f"{pr} is a priority with {sets.get(pr,0):.1f} sets/week, "
                               f"under the {pmin} floor."))

    # ---- session coherence and length
    banned = physio.banned_movements(p)
    for day, exs in plan["week"].items():
        for e in exs:
            for bad, why in banned:
                if bad in e["name"].lower():
                    v.append(("refusal", f"{day}: {e['name']} -- {why}."))
        v += [(k, f"{day}: {m}") for k, m in
              coherence.session_problems(exs, lib, p["equipment"], p["minutes"])]
        n = sum(e["sets"] for e in exs)
        pr = sum(e["sets"] for e in exs if e.get("pair"))
        mins = physio.session_minutes(p, n, pr)
        if mins > p["minutes"] + 5:
            v.append(("energy", f"{day} needs ~{mins:.0f} min against a "
                                f"{p['minutes']} min budget ({n} sets at "
                                f"{physio.sec_per_set(p)} s)."))

    # ---- meal coherence, on every day the plan defines
    days = {"training day": plan["day"]}
    if "day_rest" in plan:
        days["rest day"] = plan["day_rest"]
    for label, day in days.items():
        for slot, items in day.items():
            v += [(k, f"{label}, {slot}: {m}") for k, m in
                  coherence.meal_problems([tuple(i) for i in items], foods)]
        v += [(k, f"{label}: {m}") for k, m in
              coherence.clustering_problems(
                  {s: [tuple(i) for i in it] for s, it in day.items()}, foods)]

    # ---- food safety
    limit = physio.carried_hold_limit_h(p)
    chilled = physio.chilled(p)
    for label, day in days.items():
      for slot, items in day.items():
        if "carried" not in slot:
            continue
        for name, _ in items:
            tags = foods[name]["tags"]
            if "perishable" not in tags:
                continue
            cap = limit if chilled or "cooked_rice" not in tags else min(limit, 4)
            if p["hold_hours"] > cap:
                v.append(("safety", f"{label}, {slot}: {name} held "
                                    f"{p['hold_hours']} h, safe limit {cap} h "
                                    f"at {p['ambient_c']} C."))

    # ---- macros, on every day, with the printed arithmetic checked
    #
    # Two passes, because the protein floor depends on whether the person is in
    # an energy deficit, and that is a fact about the whole week's eating. It
    # used to be a profile field an author set by hand, which meant the field
    # and the arithmetic could disagree and nothing objected: example-b declared
    # a deficit while its plan fed a 498 calorie surplus, and drew the deficit
    # protein floor anyway.
    t_ = physio.tdee(p, acts)
    day_totals = {}
    protein_per_sitting = {}
    for label, dd in days.items():
        tot = [0.0] * 5
        per = []
        for slot, items in dd.items():
            it = [tuple(i) for i in items]
            t = food_totals(it, foods)
            per.append(t[1])
            tot = [x + y for x, y in zip(tot, t)]
            # what a reader adding the printed column would get for this meal
            pk, pp, pfat, pc = printed_totals(it, foods)
            if abs(pk - t[0]) > 1.5 or abs(pp - t[1]) > 0.25:
                v.append(("energy", f"{label}, {slot}: the printed rows add to "
                                    f"{pk} kcal / {pp:g} g protein but the meal "
                                    f"total says {t[0]:.0f} / {t[1]:.1f}."))
        day_totals[label] = tot
        protein_per_sitting[label] = per
        for sev, msg in coherence.source_problems(dd, foods, p["protein_sources"]):
            v.append((sev, f"{label}, {msg}"))
        for sev, msg in coherence.occasion_problems(dd, p["eating_occasions"]):
            v.append((sev, f"{label}: {msg}"))

    in_deficit = physio.in_deficit(p, day_totals, t_)
    pf, pt = physio.protein_target_g(p, in_deficit)

    for label, tot in day_totals.items():
        kcal, prot, fat, carb, fib = tot
        per = protein_per_sitting[label]
        if prot < pf:
            v.append(("floor", f"{label}: protein {prot:.0f} g under the {pf} g floor."))
        if fat < physio.fat_floor_g(p):
            v.append(("floor", f"{label}: fat {fat:.0f} g under the "
                               f"{physio.fat_floor_g(p)} g floor."))
        if fib < physio.fibre_target_g(kcal) - physio.FIBRE_TOLERANCE_G:
            v.append(("floor", f"{label}: fibre {fib:.0f} g under the "
                               f"{physio.fibre_target_g(kcal)} g target."))
        if abs(prot * 4 + fat * 9 + carb * 4 - kcal) > 25:
            v.append(("energy", f"{label}: macros do not sum to the calorie total."))
        ok, reached, need, d = physio.distribution_ok(per, p)
        if not ok:
            v.append(("distribution", f"{label}: only {reached} sittings reach the "
                                      f"{d} g dose, need {need}."))

    # loss rate is judged on the weekly average, because the activity factor
    # already averages the training days in
    tr = day_totals["training day"][0]
    rs = day_totals.get("rest day", [tr])[0]
    n_train = p["days"]
    weekly = (tr * n_train + rs * (7 - n_train)) / 7
    if acts and any(g["want"] == "endurance" for g in p.get("goals", [])):
        mins = physio.aerobic_minutes(p, acts)
        if mins < physio.AEROBIC_FLOOR_MIN:
            v.append(("floor", f"An endurance goal with {mins} aerobic minutes "
                               f"a week, under the {physio.AEROBIC_FLOOR_MIN} "
                               f"minute public-health minimum."))
    ea, ffm = physio.energy_availability(p, weekly)
    if ea < physio.EA_FLOOR:
        v.append(("floor", f"Energy availability {ea} kcal per kg of fat-free "
                           f"mass a day, under the {physio.EA_FLOOR} floor "
                           f"(fat-free mass estimated at {ffm} kg). Raise "
                           f"calories or train less."))
    wk = (t_ - weekly) * 7 / 7700
    if wk > physio.max_weekly_loss_kg(p):
        v.append(("floor", f"Losing {wk:.2f} kg/week on the weekly average exceeds "
                           f"the {physio.max_weekly_loss_kg(p)} kg cap."))
    kcal, prot, fat, carb, fib = day_totals["training day"]

    # ---- the floor day, which the document states calories and protein for
    if "floor_day" in plan:
        fl = [tuple(i) for i in plan["floor_day"]]
        ft = food_totals(fl, foods)
        if ft[1] < pf:
            v.append(("floor", f"The floor day gives {ft[1]:.0f} g protein, under "
                               f"the {pf} g floor. It is the day someone falls back "
                               f"on, so it is the last one that should miss."))
        pk, pp, _, _ = printed_totals(fl, foods)
        if abs(pk - ft[0]) > 1.5 or abs(pp - ft[1]) > 0.25:
            v.append(("energy", f"The floor day's printed items add to {pk} kcal / "
                                f"{pp:g} g protein, not the {ft[0]:.0f} / {ft[1]:.1f} "
                                f"the document states."))

    # ---- calendar
    # blocks.problems used to run here. It checked the calendar that
    # blocks.build had just constructed, against properties build guarantees by
    # construction, so it could not fire: a sweep of 10,416 profiles raised
    # nothing. Those invariants are now asserted in test_physio.Blocks over the
    # same sweep, where a change to build is caught at test time instead.
    cal = blocks.calendar(p, day_totals["training day"][0], t_)

    # ---- claims
    lines = ([e["name"] for exs in plan["week"].values() for e in exs]
             + [n for items in plan["day"].values() for n, _ in items])
    for _, claim, line in myths.scan(lines):
        v.append(("refusal", f"Banned claim '{claim}' in: {line}"))

    # prot/carb/fib are not returned: day_totals already carries every one of
    # them per day, and the line that reprinted them said nothing the row above
    # had not already said.
    return v, dict(sets=sets, freq=freq, kcal=kcal, fat=fat,
                   in_deficit=in_deficit,
                   tdee=t_, cal=cal, loss=wk,
                   weekly=weekly, day_totals=day_totals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--foods", default="data/foods-india-egg-dairy.json")
    ap.add_argument("--exercises", default="data/exercises-home-gym.json")
    ap.add_argument("--activities", default="data/activities.json")
    a = ap.parse_args()

    p, plan = load(a.profile), load(a.plan)
    foods = {k: val for k, val in load(a.foods).items() if not k.startswith("_")}
    lib = {k: val for k, val in load(a.exercises).items() if not k.startswith("_")}
    acts = {k: val for k, val in load(a.activities).items() if not k.startswith("_")}

    v, s = run(p, plan, foods, lib, acts)
    print(f"AUDIT -- {p['name']}\n")
    print(f"  TDEE {s['tdee']:.0f}   weekly average intake {s['weekly']:.0f}   "
          f"loss {s['loss']:.2f} kg/wk (cap {physio.max_weekly_loss_kg(p)})")
    for lbl, t in s["day_totals"].items():
        print(f"  {lbl:14} {t[0]:>5.0f} kcal  {t[1]:>5.1f} g protein "
              f"({t[1]/p['kg']:.2f} g/kg)  {t[2]:>4.0f} F  {t[3]:>4.0f} C  {t[4]:>4.1f} fibre")
    print(f"  weekly sets: " + "  ".join(
        f"{m} {n:.0f}" for m, n in sorted(s["sets"].items(), key=lambda x: -x[1])))
    print()
    if not v:
        print("PASS  no violations")
        sys.exit(0)
    for k in PRECEDENCE:
        for kk, m in [x for x in v if x[0] == k]:
            print(f"{kk.upper():<13} {m}")
    sys.exit(1)


if __name__ == "__main__":
    main()
