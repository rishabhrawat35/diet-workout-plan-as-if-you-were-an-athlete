"""
Tests for completeness and for the staged loop.

The first class exists because supplements, post-workout feeding and dry fruits
each went missing between drafts and none was caught by the code.

    python3 -m unittest test_contract -v
"""
import unittest
import contract as K

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
