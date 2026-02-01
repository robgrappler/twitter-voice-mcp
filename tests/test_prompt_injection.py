
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ai_handler import AIHandler

class TestPromptInjection(unittest.TestCase):
    def setUp(self):
        self.handler = AIHandler()
        # Mock dependencies
        self.handler.api_key = "dummy"

        # Create dummy voice profile
        os.makedirs(os.path.dirname(self.handler.voice_profile_path), exist_ok=True)
        with open(self.handler.voice_profile_path, "w") as f:
            f.write("You are a cynical robot.")

    @patch("google.generativeai.GenerativeModel")
    def test_gemini_separation(self, mock_model_class):
        self.handler.configure("gemini", "dummy", "gemini-1.5")
        mock_instance = mock_model_class.return_value
        mock_instance.generate_content.return_value.text = "tweet"

        self.handler.generate_tweet("input", count=1)

        # Check system instruction
        _, kwargs = mock_model_class.call_args
        self.assertIn("system_instruction", kwargs)
        self.assertIn("You are a cynical robot", kwargs["system_instruction"])

        # Check user prompt
        gen_args, _ = mock_instance.generate_content.call_args
        user_prompt = gen_args[0]
        self.assertIn("Task: Write 1 distinct tweets", user_prompt)
        self.assertNotIn("You are a cynical robot", user_prompt)

    @patch("ai_handler.OpenAI")
    def test_openai_separation(self, mock_openai_class):
        self.handler.configure("openai", "dummy", "gpt-4")
        mock_client = mock_openai_class.return_value
        mock_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="tweet"))
        ]

        self.handler.generate_tweet("input", count=1)

        _, kwargs = mock_client.chat.completions.create.call_args
        messages = kwargs["messages"]

        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("You are a cynical robot", messages[0]["content"])

        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("Task:", messages[1]["content"])

    @patch("ai_handler.Anthropic")
    def test_anthropic_separation(self, mock_anthropic_class):
        self.handler.configure("anthropic", "dummy", "claude")
        mock_client = mock_anthropic_class.return_value
        mock_client.messages.create.return_value.content = [
            MagicMock(text="tweet")
        ]

        self.handler.generate_tweet("input", count=1)

        _, kwargs = mock_client.messages.create.call_args

        self.assertIn("system", kwargs)
        self.assertIn("You are a cynical robot", kwargs["system"])

        self.assertEqual(kwargs["messages"][0]["role"], "user")
        self.assertIn("Task:", kwargs["messages"][0]["content"])

if __name__ == "__main__":
    unittest.main()
