"""
Turning a quantity and a food into words a person can act on.

This module exists because an earlier version used the food's dictionary key as
its display name, and those keys had a quantity inside them: `roti 1 medium`,
`egg white 1`, `paneer 100 g`. Applying a multiplier on top produced lines like
"3 x egg white 1" and "0.5 x paneer 100 g" in a document someone was meant to
cook from.

A food now carries a name, a unit, and macros for one unit. Nothing here knows
what a katori is; it only knows which units are weights, which are containers,
and which are the food itself.
"""

# Units measured out rather than counted. "50 g paneer", not "50 paneer".
MEASURED = {"g", "ml", "tsp", "tbsp"}

# Units that are a vessel or portion the food sits in. "1 katori rice".
CONTAINERS = {"katori", "bowl", "cup", "scoop", "serving", "plate", "glass"}

FRACTIONS = {0.25: "¼", 0.5: "½", 0.75: "¾",
             0.333: "⅓", 0.667: "⅔"}

# Plurals belong to the unit, not to each food, so a new food using katori does
# not have to restate it. A food may still override with its own unit_plural.
UNIT_PLURAL = {"katori": "katori", "scoop": "scoops", "bowl": "bowls",
               "cup": "cups", "serving": "servings", "plate": "plates",
               "glass": "glasses", "medium": "medium", "large": "large",
               "small": "small"}


def number(q):
    """1 -> '1'. 0.5 -> '½'. 1.5 -> '1½'. 2.0 -> '2'. 0.4 -> '0.4'."""
    if q == int(q):
        return str(int(q))
    whole, frac = int(q), round(q - int(q), 3)
    for value, glyph in FRACTIONS.items():
        if abs(frac - value) < 0.01:
            return f"{whole}{glyph}" if whole else glyph
    return f"{q:g}"


def food_name(name, food, q):
    """Only pluralise a name that declares a plural. Most do not: sabji, dal,
    curd and paneer stay as they are however many katori there were."""
    return food.get("name_plural", name) if q != 1 else name


def plural(food, unit, q):
    if q == 1:
        return unit
    return food.get("unit_plural") or UNIT_PLURAL.get(unit) or unit + "s"


def amount(name, q, food):
    """The phrase that goes in the document.

    Weighed:    50 g paneer      250 ml high-protein milk
    Container:  ½ katori rice    1 bowl salad     1 serving egg bhurji
    Itself:     2 roti           3 egg whites     1 banana
    """
    unit = food["unit"]
    if unit in MEASURED:
        return f"{number(q)} {unit} {name}"
    if unit in CONTAINERS:
        return f"{number(q)} {plural(food, unit, q)} {food_name(name, food, q)}"
    if unit == name:                      # the unit is the food: 2 roti
        return f"{number(q)} {plural(food, unit, q)}"
    if unit in ("medium", "large", "small"):   # 1 medium banana, 2 medium bananas
        return f"{number(q)} {unit} {food_name(name, food, q)}"
    return f"{number(q)} {plural(food, unit, q)}"   # 3 egg whites


def macros(q, food):
    """[kcal, protein, fat, carb, fibre] for this quantity."""
    return [q * v for v in food["per"]]
