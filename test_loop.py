"""
Tests that the loop cannot clash or spin.

The last two are the ones that matter: an oscillating agent pair and an
impossible constraint set both have to terminate, and neither may be settled
by letting a low-ranked constraint override a high-ranked one.

    python3 -m unittest test_loop -v
"""
import unittest
import coherence as C
import resolve as Rz

FOODS = {
  "roti":        dict(role="carrier", cuisine=["indian"], palatability=3),
  "rice":        dict(role="carrier", cuisine=["indian"], palatability=3),
  "dal":         dict(role="wet",     cuisine=["indian"], palatability=4),
  "egg bhurji":  dict(role="wet",     cuisine=["indian"], palatability=5),
  "boiled egg":  dict(role="anchor",  cuisine=[],         palatability=2),
  "salad":       dict(role="side",    cuisine=[],         palatability=2),
  "curd":        dict(role="wet",     cuisine=["indian"], palatability=4),
  "pasta":       dict(role="carrier", cuisine=["italian"],palatability=4),
  "pesto":       dict(role="wet",     cuisine=["italian"],palatability=5),
}


class Coherence(unittest.TestCase):

    def test_dry_roti_is_caught(self):
        prob = C.meal_problems([("roti",2),("boiled egg",3),("salad",1)], FOODS)
        self.assertIn("coherence", [k for k,_ in prob])

    def test_a_wet_partner_fixes_it(self):
        prob = C.meal_problems([("roti",2),("egg bhurji",1)], FOODS)
        self.assertNotIn("coherence", [k for k,_ in prob])

    def test_a_drink_or_side_does_not_rescue_a_carrier(self):
        prob = C.meal_problems([("roti",2),("salad",1)], FOODS)
        self.assertIn("coherence", [k for k,_ in prob])

    def test_cuisine_clash_is_caught(self):
        prob = C.meal_problems([("roti",2),("pesto",1)], FOODS)
        self.assertIn("coherence", [k for k,_ in prob])

    def test_neutral_items_never_cause_a_clash(self):
        prob = C.meal_problems([("roti",2),("dal",1),("boiled egg",2),("salad",1)], FOODS)
        self.assertEqual([k for k,_ in prob], [])

    def test_a_grim_meal_is_flagged(self):
        prob = C.meal_problems([("boiled egg",4),("salad",2)], FOODS)
        self.assertIn("palatability", [k for k,_ in prob])

    def test_identical_days_are_flagged_as_monotony(self):
        day = {"breakfast":[("roti",2),("dal",1)]}
        prob = C.week_problems({"mon":day,"tue":day,"wed":day}, FOODS)
        self.assertIn("variety", [k for k,_ in prob])


class Precedence(unittest.TestCase):

    def test_the_order_is_the_one_the_design_intends(self):
        self.assertLess(Rz.RANK["safety"], Rz.RANK["palatability"])
        self.assertLess(Rz.RANK["refusal"], Rz.RANK["safety"])
        self.assertLess(Rz.RANK["floor"], Rz.RANK["coherence"])
        self.assertLess(Rz.RANK["coherence"], Rz.RANK["variety"])

    def test_palatability_can_never_buy_a_safety_exception(self):
        """An agent that fixes enjoyment by breaking safety must be rejected."""
        def evaluate(plan):
            v = []
            if plan.get("carried_curry"):  v.append(("safety","curry held 9 h"))
            if plan.get("bland"):          v.append(("palatability","palatability"))
            return v
        tempter = ("tempter", lambda p, t: {**p, "carried_curry": True, "bland": False})
        plan = {"carried_curry": False, "bland": True}
        out, trace, left = Rz.resolve(plan, evaluate, [tempter])
        self.assertFalse(out["carried_curry"], "safety was traded for enjoyment")


class Termination(unittest.TestCase):

    def test_an_oscillating_pair_of_agents_still_terminates(self):
        """Two agents that undo each other must not spin."""
        def evaluate(plan):
            return [] if plan["n"] == 5 else [("palatability", f"n={plan['n']}")]
        up   = ("up",   lambda p, t: {"n": p["n"] + 1})
        down = ("down", lambda p, t: {"n": p["n"] - 1})
        out, trace, left = Rz.resolve({"n": 0}, evaluate, [up, down])
        self.assertLessEqual(len(trace), Rz.MAX_ROUNDS)

    def test_a_no_op_agent_stops_the_loop_immediately(self):
        def evaluate(plan): return [("variety", "same every day")]
        useless = ("useless", lambda p, t: None)
        out, trace, left = Rz.resolve({}, evaluate, [useless])
        self.assertEqual(len(trace), 1)
        self.assertIn("no agent improved it", trace[0][2])

    def test_an_impossible_hard_constraint_raises_rather_than_looping(self):
        def evaluate(plan): return [("floor", "protein floor unreachable")]
        with self.assertRaises(Rz.Unsatisfiable) as cm:
            Rz.resolve({}, evaluate, [("none", lambda p, t: None)])
        self.assertIn("Change an input", str(cm.exception))

    def test_a_surviving_soft_violation_does_not_raise(self):
        def evaluate(plan): return [("palatability", "a bit dull")]
        out, trace, left = Rz.resolve({}, evaluate, [("none", lambda p, t: None)])
        self.assertEqual([k for k, _ in left], ["palatability"])

    def test_the_round_cap_is_never_exceeded_even_with_endless_agents(self):
        calls = {"n": 0}
        def evaluate(plan):
            calls["n"] += 1
            return [("coherence", "never satisfied")] if plan["i"] < 10**9 else []
        greedy = ("greedy", lambda p, t: {"i": p["i"] + 1})
        try:
            Rz.resolve({"i": 0}, evaluate, [greedy])
        except Rz.Unsatisfiable:
            pass
        self.assertLess(calls["n"], 200, "loop ran away")

    def test_progress_is_strict_so_a_lateral_move_is_refused(self):
        """An agent that swaps one violation for another of equal rank
        must not be accepted, or two such agents would ping-pong forever."""
        def evaluate(plan):
            return [("coherence", plan["which"])]
        swap = ("swap", lambda p, t: {"which": "b" if p["which"] == "a" else "a"})
        try:
            out, trace, left = Rz.resolve({"which": "a"}, evaluate, [swap])
        except Rz.Unsatisfiable:
            out = None
        self.assertTrue(out is None or out["which"] == "a")


if __name__ == "__main__":
    unittest.main(verbosity=2)


class Categories(unittest.TestCase):
    """Foods the person rotates within are not monotony."""

    FOODS_CAT = dict(FOODS)
    FOODS_CAT["sabji"] = dict(role="wet", cuisine=["indian"], palatability=4,
                              category=["bhindi","lauki","baingan","palak","gobi"])

    def test_a_category_slot_is_not_flagged(self):
        day = {"dinner": [("sabji", 1), ("roti", 2)]}
        prob = C.week_problems({"mon": day, "tue": day, "wed": day}, self.FOODS_CAT)
        self.assertEqual(prob, [])

    def test_a_fixed_slot_is_still_flagged(self):
        day = {"dinner": [("dal", 1), ("roti", 2)]}
        prob = C.week_problems({"mon": day, "tue": day}, self.FOODS_CAT)
        self.assertIn("variety", [k for k, _ in prob])

    def test_two_real_variants_pass_without_any_category(self):
        prob = C.week_problems(
            {"mon": {"dinner": [("dal", 1), ("roti", 2)]},
             "tue": {"dinner": [("curd", 1), ("rice", 1)]}}, self.FOODS_CAT)
        self.assertEqual(prob, [])
