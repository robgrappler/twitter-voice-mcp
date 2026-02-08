import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import os

# We need to mock google.generativeai because it's imported in ai_handler.py
# and we don't want to rely on it being installed or having an API key.
# Also need to mock 'google' to avoid ModuleNotFoundError for the parent package.
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()

# Now we can import AIHandler
# Assuming src is in python path or we append it
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from ai_handler import AIHandler

class TestAIHandlerCaching(unittest.TestCase):
    def setUp(self):
        # Reset any potential caching/state
        pass

    @patch('builtins.open', new_callable=mock_open, read_data="Cached Voice Profile")
    @patch('os.path.exists', return_value=True)
    def test_get_voice_profile_caching(self, mock_exists, mock_file):
        ai_handler = AIHandler()

        # First call should read from file
        profile1 = ai_handler.get_voice_profile()
        self.assertEqual(profile1, "Cached Voice Profile")

        # Second call should use cache
        profile2 = ai_handler.get_voice_profile()
        self.assertEqual(profile2, "Cached Voice Profile")

        # Expected behavior: 1 read
        self.assertEqual(mock_file.call_count, 1)

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_save_voice_profile_updates_cache(self, mock_makedirs, mock_file):
        ai_handler = AIHandler()

        # Save new profile
        new_profile = "New Voice Profile"
        ai_handler.save_voice_profile(new_profile)

        # Verify file write
        mock_file.assert_called_with(ai_handler.voice_profile_path, "w")
        mock_file().write.assert_called_with(new_profile)

        # Verify cache update by checking internal state (whitebox testing)
        self.assertEqual(ai_handler._voice_profile_cache, new_profile)

        # Verify get_voice_profile returns new profile without reading file
        # We need to reset mock_file to verify no new reads
        # Note: calling reset_mock() on mock_file doesn't reset the fact that it was called as a context manager?
        # Actually mock_file is the mock object returned by open().
        # Let's just check call_count manually.
        mock_file.reset_mock()

        fetched_profile = ai_handler.get_voice_profile()
        self.assertEqual(fetched_profile, new_profile)

        # Should not be called because cache is hit.
        # Note: if it were called, it would be 'open(path, "r")'
        mock_file.assert_not_called()

if __name__ == '__main__':
    unittest.main()
