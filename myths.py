"""
Standing answers to claims that keep coming up, and claims the engine may
never emit.

This exists because the person had to raise night carbs, evening fat and
cortisol, and soy and estrogen one at a time, each as a separate round trip.
A plan that ships with the answers costs nothing and saves all of them.

Tiers: strong (meta-analysis or repeated human trials), moderate (a trial or
two, or strong mechanistic agreement), weak (practitioner consensus only --
never an instruction, only a dated test with a kill criterion).
"""

DIET = {
    "carbs at night cause fat gain":
        ("strong", "Total intake decides fat gain. Evening carbohydrate is "
         "neutral and mildly helps sleep onset."),
    "fat at night meets a cortisol spike":
        ("strong", "Cortisol peaks in the morning and troughs near midnight. "
         "Evening is its lowest point."),
    "soy lowers testosterone or raises estrogen in men":
        ("strong", "Meta-analyses find no effect on total testosterone, free "
         "testosterone, estradiol or SHBG at ordinary intakes."),
    "food or timing can strip fat from one body region":
        ("strong", "Regional fat loss cannot be directed by diet. Distribution "
         "is genetic and hormonal."),
    "a food or supplement grows a specific muscle":
        ("strong", "Nutrition is systemic. Only training is regional."),
    "testosterone boosters work in men with normal levels":
        ("strong", "No over-the-counter compound raises testosterone in a man "
         "who is not deficient. Sleep, body fat and energy intake do."),
    "eating every three hours raises metabolic rate":
        ("strong", "Meal frequency does not change total energy expenditure."),
    "fasted cardio burns more fat":
        ("moderate", "Substrate use during the session shifts. 24-hour fat "
         "balance does not."),
    "protein above 2 g/kg is wasted":
        ("moderate", "In an energy deficit the fat-free-mass response is "
         "linear to at least 1.9 g/kg with no plateau found."),
    "you must eat protein within 30 minutes of training":
        ("moderate", "The window is hours, not minutes. It matters more after "
         "a fasted session than a fed one."),
}

TRAINING = {
    "a muscle that will not grow is a genetic dead end":
        ("moderate", "Before concluding genetics, check that the muscle has "
         "had enough weekly sets, enough frequency, full range of motion under "
         "load, and proximity to failure. Most 'genetic' muscles have had none "
         "of the four."),
    "calves need daily training because they are used to walking":
        ("moderate", "Calves respond to the same variables as other muscles: "
         "load, range, frequency and proximity to failure. Daily training "
         "removes the recovery that growth needs."),
    "high reps tone and low reps bulk":
        ("strong", "Hypertrophy is similar across 5 to 30 reps when sets are "
         "taken close to failure. There is no toning rep range."),
    "muscle confusion drives growth":
        ("strong", "Progressive overload drives growth. Constant variation "
         "prevents the measurement that overload needs."),
    "every set must go to failure":
        ("moderate", "Stopping 1 to 3 reps short gives similar growth with less "
         "fatigue, which allows more total quality volume across the week."),
    "soreness measures a good session":
        ("strong", "Soreness tracks novelty and eccentric load, not growth."),
    "you can turn fat into muscle":
        ("strong", "They are different tissues. You lose one and build the "
         "other, sometimes at once, never by conversion."),
    "machines are inferior to free weights for growth":
        ("moderate", "For hypertrophy the difference is small. Machines are "
         "often better where a joint needs protecting."),
    "lifting makes you bulky quickly":
        ("strong", "A trained natural lifter adds roughly 1 to 2 kg of muscle "
         "a year. Regaining lost muscle is faster than building new."),
}

# Phrases that may never appear in a generated instruction, diet or training.
BANNED = ("spot reduce", "targets belly fat", "burns chest fat",
          "boosts testosterone", "detox", "resets metabolism", "melts fat",
          "shrinks fat cells in", "turns fat into muscle", "muscle confusion",
          "tones without bulk", "long lean muscle")


def scan(lines):
    """Refuse to ship a plan containing a banned claim."""
    out = []
    for i, line in enumerate(lines):
        low = str(line).lower()
        for c in BANNED:
            if c in low:
                out.append((i, c, str(line).strip()))
    return out


def relevant(profile):
    """The myths worth printing for this person, given what they have said."""
    out = dict(DIET)
    out.update(TRAINING)
    return out
