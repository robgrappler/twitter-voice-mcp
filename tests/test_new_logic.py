import sys
import os
import csv
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath("src"))

from scheduler import TweetScheduler
import data_handler
from data_handler import DataManager

class TestScheduleLogic(unittest.TestCase):
    def setUp(self):
        self.scheduler = TweetScheduler()
        self.test_dir = tempfile.mkdtemp()
        self.post_log = os.path.join(self.test_dir, "post_log.csv")

        # Initialize post log with headers
        headers = ["timestamp", "draft_id", "status", "tweet_id", "error", "text"]
        with open(self.post_log, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

        # Patch POST_ATTEMPT_LOG
        self.original_post_log = data_handler.POST_ATTEMPT_LOG
        data_handler.POST_ATTEMPT_LOG = self.post_log

    def tearDown(self):
        data_handler.POST_ATTEMPT_LOG = self.original_post_log
        shutil.rmtree(self.test_dir)

    def test_vampire_mode_slots(self):
        # Vampire Mode (CST): Mon, Tue, Fri at 00:00, 01:00, 02:00
        # Mon, Feb 2, 2026 is a Monday.
        # 00:00 CST is 06:00 UTC.
        
        # Test Monday 00:00 CST (06:00 UTC)
        vamp_mon = datetime(2026, 2, 2, 6, 0, tzinfo=timezone.utc)
        self.assertTrue(self.scheduler.is_strategy_slot(vamp_mon))
        
        # Test Monday 01:00 CST (07:00 UTC)
        vamp_mon_1 = datetime(2026, 2, 2, 7, 0, tzinfo=timezone.utc)
        self.assertTrue(self.scheduler.is_strategy_slot(vamp_mon_1))
        
        # Test Wednesday 00:00 CST (06:00 UTC) - Should be False
        wed = datetime(2026, 2, 4, 6, 0, tzinfo=timezone.utc)
        self.assertFalse(self.scheduler.is_strategy_slot(wed))

    def test_growth_mode_slots(self):
        # Growth Mode (CST): Everyday at 08:00, 14:00
        # 08:00 CST is 14:00 UTC.
        
        # Everyday 08:00 CST (14:00 UTC)
        growth_anyday = datetime(2026, 2, 4, 14, 0, tzinfo=timezone.utc)
        self.assertTrue(self.scheduler.is_strategy_slot(growth_anyday))
        
        # Everyday 14:00 CST (20:00 UTC)
        growth_anyday_2 = datetime(2026, 2, 4, 20, 0, tzinfo=timezone.utc)
        self.assertTrue(self.scheduler.is_strategy_slot(growth_anyday_2))

    def test_drift_protection(self):
        # Top of hour check (first 5 mins)
        slot_ok = datetime(2026, 2, 4, 14, 2, tzinfo=timezone.utc)
        self.assertTrue(self.scheduler.is_strategy_slot(slot_ok))
        
        slot_late = datetime(2026, 2, 4, 14, 6, tzinfo=timezone.utc)
        self.assertFalse(self.scheduler.is_strategy_slot(slot_late))

    def test_log_attempt(self):
        data_manager = DataManager()
        
        # Log a dummy attempt
        test_msg = "Verification test message"
        data_manager.log_attempt("success", draft_id="test_id", text=test_msg)
        
        # Verify it exists
        self.assertTrue(os.path.exists(self.post_log))
        
        # Read and check content
        with open(self.post_log, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        last_row = rows[-1]
        self.assertEqual(last_row["status"], "success")
        self.assertEqual(last_row["draft_id"], "test_id")
        self.assertIn(test_msg, last_row["text"])

    def test_get_next_pending_draft(self):
        # Create a mock drafts file with one pending draft
        drafts_file = os.path.join(self.test_dir, "drafts.csv")
        headers = ["id", "text", "media_path", "model_used", "status", "created_at", "scheduled_time", "notes", "is_retweet", "original_tweet_id"]

        # Patch DRAFTS_FILE
        original_drafts_file = data_handler.DRAFTS_FILE
        data_handler.DRAFTS_FILE = drafts_file

        try:
            with open(drafts_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerow(["d1", "draft1", "", "manual", "posted", "", "", "", "False", ""])
                writer.writerow(["d2", "draft2", "", "manual", "pending", "", "", "", "False", ""])
                writer.writerow(["d3", "draft3", "", "manual", "pending", "", "", "", "False", ""])

            # Should return the first pending draft (d2)
            draft = self.scheduler.get_next_pending_draft()
            self.assertIsNotNone(draft)
            self.assertEqual(draft["id"], "d2")

        finally:
            data_handler.DRAFTS_FILE = original_drafts_file

if __name__ == "__main__":
    unittest.main()
