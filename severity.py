"""
How bad a problem is, and therefore which one gets fixed first.

This ordering is the design. A lower-ranked constraint may never be satisfied by
breaking a higher-ranked one: enjoyment cannot buy a food-safety exception at
any price.

It lived in resolve.py alongside an agent-and-challenger loop that the engine
never called. The loop is gone; the ordering was always the useful part.
"""

PRECEDENCE = (
    "refusal",        # 0  life stage, contraindicated movement, missing equipment
    "safety",         # 1  food held past its limit for that temperature and storage
    "floor",          # 2  a hard bound broken: protein, fat, fibre, volume, loss rate
    "energy",         # 3  session over budget, macros that do not sum
    "coherence",      # 4  a carrier with nothing wet, two heavy lifts back to back
    "distribution",   # 5  a nutrient bunched into one sitting instead of spread
    "palatability",   # 6  a meal or session nobody will keep doing
)

# "variety" was here. Nothing raised it: the only check that did assumed a
# seven-day rotation the plan does not model, and the one other user was a
# volume ceiling breach mislabelled for weeks. Removed rather than kept as a
# level nothing can reach.

RANK = {k: i for i, k in enumerate(PRECEDENCE)}
