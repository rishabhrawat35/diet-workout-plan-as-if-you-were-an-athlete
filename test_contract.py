"""
Tests for completeness and for the staged loop.

The first class exists because supplements, post-workout feeding and dry fruits
each went missing between drafts and none was caught by the code.

    python3 -m unittest test_contract -v
"""
import unittest
import contract as K
import resolve as Rz

FULL = {k: "content" for k in K.ALL}


class Completeness(unittest.TestCase):

    def test_a_full_plan_passes(self):
        self.assertTrue(K.require(FULL))

    def test_every_section_is_individually_load_bearing(self):
        for k in K.ALL:
            d = dict(FULL); d.pop(k)
            with self.assertRaises(K.Incomplete, msg=f"{k} not enforced"):
                K.require(d)

    def test_an_empty_section_counts_as_missing(self):
        d = dict(FULL); d["supplements"] = "   "
        self.assertIn("supplements", " ".join(K.check(d)))

    def test_the_three_that_actually_went_missing_are_covered(self):
        for k in ("supplements", "peri_workout", "downside"):
            self.assertIn(k, K.ALL)

    def test_the_refusal_names_what_to_add(self):
        d = dict(FULL); d.pop("measurement")
        with self.assertRaises(K.Incomplete) as cm:
            K.require(d)
        self.assertIn("trigger", str(cm.exception))


class StagedLoop(unittest.TestCase):

    def ev_factory(self, state):
        def evaluate(plan):
            v = []
            if plan.get("unsafe"):  v.append(("safety", "held too long"))
            if plan.get("dry"):     v.append(("coherence", "dry meal"))
            if plan.get("dull"):    v.append(("palatability", "grim"))
            return v
        return evaluate

    def test_a_later_stage_cannot_reopen_an_earlier_one(self):
        evaluate = self.ev_factory(None)
        # this agent fixes dullness by making the food unsafe
        tempter = ("tempter", lambda p, t: {**p, "dull": False, "unsafe": True})
        plan = {"unsafe": False, "dry": False, "dull": True}
        out, trace, left = Rz.stage_resolve(
            plan, evaluate, {"palatability": [tempter]}, lambda p, k: None)
        self.assertFalse(out["unsafe"])
        self.assertTrue(any("would reopen safety" in t[3] for t in trace))

    def test_a_challenger_can_block_a_bad_proposal(self):
        evaluate = self.ev_factory(None)
        fixer = ("fixer", lambda p, t: {**p, "dull": False})
        veto = lambda p, k: "not actually better" if k == "palatability" else None
        out, trace, left = Rz.stage_resolve(
            {"unsafe": False, "dry": False, "dull": True}, evaluate,
            {"palatability": [fixer]}, veto)
        self.assertTrue(out["dull"])
        self.assertTrue(any("challenged" in t[3] for t in trace))

    def test_a_repeating_challenger_cannot_extend_a_stage(self):
        evaluate = self.ev_factory(None)
        fixer = ("fixer", lambda p, t: {**p, "dull": False})
        out, trace, left = Rz.stage_resolve(
            {"unsafe": False, "dry": False, "dull": True}, evaluate,
            {"palatability": [fixer]}, lambda p, k: "same objection every time")
        objections = [t for t in trace if "challenged" in t[3]]
        self.assertEqual(len(objections), 1, "duplicate objections not collapsed")

    def test_total_work_is_bounded_by_stages_times_cap(self):
        calls = {"n": 0}
        def evaluate(plan):
            calls["n"] += 1
            return [("coherence", "never fixed")]
        greedy = ("greedy", lambda p, t: {"i": p.get("i", 0) + 1})
        try:
            Rz.stage_resolve({}, evaluate, {"coherence": [greedy]},
                             lambda p, k: None, max_rounds=4)
        except Rz.Unsatisfiable:
            pass
        self.assertLess(calls["n"], len(Rz.PRECEDENCE) * 4 * 4)

    def test_a_clean_plan_needs_no_rounds(self):
        out, trace, left = Rz.stage_resolve(
            {}, lambda p: [], {}, lambda p, k: None)
        self.assertEqual(trace, [])
        self.assertEqual(left, [])

    def test_stages_run_in_precedence_order(self):
        evaluate = self.ev_factory(None)
        seen = []
        def agent(p, t):
            seen.append(t[0]); return None
        try:
            Rz.stage_resolve(
                {"unsafe": True, "dry": True, "dull": True}, evaluate,
                {k: [("a", agent)] for k in Rz.PRECEDENCE}, lambda p, k: None)
        except Rz.Unsatisfiable:
            pass   # safety is unfixable here; the ordering is what is under test
        self.assertEqual(seen, ["safety", "coherence", "palatability"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
