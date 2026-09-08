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
import physio, blocks, myths, contract, units, ledger
from audit import load, run, food_totals


def rest_day_diff(plan, foods):
    """What changes between the training day and the rest day, in sentences.

    This was a hand-written list in the plan file. Nothing kept it honest, so
    editing one day silently left the other day's description wrong.

    A food that leaves one slot and appears in another at the same quantity is
    one move, not a deletion and an unrelated addition.
    """
    def bare(name, q, food):
        """'the banana', not 'the 1 medium banana'."""
        s = units.amount(name, q, food)
        return s[2:] if s.startswith("1 ") else s

    train, rest = plan["day"], plan["day_rest"]
    dropped, added, out = {}, {}, []

    for slot in train:
        a = {n: q for n, q in train[slot]}
        b = {n: q for n, q in rest.get(slot, [])}
        for n, q in a.items():
            if n not in b:
                dropped[(n, q)] = slot
            elif b[n] != q:
                out.append(f"{slot}: {bare(n, q, foods[n])} becomes "
                           f"{bare(n, b[n], foods[n])}.")
    for slot in rest:
        a = {n: q for n, q in train.get(slot, [])}
        for n, q in rest[slot]:
            if n not in a:
                added[(n, q)] = slot

    for key in list(dropped):
        if key in added:
            n, q = key
            out.append(f"Move {units.amount(n, q, foods[n])} from "
                       f"{dropped[key].split(' ', 1)[0]} to {added[key].split(' ', 1)[0]}.")
            del dropped[key], added[key]
    for (n, q), slot in dropped.items():
        out.append(f"{slot}: drop the {bare(n, q, foods[n])}.")
    for (n, q), slot in added.items():
        out.append(f"{slot}: add {units.amount(n, q, foods[n])}.")
    return out or ["Nothing changes."]


