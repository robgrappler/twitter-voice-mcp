import unittest
import os
import shutil
import tempfile
import csv
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
        with open(data_handler.POSTED_LOG, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], draft_id)
        self.assertEqual(rows[0]["tweet_id"], tweet_id)
        self.assertEqual(rows[0]["text"], "Test Tweet")
        self.assertEqual(rows[0]["media_path"], "media.jpg")

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
        with open(data_handler.POSTED_LOG, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], draft_id)
        self.assertEqual(rows[0]["tweet_id"], tweet_id)
        self.assertEqual(rows[0]["text"], "Test Tweet 2")
        self.assertEqual(rows[0]["media_path"], "media2.jpg")

    def test_get_first_pending_draft(self):
        # 1. Add multiple drafts (some pending, some posted)
        id1 = self.data_manager.add_draft("Draft 1")
        self.data_manager.mark_as_posted(id1, "tweet1")

        id2 = self.data_manager.add_draft("Draft 2") # This is the first pending one
        id3 = self.data_manager.add_draft("Draft 3") # Second pending

        # 2. Get first pending
        draft = self.data_manager.get_first_pending_draft()

        # 3. Verify it is Draft 2
        self.assertIsNotNone(draft)
        self.assertEqual(draft["id"], id2)
        self.assertEqual(draft["text"], "Draft 2")

        # 4. Mark Draft 2 as posted
        self.data_manager.mark_as_posted(id2, "tweet2")

        # 5. Get first pending again
        draft = self.data_manager.get_first_pending_draft()

        # 6. Verify it is Draft 3
        self.assertIsNotNone(draft)
        self.assertEqual(draft["id"], id3)
        self.assertEqual(draft["text"], "Draft 3")

        # 7. Mark Draft 3 as posted
        self.data_manager.mark_as_posted(id3, "tweet3")

        # 8. Get first pending (none left)
        draft = self.data_manager.get_first_pending_draft()
        self.assertIsNone(draft)

if __name__ == "__main__":
    unittest.main()
