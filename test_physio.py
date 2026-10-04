"""
Physiology and intake tests.

The first group exists because the engine once read a person's sex and never
used it, assumed a cooking-fat practice, assumed an ambient temperature, and
reported its missing intake through a print statement rather than refusing.

    python3 -m unittest discover -p 'test_*.py'
"""
import unittest, subprocess, sys, os, json, tempfile
import physio as P, blocks, myths

HERE = os.path.dirname(os.path.abspath(__file__))


def person(**kw):
    d = dict(sex="m", age=30, kg=80.0, cm=178.0, waist_cm=95.0, sleep_h=7.0,
             training_age_yrs=5, medically_cleared=True,
             detrained=False, gym_traffic="shared", pregnant=False,
             postpartum_weeks=False, menstrual_status="cycling",
             job="desk", steps=9000, days=5, minutes=60,
             equipment=["cable stack"], injuries=[], goals=[{"want": "size", "of": "calves"}],
             ambient_c=23, storage="insulated_gelpack", hold_hours=6,
             protein_sources=["egg"], cooking_fat="typical_home",
             eating_occasions=6, activities=[])
    d.update(kw); return d


class IntakeGate(unittest.TestCase):
    def test_complete_profile_passes(self):
        self.assertTrue(P.require_context(person()))

    def test_every_required_field_is_load_bearing(self):
        """Two of these are asked only of women, so the fixture is run as both."""
        for sex in ("m", "f"):
            for f in P.required_for(person(sex=sex)):
                d = person(sex=sex); d[f] = None
                with self.assertRaises(P.IntakeIncomplete,
                                       msg=f"{f} not enforced for sex={sex}"):
                    P.require_context(d)

    def test_required_and_the_keys_the_code_reads_agree(self):
        """The one axis that had no coverage, which is where the bugs were.

        Every other enforcement mechanism in this engine fires on something the
        code can enumerate from itself: ledger.NARRATED enumerates functions,
        test_severity enumerates severity strings, contract.ALL enumerates
        document sections. REQUIRED was a hand-maintained list calibrated
        against the intake script rather than against what the modules read.

        Both halves of this test have a real defect behind them. `detrained`
        was read and not gated, so omitting it silently removed the four-week
        ramp. `eating_occasions` and `protein_sources` were gated and read
        nowhere, so the intake refused to run without an answer it then threw
        away.
        """
        import re
        mods = ("physio.py", "audit.py", "coherence.py", "blocks.py",
                "render.py", "ledger.py", "myths.py", "units.py")
        pat = re.compile(r"""p(?:rof)?\s*(?:\[\s*["'](\w+)["']\s*\]"""
                         r"""|\.get\(\s*["'](\w+)["'])""")
        read = set()
        for m in mods:
            with open(os.path.join(HERE, m)) as fh:
                for a, b in pat.findall(fh.read()):
                    read.add(a or b)

        known = set(P.REQUIRED) | set(P.NOT_GATED)
        ungated = sorted(read - known)
        self.assertEqual(ungated, [], "profile keys read but neither required "
                                      "nor listed in physio.NOT_GATED with a "
                                      "reason: " + ", ".join(ungated))

        unread = sorted(set(P.REQUIRED) - read)
        self.assertEqual(unread, [], "required fields that no module reads, so "
                                     "the intake refuses to run without an "
                                     "answer it then ignores: "
                                     + ", ".join(unread))

    def test_a_man_is_not_asked_whether_he_is_pregnant(self):
        self.assertNotIn("pregnant", P.required_for(person(sex="m")))
        self.assertIn("pregnant", P.required_for(person(sex="f")))

    def test_the_gate_raises_it_does_not_report(self):
        d = person(); d["equipment"] = None
        self.assertTrue(P.missing_context(d))
        self.assertRaises(P.IntakeIncomplete, P.require_context, d)


