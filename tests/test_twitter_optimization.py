import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from twitter_handler import TwitterHandler

class TestTwitterHandlerOptimization(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {
            "TWITTER_CONSUMER_KEY": "fake_key",
            "TWITTER_CONSUMER_SECRET": "fake_secret",
            "TWITTER_ACCESS_TOKEN": "fake_token",
            "TWITTER_ACCESS_TOKEN_SECRET": "fake_token_secret"
        })
        self.env_patcher.start()
        self.handler = TwitterHandler()
        self.handler.session = MagicMock()

    def tearDown(self):
        self.env_patcher.stop()

    def test_verify_credentials_caches_user_id(self):
        # Mock responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"id": "12345"}}

        self.handler.session.get.return_value = mock_response

        # Call verify_credentials
        result = self.handler.verify_credentials()
        self.assertTrue(result)

        # Verify user_id is cached
        self.assertEqual(self.handler.user_id, "12345", "user_id should be cached after verify_credentials")

    def test_get_user_tweets_caches_username(self):
        # Mock response for user ID lookup
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {"data": {"id": "67890"}}

        # Mock response for tweets
        mock_tweets_response = MagicMock()
        mock_tweets_response.status_code = 200
        mock_tweets_response.json.return_value = {"data": [{"text": "tweet1"}]}

        def get_side_effect(url, **kwargs):
            if "users/by/username" in url:
                return mock_user_response
            if "users/67890/tweets" in url:
                return mock_tweets_response
            return MagicMock(status_code=404)

        self.handler.session.get.side_effect = get_side_effect

        # First call
        tweets1 = self.handler.get_user_tweets("testuser")
        self.assertEqual(tweets1, ["tweet1"])

        # Second call
        tweets2 = self.handler.get_user_tweets("testuser")
        self.assertEqual(tweets2, ["tweet1"])

        # Verify API called only once for user ID
        user_calls = [call for call in self.handler.session.get.call_args_list if "users/by/username" in call[0][0]]
        self.assertEqual(len(user_calls), 1, "Should only look up username once")

if __name__ == "__main__":
    unittest.main()
