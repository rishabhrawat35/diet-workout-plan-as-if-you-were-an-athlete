"""
A record of what the engine decided, written as it decides.

The version this replaces re-derived the explanations at render time from the
profile. Three things were wrong with that. It reported only decisions someone
had written a paragraph for, so a rule with no paragraph was silently absent.
It could not say what was rejected, which is the part worth reading. And a rule
could change without its explanation changing, with nothing to notice.

The rules in physio.py stay pure. A function that writes to a log while it
computes is harder to trust, not easier, and purity is what makes them
testable. What makes this a record rather than a reconstruction is the coverage
test: every public rule must appear in NARRATED, so adding a rule without
narrating it fails the build. The enforcement is the mechanism, not the storage.
"""

import physio

# Raw profile keys must never reach the page. This has leaked twice.
COOKING_WORDS = {"measured": "with the oil measured out",
                 "light": "light on oil",
                 "typical_home": "the way a home kitchen normally does",
                 "heavy": "generous with oil"}
STORAGE_WORDS = {"none": "nothing to keep it cool",
                 "insulated": "an insulated bag",
                 "insulated_gelpack": "an insulated bag with a frozen gel pack",
                 "fridge": "a fridge"}
JOB_WORDS = {"desk": "desk", "shift": "shift-work", "physical": "physical",
             "travel": "travelling"}
GYM_WORDS = {"empty": "usually empty", "shared": "shared", "busy": "busy"}


class Entry:
    __slots__ = ("area", "chose", "because", "rejected", "rule")

    def __init__(self, area, chose, because, rejected="", rule=""):
        self.area, self.chose, self.because = area, chose, because
        self.rejected, self.rule = rejected, rule


# Every physio rule that decides something a reader would ask about. The test
# in test_ledger.py compares this against what physio.py actually exposes.
# Functions that are not decisions and are deliberately not narrated. Listing
# them is what stops "not narrated" and "forgotten" looking the same.
NOT_DECISIONS = {"missing_context", "require_context"}

NARRATED = {
    "bmr", "activity_factor", "tdee", "cooking_fat_g",
    "protein_target_g", "fat_floor_g", "dose_g", "fibre_target_g", "fluid_ml",
    "deload_every_weeks", "diet_break_due_weeks", "max_weekly_loss_kg",
    "deficit_stop_waist_cm", "caffeine_cutoff_h_before_bed",
    "volume_bounds", "priority_min_sets", "sec_per_set", "session_minutes",
    "banned_movements", "waist_height_flag", "healthy_bodyfat_range",
    "life_stage_stop", "micronutrient_flags", "androgen_factors",
    "unmapped_injuries", "refer_out", "distribution_ok",
}


