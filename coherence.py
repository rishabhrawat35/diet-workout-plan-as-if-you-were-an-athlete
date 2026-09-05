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

# ============================================================ MEALS

# carrier  needs something wet to be eaten with (roti, rice, bread)
# wet      can be eaten with a carrier (dal, sabji, curry, bhurji, curd)
# anchor   the protein centre
# side     eaten alongside; does not rescue a carrier
# drink    liquid; never rescues a carrier
# fruit    eaten alone or after
MEAL_ROLES = ("carrier", "wet", "anchor", "side", "drink", "fruit")


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


# ============================================================ ROTATION

def week_problems(days, lib):
    """A slot identical every day is an adherence defect -- unless it is built
    on a category the person rotates within. "Sabji" is bhindi, lauki, palak;
    "row" is cable, chest-supported, dumbbell. The first version could not tell
    the difference and demanded variants for slots that already varied."""
    out = []
    slots = {s for d in days.values() for s in d}
    for slot in slots:
        variants = {tuple(sorted(n for n, _ in d[slot]))
                    for d in days.values() if slot in d}
        if len(variants) >= 2:
            continue
        rotates = any(lib[n].get("category") for d in days.values()
                      if slot in d for n, _ in d[slot])
        if not rotates:
            out.append(("variety", f"{slot} is identical every time and contains "
                        f"nothing to rotate within. Give it a second variant."))
    return out
