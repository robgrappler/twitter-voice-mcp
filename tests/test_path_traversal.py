import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

class TestPathTraversal(unittest.TestCase):
    def setUp(self):
        # Prepare mocks
        self.mock_ai_handler_module = MagicMock()
        self.mock_twitter_handler_module = MagicMock()
        self.mock_data_handler_module = MagicMock()
        self.mock_scheduler_module = MagicMock()

        # Mock FastMCP
        self.mock_mcp_module = MagicMock()
        self.mock_mcp_instance = MagicMock()
        # Setup tool decorator
        def tool_decorator(*args, **kwargs):
            if len(args) == 1 and callable(args[0]):
                return args[0]
            else:
                def decorator(func):
                    return func
                return decorator
        self.mock_mcp_instance.tool = tool_decorator
        self.mock_mcp_module.FastMCP.return_value = self.mock_mcp_instance

        # Patch sys.modules
        self.modules_patcher = patch.dict(sys.modules, {
            "ai_handler": self.mock_ai_handler_module,
            "twitter_handler": self.mock_twitter_handler_module,
            "data_handler": self.mock_data_handler_module,
            "scheduler": self.mock_scheduler_module,
            "mcp.server.fastmcp": self.mock_mcp_module
        })
        self.modules_patcher.start()

        # Remove server from sys.modules to ensure re-import with mocks
        if "server" in sys.modules:
            del sys.modules["server"]

        import server
        self.server = server

        # Configure default mock behaviors on the IMPORTED server module's instances
        # Note: server.py creates instances: ai_handler = AIHandler()
        # So server.ai_handler is the return value of AIHandler()
        self.server.ai_handler.generate_tweet.return_value = ["Tweet 1"]
        self.server.data_manager.add_draft.return_value = "draft_123"

    def tearDown(self):
        self.modules_patcher.stop()
        # Clean up server from sys.modules so other tests import the real one
        if "server" in sys.modules:
            del sys.modules["server"]

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
