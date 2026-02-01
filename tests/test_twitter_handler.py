import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from twitter_handler import TwitterHandler

class TestTwitterHandler(unittest.TestCase):
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

    def test_retweet_caches_user_id(self):
        # Mock responses
        mock_me_response = MagicMock()
        mock_me_response.status_code = 200
        mock_me_response.json.return_value = {"data": {"id": "12345"}}

        mock_retweet_response = MagicMock()
        mock_retweet_response.status_code = 200
        mock_retweet_response.json.return_value = {"data": {"retweeted": True}}

        def get_side_effect(url, **kwargs):
            if "users/me" in url:
                return mock_me_response
            return MagicMock(status_code=404)

        self.handler.session.get.side_effect = get_side_effect
        self.handler.session.post.return_value = mock_retweet_response

        # First call
        self.handler.retweet("tweet1")
        self.assertEqual(self.handler.user_id, "12345")

        # Second call
        self.handler.retweet("tweet2")
        self.assertEqual(self.handler.user_id, "12345")

        # Verify get was called only once for users/me
        me_calls = [call for call in self.handler.session.get.call_args_list if "users/me" in call[0][0]]
        self.assertEqual(len(me_calls), 1)

    def test_retweet_error_handling(self):
        # Mock failure response for user ID
        mock_me_response = MagicMock()
        mock_me_response.status_code = 500
        mock_me_response.text = "Internal Server Error"

        self.handler.session.get.return_value = mock_me_response

        result = self.handler.retweet("tweet1")

        self.assertEqual(result, {"error": "Failed to get my user ID"})
        self.assertIsNone(self.handler.user_id)

        # Verify it tries again next time if successful
        mock_me_response.status_code = 200
        mock_me_response.json.return_value = {"data": {"id": "67890"}}

        # We need to mock the post response as well for the success case
        mock_retweet_response = MagicMock()
        mock_retweet_response.status_code = 200
        mock_retweet_response.json.return_value = {"data": {"retweeted": True}}
        self.handler.session.post.return_value = mock_retweet_response

        self.handler.retweet("tweet2")
        self.assertEqual(self.handler.user_id, "67890")

    def test_get_user_tweets_caches_id(self):
        # Mock responses
        mock_user_id_response = MagicMock()
        mock_user_id_response.status_code = 200
        mock_user_id_response.json.return_value = {"data": {"id": "999"}}

        mock_tweets_response = MagicMock()
        mock_tweets_response.status_code = 200
        mock_tweets_response.json.return_value = {"data": [{"text": "tweet1"}]}

        def get_side_effect(url, **kwargs):
            if "users/by/username/testuser" in url:
                return mock_user_id_response
            if "users/999/tweets" in url:
                return mock_tweets_response
            return MagicMock(status_code=404)

        self.handler.session.get.side_effect = get_side_effect

        # First call
        tweets1 = self.handler.get_user_tweets("testuser")
        self.assertEqual(len(tweets1), 1)
        self.assertEqual(self.handler.user_cache["testuser"], "999")

        # Second call
        tweets2 = self.handler.get_user_tweets("testuser")
        self.assertEqual(len(tweets2), 1)

        # Verify get was called only once for user ID
        # Count calls that contain 'users/by/username/testuser'
        id_calls = [
            call for call in self.handler.session.get.call_args_list
            if call[0] and "users/by/username/testuser" in call[0][0]
        ]
        self.assertEqual(len(id_calls), 1)

    def test_verify_credentials_sets_user_id(self):
        # Mock response
        mock_me_response = MagicMock()
        mock_me_response.status_code = 200
        mock_me_response.json.return_value = {"data": {"id": "my_id_123"}}

        self.handler.session.get.return_value = mock_me_response

        # Call verify_credentials
        result = self.handler.verify_credentials()

        self.assertTrue(result)
        self.assertEqual(self.handler.user_id, "my_id_123")

if __name__ == "__main__":
    unittest.main()
