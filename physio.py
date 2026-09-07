"""
Physiology. Training and nutrition rules in one place, because they constrain
each other: a deficit changes recovery, recovery changes volume tolerance, and
volume changes the calorie floor.

Nothing here knows a cuisine, a region, a gym, or a meal count. Those live in
the data files and in the profile.
"""

# ==================================================== intake gate

REQUIRED = {
    # person
    "sex":              "biological sex; the BMR constant differs by 166 kcal",
    "age":              "years",
    "kg":               "bodyweight in kilograms",
    "cm":               "height in centimetres",
    "waist_cm":         "waist at the navel",
    "sleep_h":          "typical hours asleep",
    "training_age_yrs": "years of consistent resistance training",
    # training context
    "days":             "training days per week the person will actually do",
    "minutes":          "minutes available per session",
    "equipment":        "what the gym actually contains; never assume",
    "injuries":         "injury list, empty list if none",
    "priorities":       "muscles the person wants prioritised",
    # eating context
    "ambient_c":        "daytime temperature where food will be held",
    "storage":          "none, insulated, insulated_gelpack or fridge",
    "hold_hours":       "hours between packing a meal and eating it",
    "protein_sources":  "allowed sources, e.g. egg, dairy, legume, soy, meat",
    "cooking_fat":      "measured, light, typical_home or heavy",
    "eating_occasions": "times a day the person will actually eat",
    "job":              "desk, shift, physical or travel",
    "steps":            "typical daily step count",
}


class IntakeIncomplete(Exception):
    """Raised, never returned. A gate that only reports is not a gate."""


def missing_context(p):
    return [f"{k}: {why}" for k, why in REQUIRED.items() if p.get(k) is None]


def require_context(p):
    miss = missing_context(p)
    if miss:
        raise IntakeIncomplete(
            "Cannot build a plan. Ask for these and do not guess:\n  "
            + "\n  ".join(miss))
    return True


# ==================================================== life stage

def life_stage_stop(p):
    age = p.get("age", 30)
    if age < 18:
        return ("Under 18. Growth plates, wide variation in maturation and "
                "different volume tolerance. Refer to a coach who works with "
                "adolescents.")
    if p.get("pregnant"):
        return ("Pregnant. Needs an obstetric clinician, not a generated plan.")
    if p.get("postpartum_weeks") is not None and p["postpartum_weeks"] < 12:
        return ("Under 12 weeks postpartum. Needs pelvic floor and abdominal "
                "wall assessment before loading.")
    if age >= 65 and not p.get("medically_cleared"):
        return ("65 or over without recorded medical clearance. Get clearance, "
                "then set medically_cleared to true.")
    return None


# ==================================================== energy

def bmr(p):
    """Mifflin-St Jeor. The constant differs by sex; the first version of this
    engine used the male one for everyone, overestimating women by 166 kcal."""
    base = 10 * p["kg"] + 6.25 * p["cm"] - 5 * p["age"]
    return base + (5 if p.get("sex", "m") == "m" else -161)


def activity_factor(p):
    f = {"desk": 1.15, "shift": 1.25, "physical": 1.40, "travel": 1.20}.get(
        p.get("job", "desk"), 1.15)
    f += 0.06 * p.get("days", 3)
    f += 0.015 * max(0, (p.get("steps", 5000) - 4000) / 1000)
    return round(min(f, 1.95), 3)


def tdee(p):
    return bmr(p) * activity_factor(p)


COOKING_FAT_G = {"measured": 5, "light": 8, "typical_home": 12, "heavy": 18}


def cooking_fat_g(p):
    """Added fat that actually lands in one serving. The first version used the
    'measured' figure for a kitchen where nobody measures, and was 210 kcal a
    day light as a result."""
    return COOKING_FAT_G[p["cooking_fat"]]


# ==================================================== macros

def protein_target_g(p):
    """In an energy deficit the fat-free-mass response is linear to at least
    1.9 g/kg bodyweight with no plateau identified, and the effect is stronger
    for men and for interventions over four weeks."""
    kg = p["kg"]
    floor = 1.9 if p.get("deficit") else 1.6
    target = 2.1 if p.get("deficit") else 1.8
    if p["age"] >= 60:
        floor += 0.2
        target += 0.2
    return round(floor * kg), round(target * kg)


