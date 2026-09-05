#!/usr/bin/env python3
"""
Run every check against a profile and a plan.

    python3 audit.py --profile profiles/example-a.json --plan plans/example-a.json

Exit 0 clean, 1 violations, 2 refusal. Violations are reported in precedence
order, so the first thing printed is always the thing to fix first.
"""
import argparse, json, sys
import physio, coherence, blocks, myths, contract
from resolve import PRECEDENCE, RANK

FREQ_EXEMPT = {"biceps", "triceps", "core", "delts"}


def load(path):
    with open(path) as f:
        return json.load(f)


def food_totals(items, foods):
    t = [0.0] * 5
    for name, qty in items:
        for i, v in enumerate(foods[name]["u"]):
            t[i] += v * qty
    return t


def run(p, plan, foods, lib):
    v = []

    stop = physio.life_stage_stop(p)
    if stop:
        print(f"REFUSED\n\n  {stop}\n")
        sys.exit(2)
    physio.require_context(p)

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
    lo, hi = physio.volume_bounds(p)
    pmin = physio.priority_min_sets(p)
    for m in sorted(sets, key=lambda x: -sets[x]):
        if m in FREQ_EXEMPT:
            continue
        pri = m in p["priorities"]
        if freq[m] < 2 and pri:
            v.append(("floor", f"{m} is a priority trained {freq[m]}x/week."))
        if sets[m] > hi:
            v.append(("variety", f"{m} at {sets[m]:.1f} sets is past the {hi} ceiling."))
    for pr in p["priorities"]:
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

    # ---- meal coherence
    for slot, items in plan["day"].items():
        v += [(k, f"{slot}: {m}") for k, m in
              coherence.meal_problems([tuple(i) for i in items], foods)]

    # ---- food safety
    limit = {"fridge": 24, "insulated_gelpack": 8}.get(
        p["storage"], (6 if p["ambient_c"] < 22 else 4 if p["ambient_c"] < 27 else 2)
        + (2 if p["storage"] == "insulated" else 0))
    chilled = p["storage"] in ("fridge", "insulated_gelpack")
    for slot, items in plan["day"].items():
        if "carried" not in slot:
            continue
        for name, _ in items:
            tags = foods[name]["tags"]
            if "perishable" not in tags:
                continue
            cap = limit if chilled or "cooked_rice" not in tags else min(limit, 4)
            if p["hold_hours"] > cap:
                v.append(("safety", f"{slot}: {name} held {p['hold_hours']} h, "
                                    f"safe limit {cap} h at {p['ambient_c']} C."))

    # ---- macros
    day = [0.0] * 5
    per = []
    for items in plan["day"].values():
        t = food_totals([tuple(i) for i in items], foods)
        per.append(t[1]); day = [a + b for a, b in zip(day, t)]
    kcal, prot, fat, carb, fib = day
    pf, pt = physio.protein_target_g(p)
    if prot < pf:
        v.append(("floor", f"Protein {prot:.0f} g under the {pf} g floor."))
    if fat < physio.fat_floor_g(p):
        v.append(("floor", f"Fat {fat:.0f} g under the {physio.fat_floor_g(p)} g floor."))
    if fib < physio.fibre_target_g(kcal) - physio.FIBRE_TOLERANCE_G:
        v.append(("floor", f"Fibre {fib:.0f} g under the "
                           f"{physio.fibre_target_g(kcal)} g target."))
    if abs(prot * 4 + fat * 9 + carb * 4 - kcal) > 25:
        v.append(("energy", "Macros do not sum to the calorie total."))
    ok, reached, need, d = physio.distribution_ok(per, p)
    if not ok:
        v.append(("distribution", f"Only {reached} sittings reach the {d} g dose, "
                                  f"need {need}."))
    t_ = physio.tdee(p)
    wk = (t_ - kcal) * 7 / 7700
    if wk > physio.max_weekly_loss_kg(p):
        v.append(("floor", f"Losing {wk:.2f} kg/week exceeds the "
                           f"{physio.max_weekly_loss_kg(p)} cap."))

    # ---- calendar
    cal = blocks.calendar(p, kcal, t_)
    v += blocks.problems(cal, p)

    # ---- claims
    lines = ([e["name"] for exs in plan["week"].values() for e in exs]
             + [n for items in plan["day"].values() for n, _ in items])
    for _, claim, line in myths.scan(lines):
        v.append(("refusal", f"Banned claim '{claim}' in: {line}"))

    return v, dict(sets=sets, freq=freq, kcal=kcal, prot=prot, fat=fat,
                   carb=carb, fib=fib, per=per, tdee=t_, cal=cal, loss=wk)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--foods", default="data/foods-india-egg-dairy.json")
    ap.add_argument("--exercises", default="data/exercises-home-gym.json")
    a = ap.parse_args()

    p, plan = load(a.profile), load(a.plan)
    foods = {k: val for k, val in load(a.foods).items() if not k.startswith("_")}
    lib = {k: val for k, val in load(a.exercises).items() if not k.startswith("_")}

    v, s = run(p, plan, foods, lib)
    print(f"AUDIT -- {p['name']}\n")
    print(f"  TDEE {s['tdee']:.0f}  intake {s['kcal']:.0f}  "
          f"loss {s['loss']:.2f} kg/wk (cap {physio.max_weekly_loss_kg(p)})")
    print(f"  protein {s['prot']:.0f} g ({s['prot']/p['kg']:.2f} g/kg)  "
          f"fat {s['fat']:.0f} g  carb {s['carb']:.0f} g  fibre {s['fib']:.0f} g")
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
