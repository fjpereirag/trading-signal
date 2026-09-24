import unittest
from unittest.mock import patch

import quantfury_account as qa
from quantfury_account import review_xrp, snapshot


class AccountAlertTests(unittest.TestCase):
    def test_exposure_includes_positions_and_active_orders(self):
        result = review_xrp(
            {"tradingPower": 6000, "availableTradingPower": 2080.48},
            [{"shortNameDisplay": "XRP/USDT", "quantity": 10}],
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

    @patch.dict("os.environ", {
        "QUANTFURY_CLIENT_ID": "client", "QUANTFURY_REFRESH_TOKEN": "refresh",
        "QUANTFURY_ACCESS_TOKEN": "", "GH_SECRETS_PAT": "",
    })
    @patch("quantfury_account.requests.post")
    def test_refresh_without_rotation(self, post):
        qa._cached_token = None
        post.return_value.json.return_value = {"access_token": "new-access"}
        self.assertEqual(qa._token(), "new-access")
        self.assertEqual(post.call_count, 1)
        qa._cached_token = None

    @patch.dict("os.environ", {
        "QUANTFURY_CLIENT_ID": "client", "QUANTFURY_REFRESH_TOKEN": "old",
        "GH_SECRETS_PAT": "", "GITHUB_REPOSITORY": "fjpereirag/trading-signal",
    })
    @patch("quantfury_account.requests.post")
    def test_rotation_without_storage_fails_closed(self, post):
        qa._cached_token = None
        post.return_value.json.return_value = {
            "access_token": "new-access", "refresh_token": "rotated",
        }
        with self.assertRaisesRegex(RuntimeError, "GH_SECRETS_PAT"):
            qa._token()
        qa._cached_token = None


if __name__ == "__main__":
    unittest.main()