class Energy(unittest.TestCase):
    def test_bmr_differs_by_sex_by_exactly_166(self):
        self.assertAlmostEqual(P.bmr(person(sex="m")) - P.bmr(person(sex="f")), 166)

    def test_activity_factor_tracks_the_standard_table(self):
        for kw, want in [(dict(job="desk", days=0, steps=4000), 1.20),
                         (dict(job="desk", days=3, steps=6000), 1.375),
                         (dict(job="desk", days=5, steps=9000), 1.55),
                         (dict(job="physical", days=6, steps=12000), 1.90)]:
            self.assertLess(abs(P.activity_factor(person(**kw)) - want), 0.06)

    def test_home_cooking_costs_more_than_measured(self):
        gap = P.cooking_fat_g(person(cooking_fat="typical_home")) - \
              P.cooking_fat_g(person(cooking_fat="measured"))
        self.assertGreaterEqual(gap * 9 * 2, 100, "the error that was missed was ~210 kcal")


class Protein(unittest.TestCase):
    def test_deficit_floor_meets_the_breakpoint(self):
        self.assertAlmostEqual(P.protein_target_g(person(), True)[0] / 80, 1.9, places=2)

    def test_older_adults_need_more_not_less(self):
        self.assertGreater(P.protein_target_g(person(age=65), True)[0],
                           P.protein_target_g(person(age=30), True)[0])

    def test_distribution_needs_enough_sittings_not_all(self):
        self.assertTrue(P.distribution_ok([60, 34, 25, 33, 25, 2], person())[0])
        self.assertFalse(P.distribution_ok([150, 10, 10, 5, 5], person())[0])


class Sessions(unittest.TestCase):
    def test_a_shared_gym_costs_more_than_an_empty_one(self):
        self.assertGreater(P.sec_per_set(person(gym_traffic="shared")),
                           P.sec_per_set(person(gym_traffic="empty")))

    def test_pairing_buys_real_capacity(self):
        solo = P.session_minutes(person(), 18, 0)
        paired = P.session_minutes(person(), 18, 7)
        self.assertLess(paired, solo)
        self.assertLess(paired, 61)


class Injuries(unittest.TestCase):
    def test_lumbar_history_bans_spinal_loading(self):
        m = [x for x, _ in P.banned_movements(person(injuries=["lumbar disc"]))]
        self.assertIn("conventional deadlift", m)
        self.assertIn("sit-up", m)

    def test_unmapped_injuries_are_referred_not_swallowed(self):
        p = person(injuries=["torn meniscus"])
        self.assertEqual(P.banned_movements(p), [])
        self.assertTrue(any("torn meniscus" in r for r in P.refer_out(p)))


class Refusals(unittest.TestCase):
    def test_minors_pregnancy_postpartum_and_uncleared_elderly(self):
        for kw in (dict(age=16), dict(pregnant=True), dict(postpartum_weeks=6),
                   dict(age=70, medically_cleared=False)):
            self.assertIsNotNone(P.life_stage_stop(person(**kw)), kw)

    def test_a_normal_adult_passes(self):
        self.assertIsNone(P.life_stage_stop(person()))


