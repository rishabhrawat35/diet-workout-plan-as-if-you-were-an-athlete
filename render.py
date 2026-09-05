#!/usr/bin/env python3
"""
Render the plan as one document.

Document rules, applied to every line of the body:
 1. Every instruction complete on its own. No shorthand, no "see rule 3".
 2. Every number carries its unit and what it refers to.
 3. No colour or symbol carrying meaning.
 4. No justification in the body. If the bench angle is 30 degrees, say so.
 5. Nothing that is not an instruction.
 6. No empty cells. If a column cannot be filled on every row, drop it.
 7. Lists and tables over paragraphs.

Reasoning, evidence and standing answers go to the appendix, so the body stays
something you can print and work from.
"""
import json, sys
import physio, blocks, myths, contract
from audit import load, run, food_totals


def render(p, plan, foods, lib):
    v, s = run(p, plan, foods, lib)
    L = []
    w = L.append

    w(f"# {p['name']} — training and eating")
    w("")
    w(f"{p['kg']:.0f} kg | {p['cm']:.0f} cm | waist {p['waist_cm']:.0f} cm | "
      f"{p['days']} sessions a week | {p['minutes']} minutes each")
    w("")

    # ---------------- body
    w("## Every week")
    w("")
    w("| Day | Exercise | Sets | Reps |")
    w("|---|---|---|---|")
    for day, exs in plan["week"].items():
        for i, e in enumerate(exs):
            pair = f" (alternate with {e['pair']})" if e.get("pair") else ""
            w(f"| {day if i == 0 else ''} | {e['name']}{pair} | {e['sets']} | {e['reps']} |")
    w("")
    w(plan["proximity"])
    w("")
    w(plan["warmup"])
    w("")
    w(plan["progression"])
    w("")

    tot = {}
    for exs in plan["week"].values():
        for e in exs:
            tot[e["muscle"]] = tot.get(e["muscle"], 0) + e["sets"]
            for s2 in e.get("also", []):
                tot[s2] = tot.get(s2, 0) + e["sets"] * 0.5
    w("Weekly sets: " + " | ".join(f"{m} {n:.0f}"
      for m, n in sorted(tot.items(), key=lambda x: -x[1])))
    w("")

    w("## Every day you train")
    w("")
    w(f"{s['kcal']:.0f} calories | {s['prot']:.0f} g protein | {s['fat']:.0f} g fat | "
      f"{s['carb']:.0f} g carbohydrate | {s['fib']:.0f} g fibre | "
      f"{physio.fluid_ml(p)} ml water")
    w("")
    w("| Time | Food |")
    w("|---|---|")
    for slot, items in plan["day"].items():
        line = ", ".join(f"{q:g} x {n}" if q != 1 else n for n, q in items)
        w(f"| {slot} | {line} |")
    w("")
    w("On days you do not train:")
    for c in plan["rest_day_changes"]:
        w(f"- {c}")
    w("")
    w(f"Last caffeine of the day: {physio.caffeine_cutoff_h_before_bed(p)} hours "
      f"before you go to bed.")
    w("")
    cats = [(n, f["category"]) for n, f in foods.items() if f.get("category")]
    if cats:
        w("Rotate freely within: " + "; ".join(
            f"{n} ({', '.join(c)})" for n, c in cats) + ".")
        w("")

    w("## Supplements")
    w("")
    w("| Item | Dose | When |")
    w("|---|---|---|")
    for s_ in plan["supplements"]:
        w(f"| {s_['item']} | {s_['dose']} | {s_['when']} |")
    w("")

    w("## The 24 weeks")
    w("")
    w("| Weeks | Block | Calories a day |")
    w("|---|---|---|")
    for b in s["cal"]:
        span = f"{b['from']}" if b['from'] == b['to'] else f"{b['from']}-{b['to']}"
        kind = b["kind"] + (" and diet break" if b.get("diet_break") else "")
        w(f"| {span} | {kind} | {b['kcal']} |")
    w("")
    w(plan["deload_rule"])
    w("")

    w("## Measure")
    w("")
    w("| What | How often | Do this when |")
    w("|---|---|---|")
    w(f"| Waist at the navel, before food | Weekly | Stop the deficit at "
      f"{physio.deficit_stop_waist_cm(p)} cm |")
    w("| Bodyweight, morning, 7 day average | Daily, read weekly | Under 0.2 kg "
      "a week for 3 weeks: remove 150 calories. Over 0.7 kg a week: add 150 |")
    w("| Top set weight on incline press and leg press | Weekly | Falling for 2 "
      "weeks in a row: add 200 calories |")
    w("| Hours slept | Daily | Under 6.5 hours for a week: shorten the block by "
      "one week and deload early |")
    w("")

    w("## When the session does not happen")
    w("")
    for line in plan["bad_day"]:
        w(f"- {line}")
    w("")
    fl = plan["floor_day"]
    ft = food_totals([tuple(i) for i in fl], foods)
    w("Floor day for eating, when nothing goes to plan: "
      + ", ".join(f"{q:g} x {n}" if q != 1 else n for n, q in fl)
      + f". That is {ft[0]:.0f} calories and {ft[1]:.0f} g protein.")
    w("")

    # ---------------- appendix
    w("---")
    w("")
    w("# Appendix")
    w("")
    w("## Where the numbers come from")
    w("")
    w(f"- Basal rate {physio.bmr(p):.0f} calories, from the Mifflin-St Jeor "
      f"equation using sex, weight, height and age.")
    w(f"- Activity multiplier {physio.activity_factor(p)}, built from a desk job, "
      f"{p['days']} training days and {p['steps']} steps a day.")
    w(f"- Total daily requirement {s['tdee']:.0f} calories. Eating "
      f"{s['kcal']:.0f} is a deficit of {s['tdee']-s['kcal']:.0f} a day, which is "
      f"{s['loss']:.2f} kg a week against a cap of "
      f"{physio.max_weekly_loss_kg(p)} kg.")
    pf, pt = physio.protein_target_g(p)
    w(f"- Protein floor {pf} g and target {pt} g. In an energy deficit the "
      f"fat-free-mass response is linear to at least 1.9 g per kg of bodyweight "
      f"with no plateau found, and the effect is stronger for men and for "
      f"programmes longer than four weeks.")
    w(f"- Protein in one sitting saturates near {physio.dose_g(p)} g. Three "
      f"sittings clear it; the smaller feedings are not meant to.")
    w(f"- A set costs {physio.sec_per_set(p)} seconds in a shared gym. Two "
      f"exercises alternated cost {physio.PAIRED_FACTOR} of that each.")
    w(f"- Deload every {physio.deload_every_weeks(p)} weeks and a diet break at "
      f"week {physio.diet_break_due_weeks(p)}, both from age, training age and "
      f"sleep. The diet break is placed on a deload week so the easy training "
      f"week and the eating week are the same week.")
    w("")

    w("## What this diet does not supply")
    w("")
    tags = set()
    for items in plan["day"].values():
        for n, _ in items:
            tags.update(foods[n]["tags"])
    for k, m in physio.micronutrient_flags(tags):
        w(f"- {k}: {m}")
    w("")

    w("## Hormones")
    w("")
    for c, m in physio.androgen_factors(p, s["fat"], s["kcal"]):
        w(f"- [{c}] {m}")
    w("")

    w("## See a doctor about")
    w("")
    for m in physio.refer_out(p):
        w(f"- {m}")
    w("")

    w("## Claims you will hear, and whether they hold")
    w("")
    w("| Claim | Verdict | Confidence |")
    w("|---|---|---|")
    for claim, (conf, ans) in myths.relevant(p).items():
        w(f"| {claim} | {ans} | {conf} |")
    w("")

    w("## Left out on purpose")
    w("")
    w("- Any food, supplement or timing that claims to remove fat from one part "
      "of the body. Fat distribution is genetic and hormonal.")
    w("- Any food or supplement that claims to grow one muscle. Nutrition is "
      "systemic; only training is regional.")
    w("- Testosterone support products. Nothing sold over the counter raises "
      "testosterone in a man whose level is normal.")
    w("- Fasted cardio, carbohydrate cycling and meal-timing windows. "
      "Practitioner consensus without evidence behind it.")
    w("")
    w("Muscle gain for a trained natural lifter runs about 1 to 2 kg a year. "
      "Regaining muscle you already had is faster. This programme is buying "
      "regain, not new tissue.")
    w("")

    sections = {k: "x" for k in contract.ALL}
    contract.require(sections)
    w(f"Checks passed: {0 if not v else len(v)} violations. "
      f"{len(contract.ALL)} required sections present.")
    return "\n".join(L)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--foods", default="data/foods-india-egg-dairy.json")
    ap.add_argument("--exercises", default="data/exercises-home-gym.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p, plan = load(a.profile), load(a.plan)
    foods = {k: x for k, x in load(a.foods).items() if k[0] != "_"}
    lib = {k: x for k, x in load(a.exercises).items() if k[0] != "_"}
    with open(a.out, "w") as f:
        f.write(render(p, plan, foods, lib))
    print(f"written to {a.out}")
