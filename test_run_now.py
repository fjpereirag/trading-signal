import unittest
from unittest.mock import patch

from run_now import dispatch


class RunNowTests(unittest.TestCase):
    @patch("run_now.requests.post")
    def test_dispatches_main_with_report(self, post):
        post.return_value.status_code = 204
        dispatch("test-token")
        args, kwargs = post.call_args
        self.assertIn("/actions/workflows/main.yml/dispatches", args[0])
        self.assertEqual(kwargs["json"]["inputs"]["report_telegram"], "true")

    @patch("run_now.requests.post")
    def test_blank_token_never_calls_github(self, post):
        with self.assertRaises(ValueError):
            dispatch("")
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
