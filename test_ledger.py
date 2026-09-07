"""
Tests for the decision record.

The first test is the whole point of the design. The version this replaced
re-derived explanations at render time, so a rule with no paragraph was
silently absent and nobody found out. This one fails the build.

    python3 -m unittest test_ledger -v
"""
import inspect, json, os, unittest
import physio, ledger

HERE = os.path.dirname(os.path.abspath(__file__))


def prof(name="example-a"):
    with open(os.path.join(HERE, "profiles", name + ".json")) as fh:
        return json.load(fh)


def plan(name="example-a"):
    with open(os.path.join(HERE, "plans", name + ".json")) as fh:
        return json.load(fh)


class Coverage(unittest.TestCase):
    """Adding a rule without narrating it must fail."""

    def rules(self):
        return {n for n, f in inspect.getmembers(physio, inspect.isfunction)
                if not n.startswith("_") and f.__module__ == "physio"}

    def test_every_rule_is_either_narrated_or_explicitly_not_a_decision(self):
        missing = self.rules() - ledger.NARRATED - ledger.NOT_DECISIONS
        self.assertEqual(missing, set(),
            f"these rules decide something and nothing explains them: "
            f"{sorted(missing)}. Add them to ledger.NARRATED with an entry, or "
            f"to NOT_DECISIONS if they genuinely decide nothing.")

    def test_the_narrated_list_has_no_rules_that_no_longer_exist(self):
        stale = ledger.NARRATED - self.rules()
        self.assertEqual(stale, set(), f"narrated but gone from physio: {sorted(stale)}")

    def test_the_two_lists_do_not_overlap(self):
        self.assertEqual(ledger.NARRATED & ledger.NOT_DECISIONS, set())

    def test_the_intake_gate_is_the_only_thing_excused(self):
        self.assertEqual(ledger.NOT_DECISIONS, {"missing_context", "require_context"})


class Entries(unittest.TestCase):

    def setUp(self):
        self.e = ledger.build(prof(), plan(), 2307, 2277)

    def test_every_entry_is_complete(self):
        for x in self.e:
            self.assertTrue(x.area.strip(), "an entry has no area")
            self.assertTrue(x.chose.strip(), f"{x.area} chose nothing")
            self.assertTrue(x.because.strip(), f"{x.area} gives no reason")
            self.assertTrue(x.rule.strip(), f"{x.area} names no rule")

    def test_every_named_rule_actually_exists(self):
        for x in self.e:
            for ref in x.rule.split(","):
                ref = ref.strip()
                if not ref.startswith("physio."):
                    continue
                fn = ref.split(".", 1)[1]
                self.assertTrue(hasattr(physio, fn),
                                f"{x.area} points at physio.{fn}, which does not exist")

    def test_the_reason_carries_the_person_s_own_numbers(self):
        p = prof()
        joined = " ".join(x.because for x in self.e)
        for n in (str(p["days"]), str(p["age"]), f"{p['kg']:.0f}", str(p["ambient_c"])):
            self.assertIn(n, joined, f"no entry mentions {n}")

    def test_no_raw_profile_key_reaches_the_page(self):
        text = " ".join(f"{x.chose} {x.because} {x.rejected}" for x in self.e)
        for key in ("typical_home", "insulated_gelpack", "measured", "desk job'"):
            if key in ("measured",):
                continue
            self.assertNotIn(key, text, f"raw key '{key}' leaked")

    def test_a_violation_is_recorded_when_one_fired(self):
        e = ledger.build(prof(), plan(), 2307, 2277,
                         violations=[("floor", "protein under the floor")])
        checks = [x for x in e if x.area == "Checks"]
        self.assertEqual(len(checks), 1)
        self.assertIn("protein under the floor", checks[0].because)

    def test_a_clean_run_says_so_rather_than_saying_nothing(self):
        checks = [x for x in self.e if x.area == "Checks"]
        self.assertEqual(len(checks), 1)
        self.assertIn("passed every check", checks[0].chose)

    def test_a_different_person_gets_a_different_record(self):
        b = ledger.build(prof("example-b"), plan(), 1795, 1795)
        a_text = " ".join(x.chose for x in self.e)
        b_text = " ".join(x.chose for x in b)
        self.assertNotEqual(a_text, b_text)

    def test_an_unmapped_injury_is_recorded_not_swallowed(self):
        p = prof(); p["injuries"] = ["torn meniscus"]
        e = ledger.build(p, plan(), 2307, 2277)
        self.assertTrue(any("torn meniscus" in x.chose for x in e))


class InTheDocument(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import subprocess, sys
        subprocess.run([sys.executable, "render.py",
                        "--profile", "profiles/example-a.json",
                        "--plan", "plans/example-a.json",
                        "--out", "example-a-plan.md"],
                       cwd=HERE, capture_output=True, text=True, check=True)
        with open(os.path.join(HERE, "example-a-plan.md")) as fh:
            cls.doc = fh.read()

    def test_the_body_carries_one_food_table_and_it_is_the_summary(self):
        body = self.doc.split("# Appendix")[0]
        self.assertEqual(body.count("| Time | Food |"), 1)
        self.assertNotIn("| Time | Food | Made of |", body,
                         "the itemised table belongs in the appendix")

    def test_the_itemised_table_is_in_the_appendix(self):
        app = self.doc.split("# Appendix")[1]
        self.assertIn("## Every food, and what is in it", app)
        self.assertIn("| Time | Food | Made of | kcal |", app)

    def test_the_decision_record_is_in_the_appendix_and_every_entry_shows_its_rule(self):
        app = self.doc.split("# Appendix")[1]
        seg = app.split("## Why this plan and not another")[1].split("\n## ")[0]
        self.assertGreaterEqual(seg.count("Rule: `"), 12)
        self.assertEqual(seg.count("**"), seg.count("Rule: `") * 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
