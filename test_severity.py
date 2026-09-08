"""
The severity ordering is the design, so it gets a test of its own.

Kept from test_loop.Precedence when the unused resolve.py loop was deleted. The
ordering survived that deletion because it was the only part of the file the
engine ever used.

    python3 -m unittest test_severity -v
"""
import re, os, unittest
import severity

HERE = os.path.dirname(os.path.abspath(__file__))


class Ordering(unittest.TestCase):

    def test_the_order_is_the_one_the_design_intends(self):
        R = severity.RANK
        self.assertLess(R["refusal"], R["safety"])
        self.assertLess(R["safety"], R["floor"])
        self.assertLess(R["floor"], R["coherence"])
        self.assertLess(R["coherence"], R["palatability"])

    def test_safety_outranks_everything_except_a_refusal(self):
        """Derived from PRECEDENCE, not a hardcoded list. The first version
        named the levels and broke when one was removed."""
        R = severity.RANK
        for level in severity.PRECEDENCE:
            if level in ("refusal", "safety"):
                continue
            self.assertLess(R["safety"], R[level],
                            f"{level} must never outrank food safety")

    def test_rank_covers_precedence_exactly(self):
        self.assertEqual(set(severity.RANK), set(severity.PRECEDENCE))
        self.assertEqual(len(severity.RANK), len(severity.PRECEDENCE))


class Vocabulary(unittest.TestCase):
    """Nothing may raise a severity the ordering does not know about.

    This is the check that was missing when a volume ceiling breach was raised
    as 'variety' and nobody noticed for weeks.
    """

    # physio.py is deliberately absent. It returns evidence tiers
    # ("strong", "moderate", "weak") in the same tuple shape, and those are not
    # severities. Scanning it produced a false positive on the first run.
    ENGINE = ("audit.py", "coherence.py", "blocks.py")

    def raised(self):
        out = set()
        for f in self.ENGINE:
            with open(os.path.join(HERE, f)) as fh:
                src = fh.read()
            out |= set(re.findall(r'(?:v|out)\.append\(\(\s*"(\w+)"', src))
        return out

    def test_every_raised_severity_is_in_precedence(self):
        unknown = self.raised() - set(severity.PRECEDENCE)
        self.assertEqual(unknown, set(),
                         f"raised but not ranked: {sorted(unknown)}")

    def test_no_ranked_severity_is_unreachable(self):
        unused = set(severity.PRECEDENCE) - self.raised()
        self.assertEqual(unused, set(),
                         f"ranked but nothing raises it: {sorted(unused)}. "
                         f"Remove it or wire the check that should raise it.")
