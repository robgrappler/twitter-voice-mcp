import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

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

# Import server
import server

class TestPathTraversal(unittest.TestCase):
    def setUp(self):
        # Reset mocks
        server.ai_handler.reset_mock()
        server.data_manager.reset_mock()
        server.twitter.reset_mock()

        # Setup default mock behaviors
        server.ai_handler.generate_tweet.return_value = ["Tweet 1"]
        server.data_manager.add_draft.return_value = "draft_123"

    def test_generate_draft_tweets_rejects_bad_path(self):
        dangerous_path = "/etc/passwd"

        # We expect the function to return an error string
        result = server.generate_draft_tweets("topic", 1, media_path=dangerous_path)

        # Check for error message indicating failure/access denied
        self.assertTrue("Access denied" in result or "Error" in result, f"Result should be an error, got: {result}")

        # Verify add_draft was NOT called
        server.data_manager.add_draft.assert_not_called()

    def test_generate_draft_tweets_accepts_good_path(self):
        # Construct a path that is guaranteed to be inside SAFE_DIR
        safe_path = os.path.join(server.SAFE_DIR, "image.jpg")

        result = server.generate_draft_tweets("topic", 1, media_path=safe_path)

        self.assertIn("Generated 1 drafts", result)
        server.data_manager.add_draft.assert_called_once()

        # Verify the path passed to add_draft is correct (absolute path)
        args, kwargs = server.data_manager.add_draft.call_args
        self.assertEqual(kwargs.get("media_path"), safe_path)

    def test_approve_and_post_draft_rejects_bad_path_in_draft(self):
        # Simulate a draft that has a bad path
        draft_id = "bad_draft"
        server.data_manager.get_draft.return_value = {
            "id": draft_id,
            "text": "Bad draft",
            "media_path": "/etc/passwd",
            "status": "pending",
            "is_retweet": False
        }

        result = server.approve_and_post_draft(draft_id)

        self.assertTrue("Access denied" in result or "Error" in result or "Security Error" in result, f"Result should be an error, got: {result}")
        server.twitter.post_tweet.assert_not_called()

if __name__ == "__main__":
    unittest.main()