def fat_floor_g(p):
    return round(0.6 * p["kg"])


def dose_g(p):
    """Protein in one sitting before the response saturates."""
    return round((0.55 if p["age"] >= 60 else 0.4) * p["kg"])


def distribution_ok(per_occasion_g, p):
    """The dose applies to main meals, not every feeding. With seven feedings
    and a total already above target, most cannot reach it and should not."""
    d = dose_g(p)
    reached = sum(1 for g in per_occasion_g if g >= d)
    need = 3 if len(per_occasion_g) >= 5 else 2
    return reached >= need, reached, need, d


def fibre_target_g(kcal):
    return round(14 * kcal / 1000)


FIBRE_TOLERANCE_G = 1


def fluid_ml(p, training=True):
    base = 33 * p["kg"]
    if p.get("ambient_c", 25) >= 30:
        base += 500
    if training:
        base += 500
    return int(round(base, -2))


# ==================================================== recovery

def deload_every_weeks(p):
    w = 8
    if p["age"] >= 55:
        w = 5
    elif p["age"] >= 40:
        w = 6
    if p.get("training_age_yrs", 0) < 1:
        w = min(w, 6)
    if p.get("sleep_h", 7) < 6.5:
        w = min(w, 5)
    return w


def diet_break_due_weeks(p):
    w = 12
    if p.get("sleep_h", 7) < 6.5:
        w = 8
    if p.get("age", 30) >= 45:
        w = min(w, 10)
    return w


def max_weekly_loss_kg(p):
    return round(0.0075 * p["kg"], 2)


def deficit_stop_waist_cm(p):
    return round(0.50 * p["cm"], 1)


def caffeine_cutoff_h_before_bed(p):
    return 10 if p.get("sleep_h", 7) <= 7 else 8


# ==================================================== volume and sessions

def volume_bounds(p):
    ta = p.get("training_age_yrs", 2)
    if ta < 1:
        return 6, 14
    if ta < 3:
        return 8, 20
    return 10, 22


def priority_min_sets(p):
    return volume_bounds(p)[0] + 2


# Seconds per working set including rest. The first version used 165 s, which
# assumes an empty gym and no interruptions. A shared gym is not that.
SEC_PER_SET = {"empty": 165, "shared": 200, "busy": 240}
WARMUP_SEC = 480


def sec_per_set(p):
    return SEC_PER_SET.get(p.get("gym_traffic", "shared"), 200)


# A paired set alternates with another exercise that uses a different muscle
# and a different station, so its rest is spent working rather than waiting.
PAIRED_FACTOR = 0.65


def session_minutes(p, total_sets, paired_sets=0):
    solo = total_sets - paired_sets
    sec = sec_per_set(p)
    return (WARMUP_SEC + solo * sec + paired_sets * sec * PAIRED_FACTOR) / 60


# ==================================================== endocrine

def androgen_factors(p, fat_g, kcal):
    out = []
    t = tdee(p)
    if p.get("sleep_h", 7) < 7:
        out.append(("strong", f"Sleeping {p['sleep_h']} h. Restricting sleep to "
                    "about 5 h lowers daytime testosterone by 10 to 15 per cent "
                    "within a week. Largest modifiable factor here."))
    if kcal < 0.75 * t:
        out.append(("strong", f"Eating {kcal:.0f} kcal against {t:.0f} kcal is a "
                    "deficit deeper than 25 per cent, which suppresses androgen "
                    "output. Raise calories."))
    if fat_g / p["kg"] < 0.5:
        out.append(("moderate", f"Fat at {fat_g/p['kg']:.2f} g/kg. Below 0.5 g/kg "
                    "testosterone falls modestly."))
    r = p["waist_cm"] / p["cm"]
    if r >= 0.50:
        out.append(("strong", f"Waist to height {r:.2f}. Adipose tissue contains "
                    "aromatase, which converts testosterone to estradiol. Losing "
                    "the fat is the hormonal intervention."))
    out.append(("moderate", "Alcohol suppresses testosterone dose-dependently."))
    out.append(("strong", "Resistance training raises testosterone for under an "
                "hour after a session. It does not raise resting levels."))
    return out


# ==================================================== body composition

def waist_height_flag(p):
    r = p["waist_cm"] / p["cm"]
    return (r, "high") if r >= 0.6 else (r, "raised") if r >= 0.5 else (r, "ok")


