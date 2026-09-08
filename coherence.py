"""
Whether a plan is doable, not just whether its numbers are legal.

Both halves of this file come from the same discovery. The diet engine could
assemble "3 boiled eggs, 2 roti, 1 raw salad" and call it breakfast, because it
only checked macros: roti is a carrier and needs something wet, and nothing in
the rules knew that. The training engine has the identical blind spot -- it can
assemble a day that hits 20 sets and cannot be performed, because it only
checks volume.

Everything culture- or gym-specific lives in the data files as roles, cuisines,
categories and equipment. This file knows the shapes only.
"""

import re

# ============================================================ MEALS

# carrier  needs something wet to be eaten with (roti, rice, bread)
# wet      can be eaten with a carrier (dal, sabji, curry, bhurji, curd)
# anchor   the protein centre
# side     eaten alongside; does not rescue a carrier
# drink    liquid; never rescues a carrier
# fruit    eaten alone or after
MEAL_ROLES = ("carrier", "wet", "anchor", "side", "drink", "fruit")


def check_roles(foods):
    """Every food must declare a role this module knows.

    MEAL_ROLES was declared and never read, so a typo'd role in a new food file
    would change meal behaviour silently -- which undercuts the whole "swap the
    data file, not the code" claim.
    """
    bad = {n: f.get("role") for n, f in foods.items()
           if f.get("role") not in MEAL_ROLES}
    if bad:
        raise ValueError(
            "unknown role in the food data: "
            + ", ".join(f"{n} declares '{r}'" for n, r in sorted(bad.items()))
            + f". Known roles: {', '.join(MEAL_ROLES)}.")
    return True


PER_SERVING_CLAIM = re.compile(
    r"\b\d+(\.\d+)?\s*(tsp|tbsp|teaspoon|tablespoon|cup|katori|bowl|scoop|serving)s?\b")


def check_composition(foods):
    """A per-gram food may not describe a per-serving quantity.

    Its macro vector is one gram, so a sentence like "pan tossed with 1 tsp oil"
    has nowhere to put the oil: the reader is told about fat the numbers do not
    carry. Written after paneer was found claiming a teaspoon of oil while
    sitting below plain paneer on fat. The check is over the data file, so it
    holds for any food file swapped in, not just this one.
    """
    bad = {}
    for n, f in foods.items():
        if f.get("unit") not in ("g", "ml"):
            continue
        m = PER_SERVING_CLAIM.search(f.get("made_of", "") or "")
        if m:
            bad[n] = m.group(0)
    if bad:
        raise ValueError(
            "a per-gram food describes a per-serving quantity, which its macro "
            "vector cannot carry: "
            + ", ".join(f"{n} says '{q}'" for n, q in sorted(bad.items()))
            + ". State the composition per unit, or give the food a serving unit.")
    return True


def meal_problems(items, foods):
    out = []
    roles = [foods[n]["role"] for n, _ in items]
    names = [n for n, _ in items]

    if "carrier" in roles and "wet" not in roles:
        carriers = [n for n, _ in items if foods[n]["role"] == "carrier"]
        out.append(("coherence", f"{', '.join(carriers)} with nothing wet to eat "
                    f"it with. Add a dal, sabji, curry, bhurji or curd, or drop "
                    f"the carrier."))

    sets_ = [set(foods[n]["cuisine"]) for n, _ in items if foods[n]["cuisine"]]
    if len(sets_) > 1 and not set.intersection(*sets_):
        out.append(("coherence", f"{', '.join(names)} do not belong on one plate."))

    scores = [foods[n]["palatability"] for n, _ in items]
    if scores and sum(scores) / len(scores) < 2.5:
        out.append(("palatability",
                    f"Average palatability {sum(scores)/len(scores):.1f} of 5. "
                    f"This will not survive the length of the programme."))
    return out


# ============================================================ SESSIONS

