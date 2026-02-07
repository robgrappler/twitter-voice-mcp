import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

class TestAISafety(unittest.TestCase):
    def setUp(self):
        # Save original sys.modules state
        self._original_modules = sys.modules.copy()
        self._original_env = os.environ.copy()

        # Clean up modules
        if 'ai_handler' in sys.modules:
            del sys.modules['ai_handler']
        if 'google.generativeai' in sys.modules:
            del sys.modules['google.generativeai']

    def tearDown(self):
        # Restore sys.modules
        modules_to_remove = set(sys.modules.keys()) - set(self._original_modules.keys())
        for mod in modules_to_remove:
            del sys.modules[mod]
        # Restore env
        os.environ.clear()
        os.environ.update(self._original_env)

    def test_generate_tweet_prompt_safety(self):
        """Verify that user topic is wrapped in XML tags."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            mock_genai = MagicMock()
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_model.generate_content.return_value.text = "Tweet 1"

            with patch.dict(sys.modules, {'google.generativeai': mock_genai}):
                from ai_handler import AIHandler

                # Mock get_voice_profile to avoid file read
                with patch.object(AIHandler, 'get_voice_profile', return_value="Funny style"):
                    handler = AIHandler()
                    topic = "security best practices"
                    handler.generate_tweet(topic)

                    # Check arguments passed to generate_content
                    args, _ = mock_model.generate_content.call_args
                    prompt = args[0]

                    # Assert tags are present
                    self.assertIn("<topic>", prompt)
                    self.assertIn("</topic>", prompt)
                    self.assertIn(topic, prompt)

    def test_retweet_comment_prompt_safety(self):
        """Verify that original tweet text is wrapped in XML tags."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            mock_genai = MagicMock()
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_model.generate_content.return_value.text = "Nice tweet!"

            with patch.dict(sys.modules, {'google.generativeai': mock_genai}):
                from ai_handler import AIHandler

                with patch.object(AIHandler, 'get_voice_profile', return_value="Funny style"):
                    handler = AIHandler()
                    original_tweet = "This is a suspicious tweet"
                    handler.generate_retweet_comment(original_tweet)

                    args, _ = mock_model.generate_content.call_args
                    prompt = args[0]

                    self.assertIn("<original_tweet>", prompt)
                    self.assertIn("</original_tweet>", prompt)
                    self.assertIn(original_tweet, prompt)

if __name__ == "__main__":
    unittest.main()