class Blocks(unittest.TestCase):
    def test_the_diet_break_lands_on_a_deload(self):
        p = person(detrained=True)
        rows = blocks.calendar(p, 2300, P.tdee(p))
        br = [r for r in rows if r.get("diet_break")]
        self.assertEqual(len(br), 1)
        self.assertEqual(br[0]["kind"], "deload",
                         "diet break must coincide with a deload, not float free")

    def test_a_deload_week_is_eaten_above_the_deficit(self):
        p = person()
        rows = blocks.calendar(p, 2300, P.tdee(p))
        dl = [r for r in rows if r["kind"] == "deload" and not r.get("diet_break")]
        self.assertTrue(all(r["kcal"] > 2300 for r in dl))

    def test_the_calendar_covers_every_week_exactly_once(self):
        p = person(detrained=True)
        rows = blocks.calendar(p, 2300, P.tdee(p))
        weeks = [w for r in rows for w in range(r["from"], r["to"] + 1)]
        self.assertEqual(weeks, list(range(1, 25)))

    def test_every_block_kind_carries_an_instruction(self):
        """A block label the reader cannot act on is a claim the plan does not back.

        The calendar printed "reintroduction" for four weeks and "build" for the
        rest, and no instruction anywhere in the document differed between them.
        """
        import itertools
        kinds = set()
        for age, ta, sleep, detr, inj in itertools.product(
                (18, 30, 55, 79), (0, 1, 3, 10), (5.0, 6.4, 7.0, 9.0),
                (True, False), ([], ["lumbar disc"])):
            p = person(age=age, training_age_yrs=ta, sleep_h=sleep,
                       detrained=detr, injuries=inj)
            kinds |= {r["kind"] for r in blocks.calendar(p, 2300, P.tdee(p))}
        missing = kinds - set(blocks.BLOCK_INSTRUCTION)
        self.assertEqual(missing, set(),
                         f"block kinds with no instruction: {sorted(missing)}")
        unused = set(blocks.BLOCK_INSTRUCTION) - kinds
        self.assertEqual(unused, set(),
                         f"instructions for kinds nothing emits: {sorted(unused)}")

    def test_every_calendar_build_can_produce_holds_its_invariants(self):
        """These were runtime checks in blocks.problems until they were moved here.

        They were checking the output of blocks.build against properties build
        guarantees by construction, so at runtime they could never fire -- a
        sweep of 10,416 profiles raised nothing. As tests they are worth
        keeping: they are what would catch a future edit to build. The sweep is
        trimmed here to the axes build actually branches on.
        """
        import itertools
        seen = 0
        for age, ta, sleep, detr, inj in itertools.product(
                (18, 30, 55, 79), (0, 1, 3, 10), (5.0, 6.4, 7.0, 9.0),
                (True, False), ([], ["lumbar disc"])):
            p = person(age=age, training_age_yrs=ta, sleep_h=sleep,
                       detrained=detr, injuries=inj)
            rows = blocks.calendar(p, 2300, P.tdee(p))
            seen += 1
            kinds = [r["kind"] for r in rows]
            self.assertIn("deload", kinds, p)
            if detr or inj:
                self.assertIn("reintroduction", kinds, p)
            self.assertTrue(any(r.get("diet_break") for r in rows), p)
            for r in rows:
                if r.get("diet_break"):
                    self.assertEqual(r["kind"], "deload", p)
            self.assertEqual(sum(r["to"] - r["from"] + 1 for r in rows), 24, p)
            gap, run = P.deload_every_weeks(p), 0
            for r in rows:
                if r["kind"] == "deload":
                    run = 0
                elif r["kind"] != "reintroduction":
                    run += r["to"] - r["from"] + 1
                    self.assertLessEqual(run, gap, p)
        self.assertEqual(seen, 256)


class GoalsOnlyTighten(unittest.TestCase):
    """A goal may add a bound. It may never remove one.

    This is the whole safety boundary of personalisation. Without it, a goal
    field is a place for a user to talk the engine out of its own floors --
    declare the right thing and the protein floor, the loss rate cap or an
    injury contraindication quietly stops applying.

    The first version of this test was vacuous, and was caught by planting a
    goal that raised the loss rate cap to 99 kg a week: the test passed. It ran
    only against the two shipped profiles, neither of which trips the loss cap,
    so there was no violation for the planted goal to remove. A monotonicity
    test proves nothing unless the baseline actually contains the violations a
    goal could loosen. Hence the stress cases below, and
    `test_every_protected_severity_is_actually_represented`, which fails if the
    baseline stops covering them.
    """

    # profile overrides -> a baseline that trips a different family of bounds
    CASES = {
        "clean":  dict(),
        "unsafe": dict(_profile="example-b"),
        "starve": dict(kg=110.0, steps=25000, days=6),
    }

    def _violations(self, overrides, goals):
        import audit
        strip = lambda d: {k: v for k, v in d.items() if not k.startswith("_")}
        o = dict(overrides)
        name = o.pop("_profile", "example-a")
        p = audit.load(os.path.join(HERE, f"profiles/{name}.json"))
        plan = audit.load(os.path.join(HERE, "plans/example-a.json"))
        foods = strip(audit.load(os.path.join(HERE, "data/foods-india-egg-dairy.json")))
        lib = strip(audit.load(os.path.join(HERE, "data/exercises-home-gym.json")))
        v, _ = audit.run(dict(p, goals=goals, **o), plan, foods, lib)
        return set(v)

    GOALS = ({"want": "size", "of": "calves"},
             {"want": "size", "of": "chest"},
             {"want": "fat_loss"},
             {"want": "endurance"},
             {"want": "strength", "of": "leg press"})

    def test_adding_a_goal_never_removes_a_violation(self):
        for case, overrides in self.CASES.items():
            none = self._violations(overrides, [])
            for goal in self.GOALS:
                got = self._violations(overrides, [goal])
                self.assertTrue(none <= got,
                                f"{case} with {goal} lost: {sorted(none - got)}")
            both = self._violations(overrides, list(self.GOALS))
            self.assertTrue(none <= both, f"{case} with all goals lost violations")

    def test_every_protected_severity_is_actually_represented(self):
        """Without this the test above can pass by having nothing to lose."""
        seen = set()
        for overrides in self.CASES.values():
            seen |= {k for k, _ in self._violations(overrides, [])}
        for needed in ("safety", "floor", "energy", "distribution"):
            self.assertIn(needed, seen,
                          f"no baseline case raises '{needed}', so a goal that "
                          f"removed one would not be noticed")


