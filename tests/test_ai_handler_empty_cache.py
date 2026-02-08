import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import os

sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from ai_handler import AIHandler

class TestAIHandlerEmptyCache(unittest.TestCase):
    @patch('builtins.open', new_callable=mock_open, read_data="")
    @patch('os.path.exists', return_value=True)
    def test_get_voice_profile_empty_caching(self, mock_exists, mock_file):
        ai_handler = AIHandler()

        # First call reads empty file
        profile1 = ai_handler.get_voice_profile()
        self.assertEqual(profile1, "")

        # Second call should use cache, but currently might read again due to 'if cache:' check
        profile2 = ai_handler.get_voice_profile()
        self.assertEqual(profile2, "")

        # If caching is working correctly for empty strings, call count should be 1.
        # If buggy (using truthiness check), it will be 2.
        self.assertEqual(mock_file.call_count, 1)

if __name__ == '__main__':
    unittest.main()