# The training analogue of "roti with nothing wet". A day can be volume-legal
# and undoable.
def session_problems(exercises, lib, equipment, minutes):
    """exercises: [{name, sets, reps}] in the order they will be performed.
    lib: name -> {pattern, equipment, load_class, category}
    equipment: what this gym actually has.

    An exercise the library does not know used to raise KeyError and take the
    whole audit down. Silence and a traceback are the same failure: the person
    learns nothing about the exercise. It is now a refusal with a name in it.
    """
    out = []
    unknown = [e["name"] for e in exercises if e["name"] not in lib]
    for n in unknown:
        out.append(("refusal", f"'{n}' is not in the exercise library, so nothing "
                    f"could be checked about it -- not the equipment it needs, "
                    f"not whether an injury rules it out. Add it to the library "
                    f"or replace it."))
    exercises = [e for e in exercises if e["name"] in lib]
    names = [e["name"] for e in exercises]

    # 1. Equipment the gym does not have. The training version of assuming an
    #    ambient temperature: never guess what is in the room.
    for n in names:
        need = lib[n]["equipment"]
        if need and need not in equipment:
            out.append(("refusal", f"{n} needs {need}, which this gym does not "
                        f"have. Substitute it or remove it."))

    # 2. Two heavy compounds back to back. Volume-legal, performance-destroying.
    heavy = [i for i, n in enumerate(names) if lib[n]["load_class"] == "heavy"]
    for a, b in zip(heavy, heavy[1:]):
        if b == a + 1:
            out.append(("coherence", f"{names[a]} immediately before {names[b]}. "
                        f"Two heavy compounds back to back means the second is "
                        f"trained fatigued. Put an isolation exercise between "
                        f"them or move one to another day."))

    # 3. Isolation before the compound that uses it.
    for i, n in enumerate(names):
        if lib[n]["load_class"] != "isolation":
            continue
        later = [m for m in names[i+1:] if lib[n]["pattern"] in lib[m].get("uses", [])]
        if later:
            out.append(("coherence", f"{n} before {later[0]}. Pre-fatiguing the "
                        f"smaller muscle caps the load on the bigger lift. Put "
                        f"{n} after it."))

    # 4. One station, two exercises, no way to run them without waiting.
    stations = {}
    for n in names:
        st = lib[n]["equipment"]
        if st:
            stations.setdefault(st, []).append(n)
    for st, users in stations.items():
        if len(users) > 3:
            out.append(("coherence", f"{len(users)} exercises on the one {st} in a single "
                        f"session: {', '.join(users)}. In a shared gym this is "
                        f"where the session overruns."))

    # 5. Enjoyment. A session someone dreads is a session they skip, which is
    #    the same defect class as a meal nobody wants to eat.
    scores = [lib[n].get("tolerability", 3) for n in names]
    if scores and sum(scores) / len(scores) < 2.5:
        out.append(("palatability", f"Average tolerability {sum(scores)/len(scores):.1f} "
                    f"of 5. Adherence, not physiology, will end this."))
    return out


# ============================================================ CLUSTERING


# Tags that carry a nutrient load worth spreading across the day. A tag not
# listed here is descriptive (perishable, vitamin_c) and says nothing about
# concentration.
NUTRIENT_CLASSES = ("dairy", "egg", "legume", "nut", "grain")


def clustering_problems(day, foods):
    """One nutrient class bunched into a single sitting instead of spread.

    No threshold table and no new data: flag when a single meal holds more than
    half the day's items of one class. Scale-free, so it means the same thing
    for a three-meal day and a seven-meal day.

    It reports a fact it can verify -- three of the day's five dairy items are
    at dinner -- and does not claim that is harmful. The reason calcium is worth
    spreading, and what it does to iron absorption, is appendix material.
    """
    out = []
    for cls in NUTRIENT_CLASSES:
        per_meal = {slot: sum(1 for n, _ in items if cls in foods[n]["tags"])
                    for slot, items in day.items()}
        total = sum(per_meal.values())
        if total < 3:                      # too few to be bunched
            continue
        for slot, n in per_meal.items():
            if n > total / 2:
                out.append(("distribution",
                            f"{slot} holds {n} of the day's {total} {cls} items. "
                            f"Spreading them costs nothing and absorbs better; "
                            f"calcium and iron in particular saturate in one "
                            f"sitting."))
    return out
