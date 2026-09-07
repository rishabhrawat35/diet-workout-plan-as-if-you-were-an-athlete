"""
Tests that read the rendered document.

Every defect these cover shipped in a document a person was meant to cook from,
and every one passed the existing 71 tests, because no test had ever looked at
what the output said. The numbers were right the whole time. The sentences were
not.

    python3 -m unittest test_render -v
"""
import json, os, re, subprocess, sys, unittest
import units

HERE = os.path.dirname(os.path.abspath(__file__))
FOODS = {k: v for k, v in json.load(
    open(os.path.join(HERE, "data/foods-india-egg-dairy.json"))).items()
    if not k.startswith("_")}


class FoodData(unittest.TestCase):
    """The keys used to carry a quantity, which is what produced '3 x egg white 1'."""

    def test_no_food_name_contains_a_digit_or_a_comma(self):
        for name in FOODS:
            self.assertNotRegex(name, r"[0-9,]", f"'{name}' has a quantity or a "
                                                 f"comma in its name")

    def test_every_food_declares_a_unit_and_five_macros(self):
        for name, f in FOODS.items():
            self.assertIn("unit", f, name)
            self.assertEqual(len(f["per"]), 5, name)
            for v in f["per"]:
                self.assertGreaterEqual(v, 0, name)

    def test_per_unit_macros_are_internally_consistent(self):
        """kcal must be within 12% of 4/9/4 on the macros, or a number is wrong."""
        for name, f in FOODS.items():
            k, p, fa, c, _ = f["per"]
            if k < 5:
                continue
            implied = p * 4 + fa * 9 + c * 4
            self.assertLess(abs(implied - k) / k, 0.12,
                            f"{name}: {k} kcal but macros imply {implied:.1f}")


class Wording(unittest.TestCase):

    def say(self, name, q):
        return units.amount(name, q, FOODS[name])

    def test_a_count_never_appears_twice(self):
        self.assertEqual(self.say("egg white", 3), "3 egg whites")
        self.assertEqual(self.say("roti", 2), "2 roti")
        self.assertEqual(self.say("boiled egg", 6), "6 boiled eggs")

    def test_weights_read_as_weights(self):
        self.assertEqual(self.say("paneer", 50), "50 g paneer")
        self.assertEqual(self.say("high-protein milk", 250), "250 ml high-protein milk")

    def test_fractions_are_fractions_not_decimals(self):
        self.assertEqual(self.say("rice", 0.5), "½ katori rice")
        self.assertNotIn("0.5", self.say("rice", 0.5))
        self.assertNotIn(" x ", self.say("rice", 0.5))

    def test_singular_and_plural_both_read_correctly(self):
        self.assertEqual(self.say("roti", 1), "1 roti")
        self.assertEqual(self.say("banana", 1), "1 medium banana")
        self.assertEqual(self.say("banana", 2), "2 medium bananas")
        self.assertEqual(self.say("whey in water", 2), "2 scoops whey in water")

    def test_a_name_is_never_pluralised_unless_it_declares_a_plural(self):
        for n in ("sabji", "dal", "curd", "paneer", "rice"):
            self.assertNotIn(n + "s", self.say(n, 2), f"{n} was pluralised")

    def test_nothing_renders_with_a_multiplier(self):
        for name, f in FOODS.items():
            for q in (0.5, 1, 2, 3, 50, 250):
                self.assertNotIn(" x ", units.amount(name, q, f))


class RenderedDocument(unittest.TestCase):
    """Read the file that gets printed."""

    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, "render.py",
                        "--profile", "profiles/example-a.json",
                        "--plan", "plans/example-a.json",
                        "--out", "example-a-plan.md"],
                       cwd=HERE, capture_output=True, text=True, check=True)
        with open(os.path.join(HERE, "example-a-plan.md")) as fh:
            cls.doc = fh.read()

    def rows(self, label):
        seg = self.doc.split(f"**{label}**")[1].split("**Whole day**")[0]
        out = []
        for line in seg.split("\n"):
            if not line.startswith("|") or "**" in line or "---" in line or "Time |" in line:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 7 and cells[3]:
                out.append([float(c) for c in cells[3:7]])
        return out

    def whole_day(self, label):
        line = self.doc.split(f"**{label}**")[1].split("**Whole day**")[1].split("\n")[0]
        return [float(c.strip().strip("*")) for c in line.strip().strip("|").split("|")
                if c.strip()]

    def test_the_printed_columns_add_up(self):
        """A reader with a calculator must get the printed total."""
        for label in ("Training day", "Rest day"):
            items = self.rows(label)
            for i, what in enumerate(("kcal", "protein", "fat", "carbs")):
                got = round(sum(r[i] for r in items), 1)
                want = self.whole_day(label)[i]
                self.assertAlmostEqual(got, want, places=1,
                    msg=f"{label} {what}: rows sum to {got}, total says {want}")

    def test_the_header_matches_the_table(self):
        m = re.search(r"(\d+) calories \| ([\d.]+) g protein \| ([\d.]+) g fat "
                      r"\| (\d+) g carbohydrate", self.doc)
        self.assertIsNotNone(m, "header line not found")
        self.assertEqual([float(m.group(i)) for i in (1, 2, 3, 4)],
                         self.whole_day("Training day"),
                         "the header and the table disagree")

    def test_both_days_are_shown(self):
        self.assertIn("**Training day**", self.doc)
        self.assertIn("**Rest day**", self.doc)

    def test_the_document_has_no_quantity_artefacts(self):
        body = self.doc
        for bad in (" x roti", " x egg white", "0.5 x", " x boiled egg", " x paneer"):
            self.assertNotIn(bad, body, f"'{bad}' is back")

    def test_every_food_row_names_what_it_is_made_of_or_needs_nothing(self):
        composites = [n for n, f in FOODS.items() if f["unit"] == "serving"]
        for n in composites:
            self.assertIn("made_of", FOODS[n], f"{n} is a dish with no recipe")
            self.assertIn(FOODS[n]["made_of"], self.doc)

    def test_the_rest_day_instructions_are_derived_not_written(self):
        with open(os.path.join(HERE, "plans/example-a.json")) as fh:
            plan = json.load(fh)
        self.assertNotIn("rest_day_changes", plan,
                         "prose instructions can contradict the data")
        self.assertIn("day_rest", plan)

    def test_no_raw_data_key_leaks_into_prose(self):
        for key in ("insulated_gelpack", "typical_home", "day_rest", "made_of"):
            self.assertNotIn(key, self.doc, f"raw key '{key}' is in the document")


if __name__ == "__main__":
    unittest.main(verbosity=2)
