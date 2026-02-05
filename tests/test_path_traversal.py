import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))


class TestPathTraversal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up mocks before any tests in this class run."""
        # Save original modules
        cls._original_modules = {}
        for mod_name in ["mcp.server.fastmcp", "ai_handler", "twitter_handler", "data_handler", "scheduler"]:
            cls._original_modules[mod_name] = sys.modules.get(mod_name)

        # Mock mcp.server.fastmcp before importing server
        mock_mcp_instance = MagicMock()

        def tool_decorator(*args, **kwargs):
            if len(args) == 1 and callable(args[0]):
                return args[0]
            else:
                def decorator(func):
                    return func
                return decorator

        mock_mcp_instance.tool = tool_decorator

        fastmcp_module = MagicMock()
        fastmcp_module.FastMCP.return_value = mock_mcp_instance
        sys.modules["mcp.server.fastmcp"] = fastmcp_module

        # Mock other modules
        sys.modules["ai_handler"] = MagicMock()
        sys.modules["twitter_handler"] = MagicMock()
        sys.modules["data_handler"] = MagicMock()
        sys.modules["scheduler"] = MagicMock()

        # Import server after mocks are in place
        # Need to remove server from modules if it exists to force reimport
        if "server" in sys.modules:
            del sys.modules["server"]

        import server
        cls.server = server

    @classmethod
    def tearDownClass(cls):
        """Clean up mocks after all tests in this class have run."""
        # Remove server module to prevent stale imports
        if "server" in sys.modules:
            del sys.modules["server"]

        # Restore original modules
        for mod_name, original in cls._original_modules.items():
            if original is None:
                if mod_name in sys.modules:
                    del sys.modules[mod_name]
            else:
                sys.modules[mod_name] = original

    def setUp(self):
        # Reset mocks
        self.server.ai_handler.reset_mock()
        self.server.data_manager.reset_mock()
        self.server.twitter.reset_mock()

        # Setup default mock behaviors
        self.server.ai_handler.generate_tweet.return_value = ["Tweet 1"]
        self.server.data_manager.add_draft.return_value = "draft_123"

    def test_generate_draft_tweets_rejects_bad_path(self):
        dangerous_path = "/etc/passwd"

        # We expect the function to return an error string
        result = self.server.generate_draft_tweets("topic", 1, media_path=dangerous_path)

        # Check for error message indicating failure/access denied
        self.assertTrue("Access denied" in result or "Error" in result, f"Result should be an error, got: {result}")

        # Verify add_draft was NOT called
        self.server.data_manager.add_draft.assert_not_called()

    def test_generate_draft_tweets_accepts_good_path(self):
        # Construct a path that is guaranteed to be inside SAFE_DIR
        safe_path = os.path.join(self.server.SAFE_DIR, "image.jpg")

        result = self.server.generate_draft_tweets("topic", 1, media_path=safe_path)

        self.assertIn("Generated 1 drafts", result)
        self.server.data_manager.add_draft.assert_called_once()

        # Verify the path passed to add_draft is correct (absolute path)
        args, kwargs = self.server.data_manager.add_draft.call_args
        self.assertEqual(kwargs.get("media_path"), safe_path)

    def test_approve_and_post_draft_rejects_bad_path_in_draft(self):
        # Simulate a draft that has a bad path
        draft_id = "bad_draft"
        self.server.data_manager.get_draft.return_value = {
            "id": draft_id,
            "text": "Bad draft",
            "media_path": "/etc/passwd",
            "status": "pending",
            "is_retweet": False
        }

        result = self.server.approve_and_post_draft(draft_id)

        self.assertTrue("Access denied" in result or "Error" in result or "Security Error" in result, f"Result should be an error, got: {result}")
        self.server.twitter.post_tweet.assert_not_called()

if __name__ == "__main__":
    unittest.main()

