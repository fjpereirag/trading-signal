import unittest
from unittest.mock import patch
from datetime import datetime, timezone

from opportunity_bot import evaluate, candles


class OpportunityTests(unittest.TestCase):
    @patch("opportunity_bot.requests.get")
    def test_rejects_stale_crypto_candles(self, get):
        now = datetime(2026, 9, 25, 14, 0, tzinfo=timezone.utc)
        get.return_value.json.return_value = [[0, "1", "1", "1", "1", "1", 1]] * 5
        with self.assertRaisesRegex(RuntimeError, "desactualizadas"):
            candles("ETHUSDT", now)

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
