"""
The agentic loop that settles a meal when the constraints disagree.

Clashes are real: the palatability agent wants ghee in the sabji, the energy
agent wants the calories back, the safety agent bans the carried curry, the
micronutrient agent wants a source none of the others will pay for. Left to
argue freely they deadlock, or they oscillate -- add paneer, remove paneer,
add paneer.

Two mechanisms stop that, and neither depends on the agents behaving well:

1. PRECEDENCE. Constraints are strictly ranked. A lower-ranked constraint may
   never be satisfied by breaking a higher-ranked one. Enjoyment cannot buy a
   food-safety exception at any price.

2. STRICT IMPROVEMENT. Each round must lower the (worst_rank, count) pair
   lexicographically. A round that does not is the last round: the loop stops
   and reports what is unsatisfiable instead of trying again.

Termination is therefore not a matter of trusting the agents. The state that
must decrease is finite and decreases monotonically, and the round cap bounds
it regardless.
"""

MAX_ROUNDS = 8

# Lower number wins. This ordering is the design; changing it changes what the
# system is willing to trade away.
PRECEDENCE = (
    "refusal",        # 0  life stage, medical. Never traded.
    "safety",         # 1  food safety. Never traded.
    "floor",          # 2  protein, fat, fibre floors.
    "energy",         # 3  calorie target within tolerance.
    "coherence",      # 4  is it a meal at all.
    "distribution",   # 5  protein spread across sittings.
    "variety",        # 6  monotony.
    "palatability",   # 7  optimised last, never at the cost of the above.
)
RANK = {k: i for i, k in enumerate(PRECEDENCE)}


class Unsatisfiable(Exception):
    """Raised with the surviving violations. Never raised for a soft one."""


def _state(violations):
    """Sort key where smaller is genuinely better.

    The first version returned (worst_rank, count) and compared with <, which
    inverted the meaning: a safety violation has rank 1 and a palatability one
    has rank 7, so (1, 1) < (7, 1) made "broke food safety" look like an
    improvement on "slightly dull". Negating the rank fixes the direction.
    Clean state sorts smallest of all.
    """
    if not violations:
        return (-len(PRECEDENCE) - 1, 0)
    worst = min(RANK[k] for k, _ in violations)
    return (-worst, sum(1 for k, _ in violations if RANK[k] == worst))


def resolve(plan, evaluate, agents, max_rounds=MAX_ROUNDS):
    """
    evaluate(plan) -> [(kind, message)]
    agents: [(name, fn)] where fn(plan, violation) -> candidate plan or None

    Returns (plan, trace). Raises Unsatisfiable only if a hard violation
    (rank <= RANK['energy']) survives.
    """
    trace = []
    seen = set()
    best = _state(evaluate(plan))

    for rnd in range(1, max_rounds + 1):
        vios = evaluate(plan)
        if not vios:
            trace.append((rnd, "clean", "no violations"))
            break

        # Always work the highest-precedence violation first.
        target = min(vios, key=lambda v: RANK[v[0]])
        applied = None

        for name, fn in agents:
            cand = fn(plan, target)
            if cand is None:
                continue
            key = (target[0], name, repr(sorted(map(str, cand.items()))))
            if key in seen:            # this agent already tried this fix
                continue
            seen.add(key)
            cand_state = _state(evaluate(cand))
            if cand_state < best:      # strict improvement only
                plan, best, applied = cand, cand_state, name
                break

        trace.append((rnd, target[0], f"{applied or 'no agent improved it'}"
                                      f" -- {target[1][:60]}"))
        if applied is None:
            break                      # no round may repeat without progress

    left = evaluate(plan)
    hard = [v for v in left if RANK[v[0]] <= RANK["energy"]]
    if hard:
        raise Unsatisfiable(
            "Cannot satisfy these without breaking something ranked higher:\n  "
            + "\n  ".join(f"[{k}] {m}" for k, m in hard)
            + "\nChange an input rather than the plan: more calories, a "
              "different storage option, or a wider protein source list.")
    return plan, trace, left


# --------------------------------------------------------------- staged loop

def stage_resolve(plan, evaluate, agents_by_rank, challenger, max_rounds=4):
    """One agent/challenger loop per precedence rank, in rank order.

    Rather than one flat loop arguing about everything at once, each rank is
    settled and then frozen. A later stage may not touch what an earlier stage
    decided, which is what makes enjoyment structurally unable to reopen food
    safety -- it is not a rule the loop has to remember, it is a stage it
    cannot reach backwards into.

    challenger(plan, kind) -> objection string or None. A proposal is accepted
    only if the challenger cannot break it. Objections are deduplicated, so a
    challenger repeating itself cannot extend a stage.

    Termination: stages are finite and ordered, each stage is capped, and no
    stage can undo an earlier one. Total work is bounded by
    len(PRECEDENCE) * max_rounds regardless of how the agents behave.
    """
    trace, frozen = [], []
    for kind in PRECEDENCE:
        agents = agents_by_rank.get(kind, [])
        seen_objections = set()
        for rnd in range(1, max_rounds + 1):
            vios = [v for v in evaluate(plan) if v[0] == kind]
            if not vios:
                break
            target = vios[0]
            applied = None
            for name, fn in agents:
                cand = fn(plan, target)
                if cand is None:
                    continue
                # A candidate may not reopen anything already frozen.
                reopened = [v for v in evaluate(cand)
                            if PRECEDENCE.index(v[0]) < PRECEDENCE.index(kind)]
                if reopened:
                    trace.append((kind, rnd, name,
                                  f"rejected: would reopen {reopened[0][0]}"))
                    continue
                obj = challenger(cand, kind)
                if obj:
                    h = (kind, obj)
                    if h not in seen_objections:
                        seen_objections.add(h)
                        trace.append((kind, rnd, name, f"challenged: {obj[:50]}"))
                    continue
                plan, applied = cand, name
                trace.append((kind, rnd, name, "accepted"))
                break
            if applied is None:
                trace.append((kind, rnd, "-", "no proposal survived; stage closed"))
                break
        frozen.append(kind)
    left = evaluate(plan)
    hard = [v for v in left if RANK[v[0]] <= RANK["energy"]]
    if hard:
        raise Unsatisfiable(
            "Cannot satisfy these without breaking something ranked higher:\n  "
            + "\n  ".join(f"[{k}] {m}" for k, m in hard))
    return plan, trace, left
