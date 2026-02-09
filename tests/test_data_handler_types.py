import unittest
import os
import shutil
import tempfile
import sys

# Add src to path
sys.path.append(os.path.abspath("src"))

import data_handler

class TestDataHandlerTypes(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

        # Save original paths
        self.original_drafts_file = data_handler.DRAFTS_FILE
        self.original_posted_log = data_handler.POSTED_LOG
        self.original_post_attempt_log = data_handler.POST_ATTEMPT_LOG

        # Update paths to use temp dir
        data_handler.DRAFTS_FILE = os.path.join(self.test_dir, "drafts.csv")
        data_handler.POSTED_LOG = os.path.join(self.test_dir, "posted_history.csv")
        data_handler.POST_ATTEMPT_LOG = os.path.join(self.test_dir, "post_log.csv")

        # Re-initialize DataManager
        self.data_manager = data_handler.DataManager()

    def tearDown(self):
        # Restore paths
        data_handler.DRAFTS_FILE = self.original_drafts_file
        data_handler.POSTED_LOG = self.original_posted_log
        data_handler.POST_ATTEMPT_LOG = self.original_post_attempt_log

        # Remove temporary directory
        shutil.rmtree(self.test_dir)

    def test_is_retweet_boolean(self):
        # Add a draft with is_retweet=True
        draft_id = self.data_manager.add_draft("Test Retweet", is_retweet=True)

        # Retrieve draft
        draft = self.data_manager.get_draft(draft_id)

        # Verify is_retweet is strictly boolean True
        self.assertIsInstance(draft["is_retweet"], bool)
        self.assertTrue(draft["is_retweet"])

        # Add another draft with is_retweet=False
        draft_id_2 = self.data_manager.add_draft("Test Normal Tweet", is_retweet=False)
        draft_2 = self.data_manager.get_draft(draft_id_2)

        self.assertIsInstance(draft_2["is_retweet"], bool)
        self.assertFalse(draft_2["is_retweet"])

    def test_original_tweet_id_preservation(self):
        # Long Tweet ID that might lose precision if converted to int/float
        long_id = "1234567890123456789"

        draft_id = self.data_manager.add_draft(
            "Test ID",
            original_tweet_id=long_id,
            is_retweet=True
        )

        draft = self.data_manager.get_draft(draft_id)

        self.assertIsInstance(draft["original_tweet_id"], str)
        self.assertEqual(draft["original_tweet_id"], long_id)

    def test_list_pending_drafts_types(self):
        self.data_manager.add_draft("D1", is_retweet=True)
        self.data_manager.add_draft("D2", is_retweet=False)

        pending = self.data_manager.list_pending_drafts()

        self.assertEqual(len(pending), 2)
        self.assertTrue(pending[0]["is_retweet"])
        self.assertFalse(pending[1]["is_retweet"])

if __name__ == "__main__":
    unittest.main()
