import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pandas as pd

import alert_bot


class SynchronizedAlertTests(unittest.TestCase):
    def test_real_quantfury_stop_shape_is_read(self):
        result = {"signal": "WAIT", "zone": "MEDIA", "pullback": "NO"}
        review = {"xrp": [{"direction": "Long", "lastPrice": 1.53, "quantity": 10,
                          "stopOrders": [{"price": 1.485}],
                          "targetOrders": [{"price": 1.565}]}], "block_buys": True}
        text = alert_bot.format_advice(result, review, {})
        self.assertEqual(len(text.splitlines()), 3)
        self.assertIn("SL: Mantener", text)
        self.assertIn("Parcial: No actuar", text)

    def test_stop_touch_requests_broker_check(self):
        result = {"signal": "WAIT", "zone": "MEDIA", "pullback": "NO"}
        review = {"xrp": [{"direction": "Long", "lastPrice": 1.48, "quantity": 10,
                          "stopOrders": [{"price": 1.485}],
                          "targetOrders": []}], "block_buys": True}
        self.assertEqual(alert_bot.format_advice(result, review, {}),
                         "1. Acción: Vender\n2. SL: Ejecutar\n3. Parcial: Venta total por SL")

    def test_breakout_requires_fifty_dollars_and_caps_partial(self):
        result = {"breakout": True, "signal": "WAIT"}
        position = {"direction": "Long", "lastPrice": 1.56, "quantity": 200,
                    "unrealizedPnlSystem": 50, "stopOrders": [{"price": 1.47}]}
        review = {"xrp": [position], "block_buys": True}
        self.assertEqual(alert_bot.format_advice(result, review, {}), (
            "1. Acción: Vender\n2. SL: Subir\n"
            "3. Parcial: Venta parcial de 50.0000 XRP en 1.5600 USD"
        ))
        position["unrealizedPnlSystem"] = 49.99
        self.assertEqual(alert_bot.format_advice(result, review, {}),
                         "1. Acción: Esperar\n2. SL: Mantener\n3. Parcial: No actuar")

    def test_buy_requires_safe_exposure_and_value_zone(self):
        result = {"signal": "BUY", "context": "ALCISTA", "zone": "PROFUNDA",
                  "pullback": "PROFUNDO", "breakout": False}
        position = {"direction": "Long", "lastPrice": 1.53, "quantity": 100,
                    "stopOrders": [{"price": 1.47}]}
        review = {"xrp": [position], "block_buys": False}
        self.assertIn("Acción: Comprar", alert_bot.format_advice(result, review, {}))
        self.assertIn("Parcial: Compra parcial", alert_bot.format_advice(result, review, {}))
        review["block_buys"] = True
        self.assertIn("Acción: Esperar", alert_bot.format_advice(result, review, {}))

    def test_missing_stop_blocks_message(self):
        review = {"xrp": [{"direction": "Long", "lastPrice": 1.53, "quantity": 10,
                           "stopOrders": []}], "block_buys": True}
        with self.assertRaisesRegex(RuntimeError, "sin SL"):
            alert_bot.format_advice({"signal": "WAIT"}, review, {})

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
