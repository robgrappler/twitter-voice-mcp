import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

class TestAIHandlerLazy(unittest.TestCase):
    def setUp(self):
        # Ensure ai_handler is reloaded for each test to clear state
        if 'ai_handler' in sys.modules:
            del sys.modules['ai_handler']
        if 'google.generativeai' in sys.modules:
            del sys.modules['google.generativeai']
        if 'openai' in sys.modules:
            del sys.modules['openai']
        if 'anthropic' in sys.modules:
            del sys.modules['anthropic']

    def test_lazy_import_gemini(self):
        # Mock env vars
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            # Mock the module import
            mock_genai = MagicMock()
            with patch.dict(sys.modules, {'google.generativeai': mock_genai}):
                from ai_handler import AIHandler
                handler = AIHandler()

                # Should have configured genai
                mock_genai.configure.assert_called_with(api_key="fake_key")
                self.assertEqual(handler.provider, "gemini")

    def test_lazy_import_openai(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"}):
            # We need to mock 'openai' module AND 'openai.OpenAI' class
            mock_openai_module = MagicMock()
            mock_openai_client = MagicMock()
            mock_openai_module.OpenAI.return_value = mock_openai_client

            with patch.dict(sys.modules, {'openai': mock_openai_module}):
                from ai_handler import AIHandler
                handler = AIHandler()

                # Should have initialized OpenAI client
                mock_openai_module.OpenAI.assert_called_with(api_key="fake_key")
                self.assertEqual(handler.client, mock_openai_client)

    def test_call_model_imports_genai(self):
        # Test that _call_model imports genai if not already imported (or uses it)
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}):
            mock_genai = MagicMock()
            mock_model = MagicMock()
            mock_genai.GenerativeModel.return_value = mock_model
            mock_model.generate_content.return_value.text = "Generated content"

            with patch.dict(sys.modules, {'google.generativeai': mock_genai}):
                from ai_handler import AIHandler
                handler = AIHandler()

                response = handler._call_model("test prompt")

                self.assertEqual(response, "Generated content")
                mock_genai.GenerativeModel.assert_called()

if __name__ == "__main__":
    unittest.main()