class Myths(unittest.TestCase):
    def test_banned_claims_are_caught(self):
        self.assertEqual(len(myths.scan(["4 sets of calf raises",
                                         "this meal targets belly fat"])), 1)

    def test_a_clean_plan_scans_clean(self):
        self.assertEqual(myths.scan(["incline dumbbell press", "1 katori dal"]), [])

    def test_every_myth_has_a_confidence_and_an_answer(self):
        for src in (myths.DIET, myths.TRAINING):
            for claim, (conf, ans) in src.items():
                self.assertIn(conf, ("strong", "moderate", "weak"))
                self.assertTrue(ans.strip())

    def test_the_topics_actually_raised_are_covered(self):
        joined = " ".join({**myths.DIET, **myths.TRAINING}).lower()
        for topic in ("night", "cortisol", "soy", "region", "genetic", "calves"):
            self.assertIn(topic, joined, f"no standing answer covering {topic}")


class NoPersona(unittest.TestCase):
    """Nothing in the engine may be shaped around one individual."""

    # Every module that could carry a person's details. units.py, ledger.py and
    # severity.py were never covered here; resolve.py is gone.
    CODE = ("physio.py", "coherence.py", "blocks.py", "contract.py",
            "myths.py", "severity.py", "units.py", "ledger.py",
            "audit.py", "render.py", "SKILL.md", "README.md")

    # Banned everywhere, no exceptions: health details, employer, home city,
    # local brands, the individual's name. None of these belong in a general
    # engine or in its documentation.
    PRIVATE = ("rira", "onsurity", "bangalore", "provilac", "l4-l5", "l5-s1")

    # A public repository URL is not personal data, and install instructions
    # cannot be written without it. Banned in code, allowed in the README only.
    PUBLIC_HANDLE = ("rishabh",)

    def test_no_private_identifier_appears_anywhere(self):
        for f in self.CODE:
            with open(os.path.join(HERE, f)) as fh:
                text = fh.read().lower()
            for b in self.PRIVATE:
                self.assertNotIn(b, text, f"{b} found in {f}")

    def test_the_repo_handle_stays_out_of_the_code(self):
        for f in [c for c in self.CODE if c != "README.md"]:
            with open(os.path.join(HERE, f)) as fh:
                text = fh.read().lower()
            for b in self.PUBLIC_HANDLE:
                self.assertNotIn(b, text, f"{b} found in {f}; only README may "
                                          f"carry the repository URL")

    def test_no_module_hardcodes_a_bodyweight_or_measurement(self):
        for f in self.CODE:
            with open(os.path.join(HERE, f)) as fh:
                text = fh.read()
            for n in ("81.0", "96.5", "175.0"):
                self.assertNotIn(n, text, f"hardcoded {n} in {f}")

    def test_shipped_profiles_carry_no_real_name(self):
        for n in ("example-a", "example-b"):
            with open(os.path.join(HERE, "profiles", n + ".json")) as fh:
                p = json.load(fh)
            self.assertTrue(p["name"].lower().startswith("example"))

    def test_the_engine_runs_a_completely_different_person(self):
        """A 52 year old woman, 3 days, busy gym, no cold storage, hot climate."""
        with open(os.path.join(HERE, "profiles/example-b.json")) as fh:
            b = json.load(fh)
        self.assertIsNone(P.life_stage_stop(b))
        with open(os.path.join(HERE, "profiles/example-a.json")) as fh:
            a = json.load(fh)
        self.assertNotEqual(P.protein_target_g(b, True), P.protein_target_g(a, True))
        self.assertLess(P.deload_every_weeks(b), 8)
        self.assertIn("overhead barbell press",
                      [m for m, _ in P.banned_movements(b)])


