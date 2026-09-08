"""
Tests that the loop cannot clash or spin.

The last two are the ones that matter: an oscillating agent pair and an
impossible constraint set both have to terminate, and neither may be settled
by letting a low-ranked constraint override a high-ranked one.

    python3 -m unittest test_loop -v
"""
import unittest
import coherence as C

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

class UnknownExercise(unittest.TestCase):
    """An exercise the library does not know must be reported, not crash.

    It used to raise KeyError and take the whole audit down, which tells the
    person nothing about the exercise and hides every other problem behind it.
    """

    LIB = {"leg press": dict(pattern="knee_extension", equipment="leg press",
                             load_class="heavy", uses=[], tolerability=4)}

    def test_an_unknown_exercise_is_a_refusal_not_an_exception(self):
        out = C.session_problems([{"name": "zercher good morning", "sets": 3}],
                                 self.LIB, ["leg press"], 60)
        self.assertEqual([k for k, _ in out], ["refusal"])
        self.assertIn("zercher good morning", out[0][1])

    def test_the_rest_of_the_session_is_still_checked(self):
        out = C.session_problems(
            [{"name": "zercher good morning", "sets": 3},
             {"name": "leg press", "sets": 4}],
            self.LIB, [], 60)
        kinds = [k for k, _ in out]
        self.assertEqual(kinds.count("refusal"), 2)   # unknown, and no leg press

    def test_a_known_session_is_unaffected(self):
        out = C.session_problems([{"name": "leg press", "sets": 4}],
                                 self.LIB, ["leg press"], 60)
        self.assertEqual(out, [])
