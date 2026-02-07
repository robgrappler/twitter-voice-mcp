import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from ai_handler import AIHandler

class TestAIHandlerCaching(unittest.TestCase):
    def setUp(self):
        self.handler = AIHandler()
        # Ensure we start with a clean state (no cache)
        if hasattr(self.handler, '_voice_profile_cache'):
             self.handler._voice_profile_cache = None

    def test_get_voice_profile_caches_content(self):
        # Mock file content
        content = "Cached voice profile content"

        # Mock os.path.exists to return True
        with patch("os.path.exists", return_value=True):
            # Mock open
            m = mock_open(read_data=content)
            with patch("builtins.open", m):

                # First call - should read from file
                profile1 = self.handler.get_voice_profile()
                self.assertEqual(profile1, content)

                # Verify file was opened
                m.assert_called_once()

                # Reset mock to verify it's NOT called again
                m.reset_mock()

                # Second call - should use cache
                profile2 = self.handler.get_voice_profile()
                self.assertEqual(profile2, content)

                # Verify file was NOT opened
                m.assert_not_called()

    def test_save_voice_profile_updates_cache(self):
        new_content = "New voice profile content"

        with patch("builtins.open", mock_open()) as m:
            self.handler.save_voice_profile(new_content)

            # Verify file write
            m.assert_called_with(self.handler.voice_profile_path, "w")
            handle = m()
            handle.write.assert_called_with(new_content)

            # Verify cache update
            # We need to mock existence check for get_voice_profile to work without file read
            with patch("os.path.exists", return_value=True):
                 # If we call get_voice_profile now, it should return new_content WITHOUT reading file
                 # (assuming we mock open to NOT return anything or check calls)

                 # Reset mock
                m.reset_mock()

                profile = self.handler.get_voice_profile()
                self.assertEqual(profile, new_content)
                m.assert_not_called() # Should not read file

if __name__ == "__main__":
    unittest.main()
