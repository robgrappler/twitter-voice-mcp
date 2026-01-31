import unittest
import os
import shutil
import tempfile
import pandas as pd
import sys
import importlib

# Add src to path
sys.path.append(os.path.abspath("src"))

import data_handler

class TestDataManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

        # Save original paths
        self.original_drafts_file = data_handler.DRAFTS_FILE
        self.original_posted_log = data_handler.POSTED_LOG

        # Update paths to use temp dir
        data_handler.DRAFTS_FILE = os.path.join(self.test_dir, "drafts.csv")
        data_handler.POSTED_LOG = os.path.join(self.test_dir, "posted_history.csv")

        # Re-initialize DataManager to ensure files are created in temp dir
        self.data_manager = data_handler.DataManager()

    def tearDown(self):
        # Restore paths
        data_handler.DRAFTS_FILE = self.original_drafts_file
        data_handler.POSTED_LOG = self.original_posted_log

        # Remove temporary directory
        shutil.rmtree(self.test_dir)

    def test_mark_as_posted(self):
        # 1. Add a draft
        draft_id = self.data_manager.add_draft("Test Tweet", "media.jpg")

        # 2. Mark as posted
        tweet_id = "123456789"
        self.data_manager.mark_as_posted(draft_id, tweet_id)

        # 3. Verify status updated in drafts.csv
        draft = self.data_manager.get_draft(draft_id)
        self.assertEqual(draft["status"], "posted")

        # 4. Verify appended to posted_history.csv
        df = pd.read_csv(data_handler.POSTED_LOG, dtype=str)

        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["id"], draft_id)
        self.assertEqual(df.iloc[0]["tweet_id"], tweet_id)
        self.assertEqual(df.iloc[0]["text"], "Test Tweet")
        self.assertEqual(df.iloc[0]["media_path"], "media.jpg")

    def test_mark_as_posted_with_provided_data(self):
        # 1. Add a draft
        draft_id = self.data_manager.add_draft("Test Tweet 2", "media2.jpg")

        # 2. Mark as posted, providing data explicitly
        tweet_id = "987654321"
        self.data_manager.mark_as_posted(draft_id, tweet_id, text="Test Tweet 2", media_path="media2.jpg")

        # 3. Verify status updated
        draft = self.data_manager.get_draft(draft_id)
        self.assertEqual(draft["status"], "posted")

        # 4. Verify appended to posted_history.csv
        df = pd.read_csv(data_handler.POSTED_LOG, dtype=str)

        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["id"], draft_id)
        self.assertEqual(df.iloc[0]["tweet_id"], tweet_id)
        self.assertEqual(df.iloc[0]["text"], "Test Tweet 2")
        self.assertEqual(df.iloc[0]["media_path"], "media2.jpg")

if __name__ == "__main__":
    unittest.main()