def build(p, plan, day_kcal, weekly_kcal, violations=()):
    """Every decision, in the order it shapes the plan."""
    e, tdee = [], physio.tdee(p)
    add = lambda *a, **k: e.append(Entry(*a, **k))

    # ---------------------------------------------------------------- energy
    add("Energy", f"{day_kcal:.0f} calories on a training day",
        f"Your requirement is {tdee:.0f} calories: a basal rate of "
        f"{physio.bmr(p):.0f} multiplied by {physio.activity_factor(p)} for a "
        f"{JOB_WORDS[p['job']]} job, {p['days']} training days and "
        f"{p['steps']} steps a day. "
        f"Eating {day_kcal:.0f} is a {tdee - day_kcal:.0f} calorie deficit, "
        f"which is {(tdee - weekly_kcal) * 7 / 7700:.2f} kg a week across the "
        f"whole week.",
        f"Not lower. The cap is {physio.max_weekly_loss_kg(p)} kg a week, which "
        f"is 0.75 per cent of your bodyweight, and below "
        f"{0.75 * tdee:.0f} calories androgen output starts to fall.",
        "physio.tdee, physio.max_weekly_loss_kg")

    fat_g = physio.cooking_fat_g(p)
    add("Energy", f"{fat_g} g of oil counted in every cooked dish",
        f"You said your kitchen cooks {COOKING_WORDS[p['cooking_fat']]}.",
        f"Not the 5 g a measured teaspoon holds. Across two cooked dishes that "
        f"assumption is worth {(fat_g - 5) * 9 * 2:.0f} calories a day, about "
        f"half the deficit, and it is invisible on the plate.",
        "physio.cooking_fat_g")

    # ---------------------------------------------------------------- macros
    pf, pt = physio.protein_target_g(p)
    add("Protein", f"{pf} g floor, {pt} g target",
        f"You are in a deficit, where the fat-free-mass response rises linearly "
        f"to at least 1.9 g per kg with no plateau found. At {p['kg']:.0f} kg "
        f"that is {pf} g.",
        f"Not the 1.6 g per kg that applies at maintenance. The effect is "
        f"stronger for men and for programmes past four weeks, and this runs 24.",
        "physio.protein_target_g")

    add("Protein", f"{physio.dose_g(p)} g in one sitting",
        f"Past roughly 0.4 g per kg in a single meal the muscle-building "
        f"response saturates. At {p['kg']:.0f} kg that is {physio.dose_g(p)} g.",
        "Not every feeding needs to reach it. Three sittings clearing it is the "
        "requirement; the smaller ones are not meant to.",
        "physio.dose_g, physio.distribution_ok")

    add("Fat", f"{physio.fat_floor_g(p)} g floor",
        f"0.6 g per kg. Below it testosterone falls modestly.",
        "", "physio.fat_floor_g")

    add("Fibre and fluid",
        f"{physio.fibre_target_g(day_kcal)} g fibre, {physio.fluid_ml(p)} ml water",
        f"14 g of fibre per 1000 calories, and 33 ml of water per kg with "
        f"{'an extra 500 ml for the heat and ' if p['ambient_c'] >= 30 else ''}"
        f"500 ml for training.",
        "", "physio.fibre_target_g, physio.fluid_ml")

    # -------------------------------------------------------------- recovery
    gap, brk = physio.deload_every_weeks(p), physio.diet_break_due_weeks(p)
    would = []
    if p["age"] < 40:
        would.append("6 weeks if you were over 40, 5 if over 55")
    if p.get("sleep_h", 7) >= 6.5:
        would.append("5 weeks if you slept under 6.5 hours")
    add("Recovery", f"A rest week every {gap} weeks",
        f"From age {p['age']}, {p.get('training_age_yrs')} years of training and "
        f"{p.get('sleep_h')} hours of sleep.",
        ("It would be " + ", and ".join(would) + ".") if would else "",
        "physio.deload_every_weeks")

    add("Recovery", f"The diet break sits on the rest week at or after week {brk}",
        f"You need a break from the deficit by week {brk} and a rest week every "
        f"{gap} weeks.",
        "Not on its own week. Left independent they land apart, which means "
        "eating at maintenance during a hard week and dieting through an easy "
        "one.", "physio.diet_break_due_weeks, blocks.calendar")

    add("Recovery", f"Last caffeine {physio.caffeine_cutoff_h_before_bed(p)} "
                    f"hours before bed",
        f"Caffeine has a half life near 5 hours and you sleep {p.get('sleep_h')} "
        f"hours, which leaves no room for a late dose.",
        "", "physio.caffeine_cutoff_h_before_bed")

    # ---------------------------------------------------------------- volume
    lo, hi = physio.volume_bounds(p)
    add("Volume", f"{lo} to {hi} sets per muscle per week",
        f"From {p.get('training_age_yrs')} years of consistent training. "
        f"Beginners grow on less and tolerate less.",
        "", "physio.volume_bounds")

    if p.get("priorities"):
        add("Volume", f"At least {physio.priority_min_sets(p)} sets for "
                      f"{', '.join(p['priorities'])}",
            f"You named them priorities, so they carry a floor "
            f"{physio.priority_min_sets(p) - lo} sets above the general minimum.",
            "Not the general floor. A muscle named as a priority and trained at "
            "the general minimum was a priority in the intent only.",
            "physio.priority_min_sets")

    add("Sessions", f"A set costs {physio.sec_per_set(p)} seconds",
        f"You described the gym as {GYM_WORDS[p.get('gym_traffic', 'shared')]}.",
        f"Not the {physio.SEC_PER_SET['empty']} seconds an empty gym allows. "
        f"Two exercises alternated cost {physio.PAIRED_FACTOR} of that each, "
        f"which is how {p['minutes']} minutes holds the listed volume.",
        "physio.sec_per_set, physio.session_minutes")

    # -------------------------------------------------------------- injuries
    banned = physio.banned_movements(p)
    if banned:
        add("Injuries", f"{len(banned)} movements removed",
            "; ".join(f"no {m}, which {why}" for m, why in banned[:3])
            + (f"; and {len(banned) - 3} more" if len(banned) > 3 else "") + ".",
            "Not listed as cautions. A caution in a document is not a decision.",
            "physio.banned_movements")
    for inj in physio.unmapped_injuries(p):
        add("Injuries", f"'{inj}' was not planned around",
            "It is not in the injury map, so no movement was excluded for it.",
            "Have a clinician review the plan rather than assume it is covered.",
            "physio.unmapped_injuries")

    # ------------------------------------------------------------- logistics
    limit = {"fridge": 24, "insulated_gelpack": 8}.get(
        p["storage"], (6 if p["ambient_c"] < 22 else 4 if p["ambient_c"] < 27 else 2))
    add("Food safety", f"Carried food eaten within {limit} hours",
        f"At {p['ambient_c']} C with {STORAGE_WORDS[p['storage']]}, and you hold "
        f"lunch for {p['hold_hours']} hours.",
        "Cooked rice is capped tighter unless it is actively chilled, because "
        "the spores that matter survive cooking.",
        "audit.py food safety check")

    # ---------------------------------------------------------- body and sex
    r, flag = physio.waist_height_flag(p)
    bf_lo, bf_hi = physio.healthy_bodyfat_range(p)
    add("Body composition", f"Stop the deficit at "
                            f"{physio.deficit_stop_waist_cm(p):g} cm",
        f"Your waist-to-height ratio is {r:.2f} ({flag}); 0.50 is the guideline "
        f"for both sexes. Healthy body fat for you is {bf_lo} to {bf_hi} per cent.",
        "Waist-to-height rather than BMI, because BMI counts muscle as excess.",
        "physio.waist_height_flag, physio.healthy_bodyfat_range")

    # ------------------------------------------------------------ what fired
    if violations:
        add("Checks", f"{len(violations)} problems were found and fixed",
            "; ".join(f"[{k}] {m}" for k, m in violations[:5])
            + (f"; and {len(violations) - 5} more" if len(violations) > 5 else "."),
            "", "audit.py")
    else:
        add("Checks", "The plan passed every check on this run",
            "No violation was raised at any severity.", "", "audit.py")

    return e
