import sys
import os
import unittest
from unittest.mock import MagicMock, patch, mock_open

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from ai_handler import AIHandler

class TestAIHandlerCaching(unittest.TestCase):
    def setUp(self):
        self.handler = AIHandler()
        # Reset cache if it exists (for when we implement it)
        if hasattr(self.handler, '_voice_profile_cache'):
            self.handler._voice_profile_cache = None

    @patch('builtins.open', new_callable=mock_open, read_data="Cached Profile Data")
    @patch('os.path.exists')
    def test_get_voice_profile_caches_data(self, mock_exists, mock_file):
        mock_exists.return_value = True

        # First call - should read from file
        profile1 = self.handler.get_voice_profile()
        self.assertEqual(profile1, "Cached Profile Data")

        # Verify open called once
        # Note: Depending on implementation, open might be called.
        # Currently it is called every time.
        # We want it to be called ONCE.

        # Second call - should use cache
        profile2 = self.handler.get_voice_profile()
        self.assertEqual(profile2, "Cached Profile Data")

        # In optimized version, open should be called only once
        # In unoptimized version, it will be called twice
        # We assert 1 to confirm optimization works (this will fail before optimization)
        self.assertEqual(mock_file.call_count, 1)

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    @patch('ai_handler.AIHandler._call_model')
    def test_analyze_style_updates_cache(self, mock_call_model, mock_exists, mock_file):
        mock_exists.return_value = True
        mock_call_model.return_value = "New Voice Profile"

        # Run analyze_style
        self.handler.analyze_style(["tweet1", "tweet2"])

        # Verify file write
        mock_file.assert_called_with(self.handler.voice_profile_path, "w")
        handle = mock_file()
        handle.write.assert_called_with("New Voice Profile")

        # Now call get_voice_profile - should return new profile without reading file
        # Reset mock_file to verify no read occurs
        mock_file.reset_mock()

        profile = self.handler.get_voice_profile()
        self.assertEqual(profile, "New Voice Profile")

        # Verify no read calls (cache hit)
        mock_file.assert_not_called()

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_save_voice_profile_updates_cache(self, mock_exists, mock_file):
        # This test assumes save_voice_profile exists (we will add it)
        if not hasattr(self.handler, 'save_voice_profile'):
            return

        mock_exists.return_value = True

        self.handler.save_voice_profile("Manual Profile")

        # Verify write
        mock_file.assert_called_with(self.handler.voice_profile_path, "w")
        handle = mock_file()
        handle.write.assert_called_with("Manual Profile")

        # Verify cache update
        mock_file.reset_mock()
        profile = self.handler.get_voice_profile()
        self.assertEqual(profile, "Manual Profile")
        mock_file.assert_not_called()

if __name__ == "__main__":
    unittest.main()