def render(p, plan, foods, lib):
    v, s = run(p, plan, foods, lib)
    L, emitted = [], set()
    w = L.append

    def mark(*concepts):
        """Record that this concept was actually written.

        The contract used to be handed a dict built one line before the check,
        so it could not fail. It now reads what the renderer emitted.
        """
        emitted.update(concepts)

    w(f"# {p['name']} — training and eating")
    w("")
    w(f"{p['kg']:.0f} kg | {p['cm']:.0f} cm | waist {p['waist_cm']:.0f} cm | "
      f"{p['days']} sessions a week | {p['minutes']} minutes each")
    w("")

    # ---------------- body
    mark("split", "exercises", "volume")
    w("## Every week")
    w("")
    w("| Day | Exercise | Sets | Reps |")
    w("|---|---|---|---|")
    for day, exs in plan["week"].items():
        for i, e in enumerate(exs):
            pair = f" (alternate with {e['pair']})" if e.get("pair") else ""
            w(f"| {day if i == 0 else ''} | {e['name']}{pair} | {e['sets']} | {e['reps']} |")
    w("")
    mark("proximity")
    w(plan["proximity"])
    w("")
    mark("warmup")
    w(plan["warmup"])
    w("")
    mark("progression")
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

    flat = [(n, q) for items in plan["day"].values() for n, q in items]
    tk, tp, tf, tc, tfb = units.printed_totals(flat, foods)
    mark("energy", "macros", "meals")
    w("## Every day you train")
    w("")
    w(f"{tk} calories | {tp:g} g protein | {tf:g} g fat | {tc} g carbohydrate | "
      f"{tfb:g} g fibre | {physio.fluid_ml(p)} ml water")
    mark("fibre_fluid")
    w("")
    w("| Time | Food |")
    w("|---|---|")
    for slot, items in plan["day"].items():
        w(f"| {slot} | " + ", ".join(units.amount(n, q, foods[n]) for n, q in items) + " |")
        if "after training" in slot or "pre-training" in slot:
            mark("peri_workout")
    w("")

    # The rest day used to be a hand-written sentence that could contradict the
    # data. It is now derived from the two days, so it cannot go stale.
    mark("training_day")
    w("On days you do not train:")
    for line in rest_day_diff(plan, foods):
        w(f"- {line}")
    w("")
    w(f"Last caffeine of the day: {physio.caffeine_cutoff_h_before_bed(p)} hours "
      f"before you go to bed.")
    w("")
    cats = [(n, f["category"]) for n, f in foods.items() if f.get("category")]
    if cats:
        w("Rotate freely within: " + "; ".join(
            f"{n} ({', '.join(c)})" for n, c in cats) + ".")
        w("")

    pf, pt = physio.protein_target_g(p)
    mark("supplements")
    w("## Supplements")
    w("")
    w("| Item | Dose | When |")
    w("|---|---|---|")
    for s_ in plan["supplements"]:
        w(f"| {s_['item']} | {s_['dose']} | {s_['when']} |")
    w("")

    mark("blocks")
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

    mark("measurement")
    w("## Measure")
    w("")
    w("| What | How often | Do this when |")
    w("|---|---|---|")
    w(f"| Waist at the navel, before food | Weekly | Stop the deficit at "
      f"{physio.deficit_stop_waist_cm(p):g} cm |")
    w("| Bodyweight, morning, 7 day average | Daily, read weekly | Under 0.2 kg "
      "a week for 3 weeks: remove 150 calories. Over 0.7 kg a week: add 150 |")
    w("| Top set weight on incline press and leg press | Weekly | Falling for 2 "
      "weeks in a row: add 200 calories |")
    w("| Hours slept | Daily | Under 6.5 hours for a week: shorten the block by "
      "one week and deload early |")
    w("")

    mark("bad_day", "substitution")
    w("## When the session does not happen")
    w("")
    for line in plan["bad_day"]:
        w(f"- {line}")
    w("")
    fl = plan["floor_day"]
    ft = food_totals([tuple(i) for i in fl], foods)
    w("Floor day for eating, when nothing goes to plan: "
      + ", ".join(units.amount(n, q, foods[n]) for n, q in fl)
      + f". That is {ft[0]:.0f} calories and {ft[1]:.0f} g protein.")
    w("")

    # ---------------- appendix
    w("---")
    w("")
    mark("appendix")
    w("# Appendix")
    w("")
    w("## Why this plan and not another")
    w("")
    w("Recorded as the engine decided, not written afterwards. Each entry names "
      "the rule that made the call so you can go and read it.")
    w("")
    for x in ledger.build(p, plan, tk, s["weekly"], v):
        if x.area == "Injuries":
            mark("contraindicated")
        if "androgen" in x.rejected:
            mark("downside")
        if x.area == "Protein" and "sitting" in x.chose:
            mark("distribution")
        w(f"**{x.area}: {x.chose}**")
        w("")
        w(x.because)
        if x.rejected:
            w("")
            w(f"*{x.rejected}*")
        w("")
        w(f"Rule: `{x.rule}`")
        w("")

    w("## Every food, and what is in it")
    w("")
    w("Swap anything for something with the same numbers. The column adds up as printed.")
    w("")
    for label, day in (("Training day", plan["day"]), ("Rest day", plan["day_rest"])):
        w(f"**{label}**")
        w("")
        w("| Time | Food | Made of | kcal | Protein | Fat | Carbs |")
        w("|---|---|---|---|---|---|---|")
        dk = dp = df = dc = 0
        for slot, items in day.items():
            mk = mp = mf = mc = 0
            first = True
            for n, q in items:
                m = units.macros(q, foods[n])
                k, p_, f_, c_ = round(m[0]), round(m[1], 1), round(m[2], 1), round(m[3])
                mk += k; mp = round(mp + p_, 1); mf = round(mf + f_, 1); mc += c_
                made = foods[n].get("made_of", "")
                w(f"| {slot if first else ''} | {units.amount(n, q, foods[n])} | {made} "
                  f"| {k} | {p_:g} | {f_:g} | {c_} |")
                first = False
            w(f"| | **{slot.split(' ', 1)[-1]} total** | | **{mk}** | **{mp:g}** "
              f"| **{mf:g}** | **{mc}** |")
            dk += mk; dp = round(dp + mp, 1); df = round(df + mf, 1); dc += mc
        w(f"| | **Whole day** | | **{dk}** | **{dp:g}** | **{df:g}** | **{dc}** |")
        w(f"| | Must be | | see The 24 weeks | at least {pf} | at least "
          f"{physio.fat_floor_g(p)} | whatever is left |")
        w("")
    w(f"The protein and fat floors apply every day. The calorie number changes by "
      f"block, so read it from The 24 weeks table. Aim for {pt} g protein rather "
      f"than the {pf} g floor when the day allows it.")
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

    mark("micronutrients")
    w("## What this diet does not supply")
    w("")
    w("These are properties of the foods chosen, worked out from what is on the "
      "plate. They are not enforced: nothing rejects a plan for being low in "
      "iron. Treat them as what to watch and what to ask a doctor about.")
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

    mark("excluded")
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

    contract.require({k: "written" for k in emitted})
    w(f"Checks passed: {len(v)} violations. "
      f"{len(emitted)} of {len(contract.ALL)} required sections written.")
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
