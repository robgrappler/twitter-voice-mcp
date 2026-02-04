import sys
import os
import unittest
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from ai_handler import AIHandler

class TestAISafety(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

        self.env_patcher = patch.dict(os.environ, {
            "GEMINI_API_KEY": "fake_key"
        })
        self.env_patcher.start()

        # Mock dependencies
        self.genai_patcher = patch('ai_handler.genai')
        self.mock_genai = self.genai_patcher.start()

        self.openai_patcher = patch('ai_handler.OpenAI')
        self.mock_openai = self.openai_patcher.start()

        self.anthropic_patcher = patch('ai_handler.Anthropic')
        self.mock_anthropic = self.anthropic_patcher.start()

        # Patch the voice profile path to use temp dir
        self.voice_profile_path = os.path.join(self.test_dir, "voice_profile.txt")

        # Create a mock voice profile
        with open(self.voice_profile_path, "w") as f:
            f.write("A cool sarcastic voice.")

    def tearDown(self):
        self.env_patcher.stop()
        self.genai_patcher.stop()
        self.openai_patcher.stop()
        self.anthropic_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_generate_tweet_safety(self):
        """Test that generate_tweet properly separates system instruction and user message."""
        # Use a fresh handler with mocked methods where needed, but real logic
        with patch('ai_handler.os.getenv', return_value="fake_key"):
            handler = AIHandler()
            handler.voice_profile_path = self.voice_profile_path

            with patch.object(handler, '_call_model') as mock_call_model:
                mock_call_model.return_value = "Tweet"
                topic = "Testing"

                handler.generate_tweet(topic)

                # Check arguments
                args, kwargs = mock_call_model.call_args

                # We expect signature: _call_model(user_message, images=..., system_instruction=...)
                user_message = args[0]
                system_instruction = kwargs.get('system_instruction')

                # Verify System Instruction
                self.assertIsNotNone(system_instruction, "System instruction should be separated")
                self.assertIn("You are a ghostwriter", system_instruction)
                self.assertIn("A cool sarcastic voice", system_instruction)

                # Verify User Message
                # Check that topic is present and seemingly wrapped.
                # Since we use multiline f-strings with indentation, simpler check:
                self.assertIn(topic, user_message)
                self.assertIn("<topic>", user_message)
                self.assertIn("</topic>", user_message)

                self.assertNotIn("You are a ghostwriter", user_message)

    def test_call_model_gemini_passing(self):
        """Verify _call_model passes system_instruction to Gemini correctly."""
        with patch('ai_handler.os.getenv', return_value="fake_key"):
            handler = AIHandler()
            handler.configure("gemini", "key", "model")

            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.return_value.text = "Response"
            self.mock_genai.GenerativeModel.return_value = mock_model_instance

            system_inst = "System prompt"
            user_msg = "User prompt"

            # This method needs to be the real one, so we don't patch it here.
            handler._call_model(user_msg, system_instruction=system_inst)

            # Assert GenerativeModel called with system_instruction
            self.mock_genai.GenerativeModel.assert_called_with("model", system_instruction=system_inst)
            mock_model_instance.generate_content.assert_called()

    def test_call_model_openai_passing(self):
        """Verify _call_model passes system_instruction to OpenAI correctly."""
        with patch('ai_handler.os.getenv', return_value="fake_key"):
            handler = AIHandler()
            handler.configure("openai", "key", "model")

            mock_client = self.mock_openai.return_value
            mock_client.chat.completions.create.return_value.choices[0].message.content = "Response"

            # We need to set the client manually because configure is called in init
            handler.client = mock_client

            system_inst = "System prompt"
            user_msg = "User prompt"

            handler._call_model(user_msg, system_instruction=system_inst)

            # Verify messages structure
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            messages = call_kwargs['messages']

            self.assertEqual(messages[0]['role'], 'system')
            self.assertEqual(messages[0]['content'], system_inst)
            self.assertEqual(messages[1]['role'], 'user')
            self.assertEqual(messages[1]['content'], user_msg)

if __name__ == "__main__":
    unittest.main()
