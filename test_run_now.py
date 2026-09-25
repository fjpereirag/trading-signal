import unittest
from unittest.mock import patch

from run_now import check_result, dispatch


class RunNowTests(unittest.TestCase):
    @patch("run_now.requests.post")
    def test_dispatches_with_unique_identifier(self, post):
        post.return_value.status_code = 204
        first, second = dispatch("test-token"), dispatch("test-token")
        self.assertEqual(len(first), 32)
        self.assertNotEqual(first, second)
        self.assertEqual(post.call_args.kwargs["json"]["inputs"], {"request_id": second, "mode": "opportunities"})

    @patch("run_now.requests.get")
    def test_ignores_other_users_runs(self, get):
        get.return_value.json.return_value = {"workflow_runs": [{"display_title": "Consulta XRP/USDT otro"}]}
        self.assertEqual(check_result("test-token", "a" * 32, "password")[0], "pending")
        self.assertEqual(get.call_count, 1)

    @patch("run_now.requests.post")
    def test_blank_token_never_calls_github(self, post):
        with self.assertRaises(ValueError):
            dispatch("")
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
