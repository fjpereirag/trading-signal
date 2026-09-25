import unittest

from opportunity_bot import evaluate


class OpportunityTests(unittest.TestCase):
    def test_requires_retest_rebound_and_free_account(self):
        args = ("AVGO", 359.0, "Acción Nasdaq", 2, [359.5, 359.8, 359.2, 359.6],
                "2026-09-25T14:00:00+00:00", 6000)
        plan = evaluate(*args, [])
        self.assertTrue(plan["ready"])
        self.assertEqual(plan["quantity"], 16)
        self.assertLessEqual(plan["exposure"], 6000)
        self.assertEqual(plan["target_move"], 3.13)
        self.assertFalse(evaluate(*args, [{"instrument": "XRP"}])["ready"])
        self.assertFalse(evaluate("AVGO", 359, "Acción Nasdaq", 2,
                                  [358.9, 359.8, 359.2, 359.6], args[5], 6000, [])["ready"])


if __name__ == "__main__":
    unittest.main()
