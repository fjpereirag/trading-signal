import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pandas as pd

import alert_bot


class SynchronizedAlertTests(unittest.TestCase):
    @patch.dict("os.environ", {"QUANTFURY_ACCESS_TOKEN": "", "QUANTFURY_CLIENT_ID": "", "QUANTFURY_REFRESH_TOKEN": ""})
    @patch("alert_bot.send_telegram")
    def test_no_quantfury_auth_blocks_telegram(self, send):
        with self.assertRaisesRegex(RuntimeError, "sin autorización"):
            alert_bot.main()
        send.assert_not_called()

    @patch.dict("os.environ", {"QUANTFURY_ACCESS_TOKEN": "test"})
    @patch("alert_bot.snapshot", side_effect=RuntimeError("MCP failed"))
    @patch("alert_bot.send_telegram")
    def test_account_failure_blocks_telegram(self, send, snapshot):
        with self.assertRaisesRegex(RuntimeError, "MCP failed"):
            alert_bot.main()
        send.assert_not_called()

    @patch.dict("os.environ", {"QUANTFURY_ACCESS_TOKEN": "test"})
    @patch("alert_bot.snapshot", return_value=(
        {"balance": 100, "currency": "USDT", "tradingPower": 1000, "availableTradingPower": 900}, []
    ))
    @patch("alert_bot.get_timeframes")
    @patch("alert_bot.send_telegram")
    def test_stale_price_blocks_telegram(self, send, market, snapshot):
        market.return_value = {"M1": pd.DataFrame(
            {"Close": [1.0]}, index=[datetime.now(timezone.utc) - timedelta(minutes=6)]
        )}
        with self.assertRaisesRegex(RuntimeError, "desactualizado"):
            alert_bot.main()
        send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
