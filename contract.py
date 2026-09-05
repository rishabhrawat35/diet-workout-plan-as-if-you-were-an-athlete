"""
What a finished plan must CONTAIN. Not whether its numbers are valid.

Every check written before this file was a constraint check -- is this number
inside its bounds. Not one was a completeness check -- is this section present
at all. So violations were caught automatically and omissions were not:
supplements vanished between two rebuilds, post-workout feeding was never
addressed, dry fruits were dropped during a calorie correction and never
mentioned again, warm-ups and a progression rule were never written down. Each
was found in review, one at a time, which is not a review process.

The depth contract existed as prose for several drafts. Prose does not fail a
build. This does.
"""

DIET = {
    "energy":         "Calorie target and the weekly rate of change it implies.",
    "macros":         "Each macro with the floor it is held to.",
    "distribution":   "Protein across the day's eating occasions.",
    "meals":          "Every eating occasion with items and household quantities.",
    "training_day":   "How a training day differs from a rest day.",
    "peri_workout":   "What is eaten before and after training.",
    "fibre_fluid":    "Fibre target and daily fluid.",
    "micronutrients": "Risks the food pattern creates and the food-first fix.",
    "supplements":    "Every supplement with dose, timing and evidence tier.",
    "downside":       "What happens if the person under-eats this target.",
}

TRAINING = {
    "split":          "Which muscles are trained on which day.",
    "volume":         "Weekly sets per muscle.",
    "exercises":      "Every exercise with sets, reps and the order performed.",
    "warmup":         "How to warm up before the first working set.",
    "progression":    "The rule for when load or reps go up.",
    "proximity":      "How close to failure each set is taken.",
    "substitution":   "What to do when equipment is occupied or unavailable.",
    "contraindicated":"Movements excluded for this person and why.",
    "bad_day":        "What to do on a day when the session cannot be completed.",
}

SHARED = {
    "blocks":         "The week-by-week calendar, training and eating together.",
    "measurement":    "What to measure, how often, and the trigger that changes the plan.",
    "excluded":       "What was left out and the rule it would have broken.",
    "appendix":       "Reasoning, evidence tiers and standing answers.",
}

ALL = {**DIET, **TRAINING, **SHARED}


class Incomplete(Exception):
    pass


def check(sections, required=None):
    req = required or ALL
    return [f"{k}: {why}" for k, why in req.items()
            if not str(sections.get(k, "")).strip()]


def require(sections, required=None):
    m = check(sections, required)
    if m:
        raise Incomplete("Plan is not deliverable. Missing sections:\n  "
                         + "\n  ".join(m))
    return True
