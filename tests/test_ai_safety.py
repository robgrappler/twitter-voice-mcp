import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ai_handler import AIHandler

import tempfile

class TestAISafety(unittest.TestCase):
    def setUp(self):
        self.handler = AIHandler()
        # Create a temp file for the profile
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w")
        self.temp_file.write("Mock Voice Profile")
        self.temp_file.close()
        self.handler.voice_profile_path = self.temp_file.name

    def tearDown(self):
        if os.path.exists(self.handler.voice_profile_path):
            os.remove(self.handler.voice_profile_path)

    @patch("google.generativeai.GenerativeModel")
    def test_gemini_system_instruction(self, mock_model_cls):
        """Test that system_instruction is passed to Gemini model init."""
        self.handler.provider = "gemini"
        self.handler.model = "gemini-1.5-flash"

        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value.text = "Mock Response"
        mock_model_cls.return_value = mock_model_instance

        system_instr = "You are a safe AI."
        result = self.handler._call_model("Hello", system_instruction=system_instr)

        if result.startswith("Error"):
             self.fail(f"_call_model failed with: {result}")

        # Verify GenerativeModel was initialized with system_instruction
        mock_model_cls.assert_called_with("gemini-1.5-flash", system_instruction=system_instr)

    @patch("ai_handler.OpenAI")
    def test_openai_system_instruction(self, mock_openai_cls):
        """Test that system_instruction is passed as a system message to OpenAI."""
        self.handler.provider = "openai"
        self.handler.model = "gpt-4o-mini"
        self.handler.client = mock_openai_cls.return_value

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Mock Response"
        self.handler.client.chat.completions.create.return_value = mock_response

        system_instr = "You are a safe AI."
        result = self.handler._call_model("Hello", system_instruction=system_instr)

        if result.startswith("Error"):
             self.fail(f"_call_model failed with: {result}")

        # Verify call args
        call_args = self.handler.client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], system_instr)
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "Hello")

    @patch("ai_handler.Anthropic")
    def test_anthropic_system_instruction(self, mock_anthropic_cls):
        """Test that system_instruction is passed as 'system' param to Anthropic."""
        self.handler.provider = "anthropic"
        self.handler.model = "claude-3-haiku"
        self.handler.client = mock_anthropic_cls.return_value

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Mock Response")]
        self.handler.client.messages.create.return_value = mock_response

        system_instr = "You are a safe AI."
        result = self.handler._call_model("Hello", system_instruction=system_instr)

        if result.startswith("Error"):
             self.fail(f"_call_model failed with: {result}")

        # Verify call args
        call_args = self.handler.client.messages.create.call_args
        self.assertEqual(call_args.kwargs["system"], system_instr)
        self.assertEqual(call_args.kwargs["messages"][0]["role"], "user")
        self.assertEqual(call_args.kwargs["messages"][0]["content"], "Hello")

    @patch("google.generativeai.GenerativeModel")
    def test_generate_tweet_structure(self, mock_model_cls):
        """Test that generate_tweet creates correct XML wrapping."""
        self.handler.provider = "gemini"

        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value.text = "Tweet 1\nTweet 2"
        mock_model_cls.return_value = mock_model_instance

        self.handler.generate_tweet("Dangerous Topic", count=2)

        # Check that the prompt passed to generate_content contains XML tags
        if not mock_model_instance.generate_content.called:
             self.fail("generate_content was not called")

        call_args = mock_model_instance.generate_content.call_args
        prompt_passed = call_args.args[0]

        self.assertIn("<topic>", prompt_passed)
        self.assertIn("Dangerous Topic", prompt_passed)
        self.assertIn("</topic>", prompt_passed)

        # Check that initialization had system instruction containing voice profile
        init_args = mock_model_cls.call_args
        sys_instr = init_args.kwargs["system_instruction"]
        self.assertIn("Mock Voice Profile", sys_instr)

if __name__ == "__main__":
    unittest.main()
