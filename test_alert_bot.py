import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pandas as pd

import alert_bot


class SynchronizedAlertTests(unittest.TestCase):
    def test_real_quantfury_stop_shape_is_read(self):
        review = {"xrp": [{"direction": "Long", "lastPrice": 1.53, "quantity": 10,
                          "stopOrders": [{"price": 1.485}]}], "block_buys": True}
        text = alert_bot.format_advice({"signal": "WAIT"}, review, {})
        self.assertEqual(len(text.splitlines()), 3)
        self.assertIn("SL: Mantener", text)

    def test_stop_touch_requests_broker_check(self):
        review = {"xrp": [{"direction": "Long", "lastPrice": 1.48, "quantity": 10,
                          "stopOrders": [{"price": 1.485}]}], "block_buys": True}
        self.assertEqual(alert_bot.format_advice({"signal": "WAIT"}, review, {}),
                         "1. Acción: Vender\n2. SL: Ejecutar\n3. Parcial: Venta total por SL")

    def test_breakout_requires_fifty_dollars(self):
        position = {"direction": "Long", "lastPrice": 1.56, "quantity": 200,
                    "unrealizedPnlSystem": 50, "stopOrders": [{"price": 1.47}]}
        review = {"xrp": [position], "block_buys": True}
        self.assertIn("Venta parcial de 50.0000 XRP", alert_bot.format_advice({"breakout": True}, review, {}))
        position["unrealizedPnlSystem"] = 49.99
        self.assertIn("Acción: Esperar", alert_bot.format_advice({"breakout": True}, review, {}))

    def test_missing_stop_blocks_result(self):
        review = {"xrp": [{"direction": "Long", "lastPrice": 1.53, "quantity": 10,
                           "stopOrders": []}], "block_buys": True}
        with self.assertRaisesRegex(RuntimeError, "sin SL"):
            alert_bot.format_advice({"signal": "WAIT"}, review, {})

    @patch.dict("os.environ", {"QUANTFURY_ACCESS_TOKEN": "", "QUANTFURY_CLIENT_ID": "", "QUANTFURY_REFRESH_TOKEN": ""})
    @patch("alert_bot.snapshot")
    def test_no_quantfury_auth_blocks_result(self, snapshot):
        with self.assertRaisesRegex(RuntimeError, "sin autorización"):
            alert_bot.main()
        snapshot.assert_not_called()

    @patch.dict("os.environ", {"QUANTFURY_ACCESS_TOKEN": "test", "APP_RESULT_PASSWORD": "Una clave bastante larga para el resultado", "REQUEST_ID": "a" * 32})
    @patch("alert_bot.snapshot", side_effect=RuntimeError("MCP failed"))
    def test_account_failure_blocks_result(self, snapshot):
        with self.assertRaisesRegex(RuntimeError, "MCP failed"):
            alert_bot.main()

    @patch.dict("os.environ", {"QUANTFURY_ACCESS_TOKEN": "test", "APP_RESULT_PASSWORD": "Una clave bastante larga para el resultado", "REQUEST_ID": "a" * 32})
    @patch("alert_bot.snapshot", return_value=({"balance": 100, "currency": "USDT", "tradingPower": 1000, "availableTradingPower": 900}, []))
    @patch("alert_bot.get_timeframes")
    def test_stale_price_blocks_result(self, market, snapshot):
        market.return_value = {"M1": pd.DataFrame({"Close": [1.0]}, index=[datetime.now(timezone.utc) - timedelta(minutes=6)])}
        with self.assertRaisesRegex(RuntimeError, "desactualizado"):
            alert_bot.main()


if __name__ == "__main__":
    unittest.main()