def healthy_bodyfat_range(p):
    return (10, 20) if p.get("sex", "m") == "m" else (18, 30)


# ==================================================== injuries

INJURY_MAP = {
    "lumbar disc": [
        ("conventional deadlift", "loads a flexed lumbar spine at maximal load"),
        ("barbell back squat", "spinal compression early in a return to training"),
        ("bent-over row", "holds the spine in the position being avoided"),
        ("sit-up", "loaded spinal flexion"),
        ("crunch", "loaded spinal flexion"),
        ("russian twist", "loaded rotation under flexion"),
        ("good morning", "long lever on a flexed spine"),
    ],
    "sciatica": [
        ("conventional deadlift", "spinal loading with nerve involvement"),
        ("good morning", "long lever on a flexed spine"),
        ("sit-up", "loaded spinal flexion"),
    ],
    "shoulder impingement": [
        ("overhead barbell press", "drives the arm through the painful arc"),
        ("upright row", "internal rotation under load at shoulder height"),
        ("behind-neck", "extreme external rotation under load"),
    ],
    "rotator cuff": [
        ("upright row", "impinges the cuff tendons"),
        ("behind-neck", "extreme external rotation under load"),
    ],
    "patellofemoral": [
        ("sissy squat", "high patellofemoral compression at deep knee flexion"),
        ("deep leg press", "knee flexion beyond comfortable range under load"),
    ],
    "hip impingement": [
        ("deep leg press", "hip flexion past the point of impingement"),
        ("deep squat", "hip flexion past the point of impingement"),
    ],
    "wrist": [
        ("straight-bar curl", "forced wrist supination under load"),
        ("front squat", "extreme wrist extension in the rack position"),
    ],
    "hernia": [
        ("valsalva", "intra-abdominal pressure"),
        ("heavy deadlift", "intra-abdominal pressure"),
    ],
}


def banned_movements(p):
    out, seen, uniq = [], set(), []
    for inj in p.get("injuries", []):
        for key, moves in INJURY_MAP.items():
            if key in str(inj).lower():
                out.extend(moves)
    for m, why in out:
        if m not in seen:
            uniq.append((m, why))
            seen.add(m)
    return uniq


def unmapped_injuries(p):
    return [i for i in p.get("injuries", [])
            if not any(k in str(i).lower() for k in INJURY_MAP)]


# ==================================================== micronutrients

# The first element is what a reader should see, not an internal key. An
# earlier version printed "epa_dha:" straight into the document.
PATTERN_RISK = [
    ("Vitamin B12", {"dairy", "egg", "meat", "fish"},
     "Nothing in this food pattern carries B12."),
    ("Omega-3, the EPA and DHA kind", {"fish", "algae"},
     "No preformed EPA or DHA here. The plant form converts at a few per cent, "
     "so a capsule or two fish meals a week is the fix."),
    ("Iron, the kind from meat", {"meat", "fish"},
     "No heme iron here. Pair the plant sources with something containing "
     "vitamin C, which is why there is an orange at lunch."),
    ("Calcium", {"dairy", "fortified", "leafy_greens"},
     "No substantial calcium source in this pattern."),
]


def micronutrient_flags(pattern_tags):
    tags = set(pattern_tags)
    out = [(k, msg) for k, need, msg in PATTERN_RISK if not (tags & need)]
    out.append(("Vitamin D", "Not reliably present in any diet, and it depends "
                "on sun exposure rather than food. Get a 25(OH)D blood test, "
                "then dose to the result."))
    return out


# ==================================================== referrals

def refer_out(p):
    out = []
    if p.get("chest_tissue_unassessed"):
        out.append("Male chest tissue is either subcutaneous fat, which responds "
                   "to a deficit, or glandular, which does not respond at any "
                   "body fat level. A clinician distinguishes them by "
                   "examination. Establish which before setting a goal on it.")
    if p.get("sleep_h", 7) < 6:
        out.append("Under 6 h of sleep is a medical question before it is a "
                   "training one. No diet compensates for it.")
    for inj in unmapped_injuries(p):
        out.append(f"'{inj}' is not in the injury map, so nothing was excluded "
                   f"for it. Have a clinician review the plan.")
    return out