class Skill(unittest.TestCase):
    """The skill file is the only entry point most people will ever use."""

    def setUp(self):
        with open(os.path.join(HERE, "SKILL.md")) as fh:
            self.s = fh.read()

    def test_it_has_frontmatter_with_a_name_and_description(self):
        self.assertTrue(self.s.startswith("---"))
        head = self.s.split("---")[1]
        self.assertIn("name:", head)
        self.assertIn("description:", head)

    def test_it_tells_claude_not_to_guess_the_intake(self):
        low = self.s.lower()
        self.assertIn("do not guess", low)

    def test_every_command_it_gives_actually_runs(self):
        import re
        for cmd in re.findall(r"python3 (\w+\.py)", self.s):
            self.assertTrue(os.path.exists(os.path.join(HERE, cmd)),
                            f"SKILL.md references {cmd}, which does not exist")

    def test_it_names_the_private_prefix_that_gitignore_protects(self):
        self.assertIn("private-", self.s)
        with open(os.path.join(HERE, ".gitignore")) as fh:
            self.assertIn("private-", fh.read())

    def test_it_carries_the_refusal_rule(self):
        for t in ("18", "pregnant", "postpartum", "65"):
            self.assertIn(t, self.s)


class EndToEnd(unittest.TestCase):
    """Rendered once here, because two of these tests used to depend on which
    order unittest happened to run them in: one wrote the document and the
    other read it, and alphabetically the reader ran first. It passed on a
    second run and failed on a clean checkout."""

    DOC = os.path.join(HERE, "example-a-plan.md")

    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, "render.py",
                        "--profile", "profiles/example-a.json",
                        "--plan", "plans/example-a.json",
                        "--out", "example-a-plan.md"],
                       cwd=HERE, capture_output=True, text=True, check=True)

    def doc(self):
        with open(self.DOC) as fh:
            return fh.read()

    def sh(self, *a):
        return subprocess.run([sys.executable, *a], cwd=HERE,
                              capture_output=True, text=True)

    def test_the_shipped_plan_passes_every_check(self):
        r = self.sh("audit.py", "--profile", "profiles/example-a.json",
                    "--plan", "plans/example-a.json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_a_minor_is_refused_with_exit_code_2(self):
        with open(os.path.join(HERE, "profiles/example-a.json")) as fh:
            p = json.load(fh)
        p["age"] = 16
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(p, f)
        try:
            r = self.sh("audit.py", "--profile", path, "--plan", "plans/example-a.json")
            self.assertEqual(r.returncode, 2)
            self.assertIn("REFUSED", r.stdout)
        finally:
            os.unlink(path)

    def test_a_gym_without_the_equipment_refuses_the_exercise(self):
        with open(os.path.join(HERE, "profiles/example-a.json")) as fh:
            p = json.load(fh)
        p["equipment"] = ["dumbbells"]
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(p, f)
        try:
            r = self.sh("audit.py", "--profile", path, "--plan", "plans/example-a.json")
            self.assertEqual(r.returncode, 1)
            self.assertIn("REFUSAL", r.stdout)
        finally:
            os.unlink(path)

    def test_the_document_carries_every_required_heading(self):
        doc = self.doc()
        for h in ("## Every week", "## Every day you train", "## Supplements",
                  "## The 24 weeks", "## Measure", "# Appendix"):
            self.assertIn(h, doc, f"missing {h}")

    def test_the_body_carries_no_banned_claim(self):
        body = self.doc().split("# Appendix")[0]
        self.assertEqual(myths.scan(body.splitlines()), [])

    def test_the_body_carries_no_reasoning(self):
        """Reasoning belongs in the appendix. The body is instructions."""
        body = self.doc().split("# Appendix")[0].lower()
        for w in ("because", "meta-analys", "evidence", "the reason"):
            self.assertNotIn(w, body, f"'{w}' is justification; move it below")


if __name__ == "__main__":
    unittest.main(verbosity=2)
