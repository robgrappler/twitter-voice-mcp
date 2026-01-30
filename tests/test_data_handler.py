
import unittest
import os
import sys
import shutil
import pandas as pd
from unittest.mock import patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

# We need to import data_handler to patch its attributes
import data_handler
from data_handler import DataManager

class TestDataManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary data directory
        self.test_dir = os.path.join(os.path.dirname(__file__), "test_data_handler_temp")
        os.makedirs(self.test_dir, exist_ok=True)

        self.test_drafts_file = os.path.join(self.test_dir, "drafts.csv")
        self.test_posted_log = os.path.join(self.test_dir, "posted_history.csv")

        # Patch the file paths in data_handler module
        self.patcher1 = patch('data_handler.DRAFTS_FILE', self.test_drafts_file)
        self.patcher2 = patch('data_handler.POSTED_LOG', self.test_posted_log)
        self.patcher1.start()
        self.patcher2.start()

        # Initialize DataManager which will create the files
        self.dm = DataManager()

    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_mark_as_posted(self):
        # Create a draft
        draft_id = self.dm.add_draft("Test Tweet")

        # Mark as posted
        tweet_id = "1234567890"
        self.dm.mark_as_posted(draft_id, tweet_id)

        # Verify status updated
        draft = self.dm.get_draft(draft_id)
        self.assertEqual(draft["status"], "posted")

        # Verify added to posted log
        df = pd.read_csv(self.test_posted_log, dtype=str)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["id"], draft_id)
        self.assertEqual(df.iloc[0]["tweet_id"], tweet_id)
        self.assertEqual(df.iloc[0]["text"], "Test Tweet")

    def test_mark_as_posted_appends(self):
        # Add two drafts
        draft1 = self.dm.add_draft("Tweet 1")
        draft2 = self.dm.add_draft("Tweet 2")

        self.dm.mark_as_posted(draft1, "id1")
        self.dm.mark_as_posted(draft2, "id2")

        df = pd.read_csv(self.test_posted_log)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]["tweet_id"], "id1")
        self.assertEqual(df.iloc[1]["tweet_id"], "id2")

if __name__ == "__main__":
    unittest.main()
