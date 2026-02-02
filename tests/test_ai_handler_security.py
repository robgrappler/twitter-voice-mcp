import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json
import tempfile

# Add src to path
sys.path.append(os.path.abspath("src"))

# Mock modules before importing ai_handler
sys.modules["google.generativeai"] = MagicMock()
sys.modules["openai"] = MagicMock()
sys.modules["anthropic"] = MagicMock()
# sys.modules["PIL"] = MagicMock() # PIL might be needed for real import, but we mock it if import fails usually.
# Actually ai_handler tries to import PIL. If we mock it, we control it.

from ai_handler import AIHandler
import google.generativeai as genai
# from openai import OpenAI
# from anthropic import Anthropic

class TestAIHandlerSecurity(unittest.TestCase):
    def setUp(self):
        # We need to ensure environment variables don't mess up init
        with patch.dict(os.environ, {}, clear=True):
             self.ai_handler = AIHandler()

        # Mock voice profile
        self.ai_handler.get_voice_profile = MagicMock(return_value="Test Voice Profile")

        # Prevent file writes
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.ai_handler.voice_profile_path = self.temp_file.name

    def tearDown(self):
        if os.path.exists(self.ai_handler.voice_profile_path):
            os.remove(self.ai_handler.voice_profile_path)

    def test_gemini_system_instruction(self):
        self.ai_handler.configure("gemini", "key")

        # Reset mock
        genai.GenerativeModel.reset_mock()
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = "Tweet 1"
        genai.GenerativeModel.return_value = mock_model

        self.ai_handler.generate_tweet("Test Topic", 1)

        # Verify GenerativeModel called with system_instruction
        call_args = genai.GenerativeModel.call_args
        self.assertIsNotNone(call_args)
        _, kwargs = call_args
        self.assertIn("system_instruction", kwargs)
        self.assertIn("Test Voice Profile", kwargs["system_instruction"])

        # Verify generate_content called with user prompt only (roughly)
        mock_model.generate_content.assert_called_once()
        args, _ = mock_model.generate_content.call_args
        prompt_arg = args[0]
        self.assertIn("Test Topic", prompt_arg)
        # Ensure voice profile is NOT in the user prompt (it should be in system instruction)
        self.assertNotIn("Test Voice Profile", prompt_arg)

    def test_openai_system_instruction(self):
        self.ai_handler.configure("openai", "key")

        # Mock client
        mock_client = MagicMock()
        # Mock the nested response structure: response.choices[0].message.content
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Tweet 1"
        mock_client.chat.completions.create.return_value = mock_response

        self.ai_handler.client = mock_client

        self.ai_handler.generate_tweet("Test Topic", 1)

        mock_client.chat.completions.create.assert_called_once()
        _, kwargs = mock_client.chat.completions.create.call_args
        messages = kwargs["messages"]

        # Should have 2 messages: System and User
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Test Voice Profile", messages[0]["content"])
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("Test Topic", messages[1]["content"])

    def test_anthropic_system_instruction(self):
        self.ai_handler.configure("anthropic", "key")

        # Mock client
        mock_client = MagicMock()
        # Mock response.content[0].text
        mock_content = MagicMock()
        mock_content.text = "Tweet 1"
        mock_client.messages.create.return_value.content = [mock_content]

        self.ai_handler.client = mock_client

        self.ai_handler.generate_tweet("Test Topic", 1)

        mock_client.messages.create.assert_called_once()
        _, kwargs = mock_client.messages.create.call_args

        self.assertIn("system", kwargs)
        self.assertIn("Test Voice Profile", kwargs["system"])

        messages = kwargs["messages"]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")
        self.assertIn("Test Topic", messages[0]["content"])

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=MagicMock)
    def test_analyze_style_separation(self, mock_open, mock_makedirs):
        self.ai_handler.configure("gemini", "key")
        genai.GenerativeModel.reset_mock()
        mock_model = MagicMock()
        mock_model.generate_content.return_value.text = "Analyzed Profile"
        genai.GenerativeModel.return_value = mock_model

        tweets = ["Tweet A", "Tweet B"]
        self.ai_handler.analyze_style(tweets)

        call_args = genai.GenerativeModel.call_args
        _, kwargs = call_args
        self.assertIn("system_instruction", kwargs)
        self.assertIn("Analyze the provided tweets", kwargs["system_instruction"])

        args, _ = mock_model.generate_content.call_args
        prompt_arg = args[0]
        self.assertIn("Tweet A", prompt_arg)

if __name__ == "__main__":
    unittest.main()
