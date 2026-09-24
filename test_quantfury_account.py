import unittest
from unittest.mock import patch

from quantfury_account import review_xrp, snapshot


class AccountAlertTests(unittest.TestCase):
    def test_exposure_includes_positions_and_active_orders(self):
        result = review_xrp(
            {"tradingPower": 6000, "availableTradingPower": 2080.48},
            [{"shortNameDisplay": "XRP", "quantity": 10}],
        )
        self.assertAlmostEqual(result["exposure_pct"], 65.3253333333)
        self.assertTrue(result["block_buys"])
        self.assertEqual(len(result["xrp"]), 1)

    @patch("quantfury_account._call")
    def test_incomplete_response_fails_closed(self, call):
        call.side_effect = [
            {"balance": 100, "currency": "USD", "tradingPower": 1000,
             "availableTradingPower": 500},
            {},
        ]
        with self.assertRaisesRegex(RuntimeError, "incompleta"):
            snapshot()


if __name__ == "__main__":
    unittest.main()
